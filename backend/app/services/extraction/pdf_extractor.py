"""
PDF Text Extractor
Extracts text, pages, and metadata using PyMuPDF (fitz) with pdfplumber fallback.
Handles password-protected PDF detection and unlocking.
"""

from __future__ import annotations

import io
from typing import Dict, List, Optional, Tuple
import pymupdf as fitz  # PyMuPDF modern import


def is_pdf_password_protected(pdf_bytes: bytes) -> bool:
    """Checks whether the PDF document is encrypted / requires a password."""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        is_enc = doc.is_encrypted
        doc.close()
        return is_enc
    except Exception:
        return False


def extract_text_from_pdf(
    pdf_bytes: bytes,
    password: Optional[str] = None,
) -> Tuple[bool, List[Dict[str, str]], str]:
    """
    Extracts text from PDF page-by-page.
    Returns:
      success: bool,
      pages: List[Dict[str, str]] (keys: page_num, text),
      full_text: str
    Raises ValueError if PDF is password protected and wrong/no password was supplied.
    """
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        return False, [], f"Error opening PDF: {str(e)}"

    if doc.is_encrypted:
        if not password:
            doc.close()
            raise ValueError("PDF is password protected. User password required.")
        auth_success = doc.authenticate(password)
        if not auth_success:
            doc.close()
            raise ValueError("Incorrect password for protected PDF.")

    pages_data: List[Dict[str, str]] = []
    full_text_parts: List[str] = []

    for page_idx in range(len(doc)):
        page = doc[page_idx]
        text = page.get_text("text")
        cleaned_text = text.strip()
        pages_data.append({"page_num": page_idx + 1, "text": cleaned_text})
        if cleaned_text:
            full_text_parts.append(cleaned_text)

    doc.close()
    combined_text = "\n\n--- PAGE BREAK ---\n\n".join(full_text_parts)
    return True, pages_data, combined_text
