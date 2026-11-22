"""
Document Extraction Pipeline
Orchestrates text extraction, classification, field extraction, normalisation, and database persistence.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.db.models import Document, ExtractedField
from app.services.documents.storage import read_decrypted_file
from app.services.extraction.doc_classifier import classify_document
from app.services.extraction.field_extractors import regex_extract_fields
from app.services.extraction.llm_client import LLMClient
from app.services.extraction.normalizer import detect_financial_year_from_text
from app.services.extraction.ocr_extractor import extract_text_from_image
from app.services.extraction.pdf_extractor import extract_text_from_pdf, is_pdf_password_protected
from app.services.extraction.tabular_extractor import parse_tabular_file

logger = logging.getLogger(__name__)


def run_document_extraction_pipeline(
    document_id: str,
    db: Session,
    password: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Executes end-to-end extraction pipeline on an ingested document.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise ValueError(f"Document with ID {document_id} not found.")

    doc.status = "processing"
    db.commit()

    try:
        raw_bytes = read_decrypted_file(doc.storage_path)
    except Exception as e:
        doc.status = "failed"
        doc.error_message = f"Failed to read encrypted file: {str(e)}"
        db.commit()
        return {"success": False, "error": doc.error_message}

    extracted_text = ""
    pages_count = 1

    # Step 1: Text extraction based on file type
    try:
        if "pdf" in doc.file_type.lower():
            if is_pdf_password_protected(raw_bytes) and not password:
                doc.is_password_protected = True
                doc.status = "needs_review"
                doc.error_message = "Password required to decrypt PDF."
                db.commit()
                return {"success": False, "is_password_protected": True, "error": doc.error_message}

            success, pages, extracted_text = extract_text_from_pdf(raw_bytes, password=password)
            pages_count = len(pages)
            if not success:
                doc.status = "failed"
                doc.error_message = extracted_text
                db.commit()
                return {"success": False, "error": extracted_text}

        elif any(img_t in doc.file_type.lower() for img_t in ["image", "jpeg", "jpg", "png"]):
            success, extracted_text = extract_text_from_image(raw_bytes)
            pages_count = 1
            if not success:
                doc.status = "failed"
                doc.error_message = extracted_text
                db.commit()
                return {"success": False, "error": extracted_text}

        elif any(tab_t in doc.file_type.lower() for tab_t in ["csv", "excel", "sheet"]):
            success, rows, summary_text = parse_tabular_file(raw_bytes, doc.file_type)
            extracted_text = summary_text
            if not success:
                doc.status = "failed"
                doc.error_message = summary_text
                db.commit()
                return {"success": False, "error": summary_text}
    except Exception as e:
        doc.status = "failed"
        doc.error_message = f"Extraction error: {str(e)}"
        db.commit()
        return {"success": False, "error": doc.error_message}

    # Step 2: Auto-classify document if unassigned
    if doc.doc_type == "other" or not doc.doc_type:
        cat, conf = classify_document(extracted_text, doc.file_name)
        doc.doc_type = cat

    # Step 3: FY Detection
    detected_fy = detect_financial_year_from_text(extracted_text)
    if detected_fy:
        doc.financial_year = detected_fy

    # Step 4: Extract fields (Rules + LLM client)
    rule_fields = regex_extract_fields(extracted_text, doc.doc_type)

    llm_client = LLMClient()
    llm_fields = llm_client.extract_structured_fields(extracted_text, doc.doc_type)

    # Merge fields (rule fields override if higher confidence)
    merged_fields: Dict[str, Dict[str, Any]] = {}
    for k, v in llm_fields.items():
        if isinstance(v, dict) and "field_value" in v:
            merged_fields[k] = v

    for k, v in rule_fields.items():
        merged_fields[k] = v  # deterministic rule overrides

    # Clear old extracted fields for this document
    db.query(ExtractedField).filter(ExtractedField.document_id == doc.id).delete()

    # Step 5: Save Extracted Fields into Database
    created_fields: List[Dict[str, Any]] = []
    for k, field_data in merged_fields.items():
        field_model = ExtractedField(
            document_id=doc.id,
            user_id=doc.user_id,
            field_key=field_data["field_key"],
            field_label=field_data["field_label"],
            field_value=str(field_data["field_value"]),
            normalized_value=field_data["normalized_value"],
            confidence=field_data.get("confidence", 0.90),
            source_page=1,
            source_snippet=field_data.get("source_snippet"),
            status="auto",
            conflict_flag=field_data.get("conflict_flag", False),
        )
        db.add(field_model)
        created_fields.append(field_data)

    doc.status = "needs_review" if created_fields else "confirmed"
    doc.error_message = None
    db.commit()

    return {
        "success": True,
        "document_id": doc.id,
        "doc_type": doc.doc_type,
        "financial_year": doc.financial_year,
        "fields_extracted": len(created_fields),
        "fields": created_fields,
    }
