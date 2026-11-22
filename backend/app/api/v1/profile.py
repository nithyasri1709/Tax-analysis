"""
Financial Profile API Router
Supports Manual Entry Mode without documents, financial summary views, and copying last year's profile.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.db.models import AuditLog, FinancialProfile, User
from app.db.session import get_db

router = APIRouter(prefix="/profile", tags=["Financial Profile & Manual Entry"])


class FinancialProfileUpdate(BaseModel):
    financial_year: str = "2025-26"
    selected_regime: str = "new"
    salary_data: Optional[Dict[str, Any]] = None
    house_prop_data: Optional[Dict[str, Any]] = None
    other_sources_data: Optional[Dict[str, Any]] = None
    capital_gains_data: Optional[Dict[str, Any]] = None
    deductions_data: Optional[Dict[str, Any]] = None
    taxes_paid_data: Optional[Dict[str, Any]] = None


@router.get("/summary")
def get_financial_summary(
    financial_year: str = "2025-26",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves taxpayer's financial profile data for the specified FY."""
    profile = db.query(FinancialProfile).filter(
        FinancialProfile.user_id == current_user.id,
        FinancialProfile.financial_year == financial_year,
    ).first()

    if not profile:
        profile = FinancialProfile(
            user_id=current_user.id,
            financial_year=financial_year,
            selected_regime="new",
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)

    return {
        "id": profile.id,
        "financial_year": profile.financial_year,
        "selected_regime": profile.selected_regime,
        "salary_data": profile.salary_data or {},
        "house_prop_data": profile.house_prop_data or {},
        "other_sources_data": profile.other_sources_data or {},
        "capital_gains_data": profile.capital_gains_data or {},
        "deductions_data": profile.deductions_data or {},
        "taxes_paid_data": profile.taxes_paid_data or {},
        "completeness_score": profile.completeness_score or 25,
        "user_demographics": {
            "full_name": current_user.full_name,
            "dob": current_user.dob,
            "age_bracket": current_user.age_bracket,
            "employment_type": current_user.employment_type,
            "is_metro": current_user.is_metro,
            "residential_status": current_user.residential_status,
            "pan_masked": current_user.pan_masked,
        },
    }


@router.put("/summary")
def update_financial_summary(
    payload: FinancialProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Manual Entry Mode: Updates user financial values directly via form without uploading documents."""
    profile = db.query(FinancialProfile).filter(
        FinancialProfile.user_id == current_user.id,
        FinancialProfile.financial_year == payload.financial_year,
    ).first()

    if not profile:
        profile = FinancialProfile(
            user_id=current_user.id,
            financial_year=payload.financial_year,
            selected_regime=payload.selected_regime,
        )
        db.add(profile)

    profile.selected_regime = payload.selected_regime
    if payload.salary_data is not None:
        profile.salary_data = payload.salary_data
    if payload.house_prop_data is not None:
        profile.house_prop_data = payload.house_prop_data
    if payload.other_sources_data is not None:
        profile.other_sources_data = payload.other_sources_data
    if payload.capital_gains_data is not None:
        profile.capital_gains_data = payload.capital_gains_data
    if payload.deductions_data is not None:
        profile.deductions_data = payload.deductions_data
    if payload.taxes_paid_data is not None:
        profile.taxes_paid_data = payload.taxes_paid_data

    # Calculate completeness
    score = 30
    if profile.salary_data and profile.salary_data.get("gross_salary"):
        score += 25
    if profile.deductions_data:
        score += 20
    if profile.taxes_paid_data:
        score += 15
    profile.completeness_score = min(100, score)

    audit = AuditLog(
        user_id=current_user.id,
        action="PROFILE_SUMMARY_UPDATED",
        details={"financial_year": payload.financial_year},
    )
    db.add(audit)
    db.commit()
    db.refresh(profile)

    return {"message": "Financial summary updated successfully.", "profile": profile}


@router.post("/copy-last-year")
def copy_last_year_profile(
    target_fy: str = "2025-26",
    source_fy: str = "2024-25",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Copies previous financial year's profile data as a starting foundation for current year."""
    source = db.query(FinancialProfile).filter(
        FinancialProfile.user_id == current_user.id,
        FinancialProfile.financial_year == source_fy,
    ).first()
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source profile for FY {source_fy} does not exist.",
        )

    target = db.query(FinancialProfile).filter(
        FinancialProfile.user_id == current_user.id,
        FinancialProfile.financial_year == target_fy,
    ).first()
    if not target:
        target = FinancialProfile(
            user_id=current_user.id,
            financial_year=target_fy,
            selected_regime="new",
        )
        db.add(target)

    target.salary_data = dict(source.salary_data or {})
    target.deductions_data = dict(source.deductions_data or {})
    target.house_prop_data = dict(source.house_prop_data or {})
    target.other_sources_data = dict(source.other_sources_data or {})

    db.commit()
    return {"message": f"Successfully initialized FY {target_fy} profile using FY {source_fy} data."}
