"""
Users Router
User profile management, PAN updates, password changes, data export, and full account purge.
"""

from datetime import datetime, timezone
import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.core.encryption import encrypt_text, mask_pan
from app.core.security import get_password_hash, verify_password
from app.db.models import (
    AuditLog,
    Document,
    FinancialProfile,
    ReportRecord,
    TaxCalculationRecord,
    Transaction,
    User,
)
from app.db.session import get_db
from app.schemas.auth import PasswordChangeRequest
from app.schemas.user import PanUpdateRequest, UserDataExport, UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserOut)
def get_my_profile(current_user: User = Depends(get_current_user)):
    """Returns profile for currently authenticated user."""
    return current_user


@router.put("/me", response_model=UserOut)
def update_my_profile(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Updates user demographic and tax-related profile fields."""
    if payload.full_name is not None:
        current_user.full_name = payload.full_name.strip()
    if payload.dob is not None:
        current_user.dob = payload.dob
    if payload.age_bracket is not None:
        current_user.age_bracket = payload.age_bracket
    if payload.residential_status is not None:
        current_user.residential_status = payload.residential_status
    if payload.state is not None:
        current_user.state = payload.state
    if payload.city is not None:
        current_user.city = payload.city
    if payload.is_metro is not None:
        current_user.is_metro = payload.is_metro
    if payload.employment_type is not None:
        current_user.employment_type = payload.employment_type

    audit = AuditLog(user_id=current_user.id, action="PROFILE_UPDATED", details={"fields": list(payload.model_dump(exclude_unset=True).keys())})
    db.add(audit)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.put("/me/pan")
def update_my_pan(
    payload: PanUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Encrypts PAN at rest and updates masked representation in profile."""
    pan_str = payload.pan.strip().upper()
    if len(pan_str) != 10 or not pan_str[:5].isalpha() or not pan_str[5:9].isdigit() or not pan_str[9].isalpha():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Indian PAN format. Must be 10 characters (e.g. ABCDE1234F).",
        )

    current_user.encrypted_pan = encrypt_text(pan_str)
    current_user.pan_masked = mask_pan(pan_str)

    audit = AuditLog(user_id=current_user.id, action="PAN_UPDATED", details={})
    db.add(audit)
    db.commit()
    return {"message": "PAN updated and encrypted securely.", "pan_masked": current_user.pan_masked}


@router.put("/me/password")
def change_my_password(
    payload: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Changes password after verifying current password."""
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )

    current_user.hashed_password = get_password_hash(payload.new_password)
    audit = AuditLog(user_id=current_user.id, action="PASSWORD_CHANGED", details={})
    db.add(audit)
    db.commit()
    return {"message": "Password changed successfully."}


@router.get("/me/export", response_model=UserDataExport)
def export_user_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    DPDP-compliant complete data export in JSON format.
    Exports all personal profile data, documents metadata, transactions, profiles, and reports.
    """
    profiles = db.query(FinancialProfile).filter(FinancialProfile.user_id == current_user.id).all()
    documents = db.query(Document).filter(Document.user_id == current_user.id).all()
    transactions = db.query(Transaction).filter(Transaction.user_id == current_user.id).all()
    calculations = db.query(TaxCalculationRecord).filter(TaxCalculationRecord.user_id == current_user.id).all()
    reports = db.query(ReportRecord).filter(ReportRecord.user_id == current_user.id).all()

    audit = AuditLog(user_id=current_user.id, action="DATA_EXPORTED", details={})
    db.add(audit)
    db.commit()

    return {
        "user_profile": {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "dob": current_user.dob,
            "age_bracket": current_user.age_bracket,
            "residential_status": current_user.residential_status,
            "employment_type": current_user.employment_type,
            "pan_masked": current_user.pan_masked,
            "created_at": current_user.created_at.isoformat(),
        },
        "profiles": [
            {
                "financial_year": p.financial_year,
                "selected_regime": p.selected_regime,
                "salary_data": p.salary_data,
                "deductions_data": p.deductions_data,
                "house_prop_data": p.house_prop_data,
            }
            for p in profiles
        ],
        "documents": [
            {"id": d.id, "file_name": d.file_name, "file_type": d.file_type, "doc_type": d.doc_type, "status": d.status}
            for d in documents
        ],
        "transactions": [
            {"id": t.id, "date": t.date, "description": t.description, "amount": t.amount, "category": t.category}
            for t in transactions
        ],
        "calculations": [
            {"id": c.id, "financial_year": c.financial_year, "recommended_regime": c.recommended_regime, "tax_diff": c.tax_difference}
            for c in calculations
        ],
        "reports": [
            {"id": r.id, "file_name": r.file_name, "created_at": r.created_at.isoformat()}
            for r in reports
        ],
        "exported_at": datetime.now(timezone.utc).isoformat(),
    }


@router.delete("/me", status_code=status.HTTP_200_OK)
def delete_my_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Complete account deletion and data purge (DPDP compliant).
    Deletes user record, encrypted files from disk, and all cascade-related database rows.
    """
    # 1. Delete physical files associated with documents
    docs = db.query(Document).filter(Document.user_id == current_user.id).all()
    for d in docs:
        if d.storage_path and os.path.exists(d.storage_path):
            try:
                os.remove(d.storage_path)
            except Exception:
                pass

    # 2. Delete reports files
    reports = db.query(ReportRecord).filter(ReportRecord.user_id == current_user.id).all()
    for r in reports:
        if r.storage_path and os.path.exists(r.storage_path):
            try:
                os.remove(r.storage_path)
            except Exception:
                pass

    # 3. Delete user row in DB (cascades to all child tables)
    db.delete(current_user)
    db.commit()

    return {"message": "Account and all associated documents, extractions, and tax calculations permanently purged."}
