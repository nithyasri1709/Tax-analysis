"""
Extraction API Router
Review, inline edit, verify, confirm, and resolve conflicts of extracted fields.
Synchronizes confirmed values to FinancialProfile.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.db.models import AuditLog, Document, ExtractedField, FinancialProfile, User
from app.db.session import get_db
from app.schemas.document import ConflictResolveRequest, ExtractedFieldOut, FieldUpdateRequest
from app.services.extraction.normalizer import parse_inr_amount
from app.services.extraction.pipeline import run_document_extraction_pipeline

router = APIRouter(prefix="/extraction", tags=["Extraction & Verification"])


@router.post("/{document_id}/process")
def process_document_extraction(
    document_id: str,
    password: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Triggers extraction pipeline on a specific document."""
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    res = run_document_extraction_pipeline(doc.id, db, password)
    return res


@router.get("/{document_id}/fields", response_model=List[ExtractedFieldOut])
def get_extracted_fields(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns all extracted fields for a document with confidence scores and snippets."""
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    fields = db.query(ExtractedField).filter(ExtractedField.document_id == doc.id).all()
    return fields


@router.put("/fields/{field_id}", response_model=ExtractedFieldOut)
def update_extracted_field(
    field_id: str,
    payload: FieldUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Inline editing of an extracted field value. Marks status as 'user_edited'."""
    field = db.query(ExtractedField).filter(
        ExtractedField.id == field_id,
        ExtractedField.user_id == current_user.id,
    ).first()
    if not field:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Extracted field not found.")

    field.field_value = payload.field_value.strip()
    if payload.normalized_value is not None:
        field.normalized_value = payload.normalized_value
    else:
        field.normalized_value = parse_inr_amount(payload.field_value)

    field.status = "user_edited"
    field.confidence = 1.0  # User edited = 100% confidence
    field.conflict_flag = False

    audit = AuditLog(
        user_id=current_user.id,
        action="FIELD_USER_EDITED",
        details={"field_key": field.field_key, "new_value": field.field_value},
    )
    db.add(audit)
    db.commit()
    db.refresh(field)
    return field


@router.post("/{document_id}/confirm")
def confirm_document_fields(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Confirms all extracted fields for a document and synchronizes them into the
    user's FinancialProfile for that Financial Year.
    """
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    fields = db.query(ExtractedField).filter(ExtractedField.document_id == doc.id).all()
    for f in fields:
        f.status = "confirmed"

    doc.status = "confirmed"

    # Synchronize into FinancialProfile
    profile = db.query(FinancialProfile).filter(
        FinancialProfile.user_id == current_user.id,
        FinancialProfile.financial_year == doc.financial_year,
    ).first()

    if not profile:
        profile = FinancialProfile(
            user_id=current_user.id,
            financial_year=doc.financial_year,
            selected_regime="new",
        )
        db.add(profile)
        db.flush()

    salary_data = dict(profile.salary_data or {})
    deductions_data = dict(profile.deductions_data or {})
    house_prop_data = dict(profile.house_prop_data or {})
    taxes_paid_data = dict(profile.taxes_paid_data or {})

    for f in fields:
        val = f.normalized_value or 0.0
        if f.field_key in ["gross_salary", "basic_salary", "hra_received", "da_amount", "professional_tax"]:
            salary_data[f.field_key] = val
        elif f.field_key in ["epf", "ppf", "elss", "80ccd_1b", "80ccd_2", "health_insurance_self", "80g_donations", "80e_interest"]:
            deductions_data[f.field_key] = val
        elif f.field_key in ["home_loan_principal"]:
            deductions_data["home_loan_principal"] = val
        elif f.field_key in ["home_loan_interest"]:
            house_prop_data["home_loan_interest"] = val
            house_prop_data["is_self_occupied"] = True
        elif f.field_key in ["rent_paid"]:
            salary_data["rent_paid"] = val
        elif f.field_key in ["tds_total"]:
            taxes_paid_data["tds_salary"] = val

    profile.salary_data = salary_data
    profile.deductions_data = deductions_data
    profile.house_prop_data = house_prop_data
    profile.taxes_paid_data = taxes_paid_data
    profile.completeness_score = min(100, 20 + len(fields) * 10)

    audit = AuditLog(
        user_id=current_user.id,
        action="DOCUMENT_CONFIRMED",
        details={"document_id": doc.id, "fields_count": len(fields)},
    )
    db.add(audit)
    db.commit()

    return {"message": "All fields confirmed and synchronized to financial profile successfully."}
