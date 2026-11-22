"""
Reports API Router
PDF generation, download, listing, and cross-report comparison.
Owner-checked and IDOR secure.
"""

from io import BytesIO
import os
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.core.config import settings
from app.db.models import AuditLog, FinancialProfile, ReportRecord, TaxCalculationRecord, Transaction, User
from app.db.session import get_db
from app.schemas.report import ReportCompareResponse, ReportGenerateRequest, ReportOut
from app.services.deductions_advisor.advisor import analyze_missed_deductions
from app.services.reports.pdf_builder import build_tax_report_pdf
from app.services.tax_engine.regime_compare import compare_regimes

router = APIRouter(prefix="/reports", tags=["Reports & Summaries"])


@router.post("/generate", response_model=ReportOut, status_code=status.HTTP_201_CREATED)
def generate_tax_report(
    payload: ReportGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generates a professional 16-section ReportLab PDF report.
    Persists reproducible snapshot in database.
    """
    profile = db.query(FinancialProfile).filter(
        FinancialProfile.user_id == current_user.id,
        FinancialProfile.financial_year == payload.financial_year,
    ).first()

    salary_data = profile.salary_data if profile else {}
    house_prop_data = profile.house_prop_data if profile else {}
    other_sources_data = profile.other_sources_data if profile else {}
    capital_gains_data = profile.capital_gains_data if profile else {}
    deductions_data = profile.deductions_data if profile else {}
    taxes_paid_data = profile.taxes_paid_data if profile else {}

    # Run comparisons
    comparison = compare_regimes(
        financial_year=payload.financial_year,
        salary_data=salary_data,
        house_prop_data=house_prop_data,
        other_sources_data=other_sources_data,
        capital_gains_data=capital_gains_data,
        deductions_data=deductions_data,
        taxes_paid_data=taxes_paid_data,
        age_bracket=current_user.age_bracket,
        employment_type=current_user.employment_type,
        is_metro=current_user.is_metro,
    )

    missed = analyze_missed_deductions(
        financial_year=payload.financial_year,
        selected_regime=comparison["recommended_regime"],
        salary_data=salary_data,
        deductions_data=deductions_data,
        house_prop_data=house_prop_data,
        age_bracket=current_user.age_bracket,
        employment_type=current_user.employment_type,
    )

    # Transactions summary
    txs = db.query(Transaction).filter(
        Transaction.user_id == current_user.id,
        Transaction.financial_year == payload.financial_year,
    ).all()
    cat_map = {}
    for t in txs:
        cat_map.setdefault(t.category, {"category": t.category, "total_amount": 0.0, "tax_eligible_amount": 0.0})
        cat_map[t.category]["total_amount"] += t.amount
        if t.is_potentially_tax_eligible:
            cat_map[t.category]["tax_eligible_amount"] += t.amount

    tx_summary = {"categories": list(cat_map.values())}

    pdf_bytes = build_tax_report_pdf(
        user_name=current_user.full_name,
        pan_masked=current_user.pan_masked or "",
        financial_year=payload.financial_year,
        comparison_data=comparison,
        missed_deductions_data=missed,
        profile_data={"salary": salary_data, "deductions": deductions_data},
        transactions_summary=tx_summary,
    )

    # Save PDF to reports folder
    user_report_dir = Path(settings.STORAGE_DIR) / current_user.id / "reports"
    user_report_dir.mkdir(parents=True, exist_ok=True)
    report_filename = f"TaxReport_{payload.financial_year}_{current_user.id[:8]}.pdf"
    report_path = str(user_report_dir / report_filename)

    with open(report_path, "wb") as f:
        f.write(pdf_bytes)

    summary_metadata = {
        "recommended_regime": comparison["recommended_regime"],
        "tax_savings": comparison["tax_savings"],
        "break_even_deductions": comparison["break_even_deductions"],
        "gross_tax_liability": comparison[f"{comparison['recommended_regime']}_regime"]["gross_tax_liability"],
        "balance_payable_or_refund": comparison[f"{comparison['recommended_regime']}_regime"]["balance_payable_or_refund"],
    }

    report_record = ReportRecord(
        user_id=current_user.id,
        financial_year=payload.financial_year,
        calculation_id=payload.calculation_id,
        file_name=report_filename,
        storage_path=report_path,
        report_summary=summary_metadata,
    )
    db.add(report_record)

    audit = AuditLog(
        user_id=current_user.id,
        action="REPORT_GENERATED",
        details={"financial_year": payload.financial_year, "file_name": report_filename},
    )
    db.add(audit)
    db.commit()
    db.refresh(report_record)

    return report_record


@router.get("", response_model=List[ReportOut])
def list_user_reports(
    financial_year: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lists all generated PDF tax reports for the user."""
    query = db.query(ReportRecord).filter(ReportRecord.user_id == current_user.id)
    if financial_year:
        query = query.filter(ReportRecord.financial_year == financial_year)
    return query.order_by(ReportRecord.created_at.desc()).all()


@router.get("/{report_id}/download")
def download_tax_report_pdf(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Streams the generated PDF report for download. Owner checked."""
    report = db.query(ReportRecord).filter(
        ReportRecord.id == report_id,
        ReportRecord.user_id == current_user.id,
    ).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    if not os.path.exists(report.storage_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report file not found on disk.")

    with open(report.storage_path, "rb") as f:
        pdf_bytes = f.read()

    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{report.file_name}"'},
    )


@router.delete("/{report_id}", status_code=status.HTTP_200_OK)
def delete_tax_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Deletes report record and physical PDF from storage."""
    report = db.query(ReportRecord).filter(
        ReportRecord.id == report_id,
        ReportRecord.user_id == current_user.id,
    ).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    if report.storage_path and os.path.exists(report.storage_path):
        try:
            os.remove(report.storage_path)
        except Exception:
            pass

    db.delete(report)
    db.commit()
    return {"message": "Report deleted successfully."}


@router.get("/compare", response_model=ReportCompareResponse)
def compare_two_reports(
    report_id_1: str = Query(...),
    report_id_2: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Compares two historical tax reports (e.g. across two financial years)."""
    r1 = db.query(ReportRecord).filter(ReportRecord.id == report_id_1, ReportRecord.user_id == current_user.id).first()
    r2 = db.query(ReportRecord).filter(ReportRecord.id == report_id_2, ReportRecord.user_id == current_user.id).first()

    if not r1 or not r2:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or both reports not found.")

    tax1 = r1.report_summary.get("gross_tax_liability", 0.0)
    tax2 = r2.report_summary.get("gross_tax_liability", 0.0)
    diff = round(tax2 - tax1, 2)

    analysis = (
        f"Comparing Report {r1.file_name} (FY {r1.financial_year}) with "
        f"Report {r2.file_name} (FY {r2.financial_year}). "
        f"Gross tax liability moved by ₹{diff:,.2f} ({'increase' if diff > 0 else 'decrease'})."
    )

    return ReportCompareResponse(
        report_1={"id": r1.id, "financial_year": r1.financial_year, "summary": r1.report_summary},
        report_2={"id": r2.id, "financial_year": r2.financial_year, "summary": r2.report_summary},
        tax_diff=diff,
        analysis=analysis,
    )
