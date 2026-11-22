"""
Investments API Router
Detailed analysis of detected investments, section utilization, 80C combined meter,
and regime-specific deduction eligibility explanations.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.db.models import FinancialProfile, Transaction, User
from app.db.session import get_db
from app.services.tax_engine.rules_provider import TaxRulesProvider

router = APIRouter(prefix="/investments", tags=["Investment Analysis"])


@router.get("")
def get_investment_analysis(
    financial_year: str = "2025-26",
    regime: str = "new",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Computes detailed investment utilization, Section 80C meter,
    unused limit bars, and regime eligibility commentary.
    """
    provider = TaxRulesProvider.get_instance()
    rules = provider.get_rules_for_fy(financial_year)
    norm_regime = regime.lower().strip()

    profile = db.query(FinancialProfile).filter(
        FinancialProfile.user_id == current_user.id,
        FinancialProfile.financial_year == financial_year,
    ).first()

    deductions = profile.deductions_data if profile else {}
    salary = profile.salary_data if profile else {}
    hp_data = profile.house_prop_data if profile else {}

    # Gather amounts
    epf = float(deductions.get("epf", 0.0))
    ppf = float(deductions.get("ppf", 0.0))
    elss = float(deductions.get("elss", 0.0))
    life_insurance = float(deductions.get("life_insurance", 0.0))
    hl_principal = float(deductions.get("home_loan_principal", 0.0))
    tuition = float(deductions.get("tuition_fees", 0.0))
    nsc = float(deductions.get("nsc", 0.0))
    fd_5yr = float(deductions.get("five_year_fd", 0.0))

    total_80c_invested = epf + ppf + elss + life_insurance + hl_principal + tuition + nsc + fd_5yr
    cap_80c = 150000.0
    allowed_80c = min(total_80c_invested, cap_80c) if norm_regime == "old" else 0.0
    remaining_80c = max(0.0, cap_80c - total_80c_invested) if norm_regime == "old" else 0.0

    # 80CCD(1B) NPS
    nps_tier1 = float(deductions.get("80ccd_1b", 0.0))
    cap_nps = 50000.0
    allowed_nps = min(nps_tier1, cap_nps) if norm_regime == "old" else 0.0
    remaining_nps = max(0.0, cap_nps - nps_tier1) if norm_regime == "old" else 0.0

    # 80CCD(2) Employer NPS
    employer_nps = float(deductions.get("80ccd_2", 0.0))
    basic_da = float(salary.get("basic_salary", 0.0)) + float(salary.get("da_amount", 0.0))
    cap_emp_nps = basic_da * 0.14
    allowed_emp_nps = min(employer_nps, cap_emp_nps)

    # 80D Health Insurance
    health_self = float(deductions.get("health_insurance_self") or deductions.get("80d_self") or 0.0)
    health_parents = float(deductions.get("health_insurance_parents") or deductions.get("80d_parents") or 0.0)
    preventive = float(deductions.get("preventive_health_checkup") or deductions.get("80d_preventive") or 0.0)
    total_health = health_self + health_parents + preventive
    cap_health = 50000.0 if current_user.age_bracket != "regular" else 25000.0
    allowed_health = min(total_health, cap_health + 25000.0) if norm_regime == "old" else 0.0

    # 24(b) Home loan interest
    hl_interest_sop = float(hp_data.get("interest_self_occupied", 0.0))
    cap_24b = 200000.0
    allowed_24b = min(hl_interest_sop, cap_24b) if norm_regime == "old" else 0.0
    remaining_24b = max(0.0, cap_24b - hl_interest_sop) if norm_regime == "old" else 0.0

    # Detailed item cards
    items = [
        {
            "category": "Employee Provident Fund (EPF)",
            "section": "80C",
            "amount": epf,
            "statutory_cap": cap_80c,
            "allowed_in_regime": allowed_80c > 0 and norm_regime == "old",
            "reason": "EPF qualifies under Section 80C in Old Regime only. Barred under New Regime.",
        },
        {
            "category": "Public Provident Fund (PPF)",
            "section": "80C",
            "amount": ppf,
            "statutory_cap": cap_80c,
            "allowed_in_regime": norm_regime == "old",
            "reason": "PPF qualifies under Section 80C in Old Regime only. Barred under New Regime.",
        },
        {
            "category": "ELSS Tax Saver Mutual Funds",
            "section": "80C",
            "amount": elss,
            "statutory_cap": cap_80c,
            "allowed_in_regime": norm_regime == "old",
            "reason": "ELSS counts under Section 80C with 3-year lock-in (Old Regime only).",
        },
        {
            "category": "Life Insurance Premium",
            "section": "80C",
            "amount": life_insurance,
            "statutory_cap": cap_80c,
            "allowed_in_regime": norm_regime == "old",
            "reason": "Eligible under Section 80C (Old Regime only). Premium must not exceed 10% of sum assured.",
        },
        {
            "category": "Home Loan Principal Repayment",
            "section": "80C",
            "amount": hl_principal,
            "statutory_cap": cap_80c,
            "allowed_in_regime": norm_regime == "old",
            "reason": "Repayment of residential housing loan principal counts under Section 80C (Old Regime only).",
        },
        {
            "category": "National Pension System (NPS Tier-1)",
            "section": "80CCD(1B)",
            "amount": nps_tier1,
            "statutory_cap": cap_nps,
            "allowed_in_regime": norm_regime == "old",
            "reason": "Additional ₹50,000 deduction under Section 80CCD(1B) available in Old Regime only.",
        },
        {
            "category": "Employer NPS Contribution",
            "section": "80CCD(2)",
            "amount": employer_nps,
            "statutory_cap": cap_emp_nps,
            "allowed_in_regime": True,
            "reason": "Deduction for employer NPS contribution is allowed in BOTH Old and New Regimes up to 14% of Basic+DA.",
        },
        {
            "category": "Health Insurance (Mediclaim)",
            "section": "80D",
            "amount": total_health,
            "statutory_cap": cap_health + 25000.0,
            "allowed_in_regime": norm_regime == "old",
            "reason": "Medical insurance premium paid via non-cash mode qualifies in Old Regime only.",
        },
    ]

    recommendations = []
    if remaining_80c > 0 and norm_regime == "old":
        recommendations.append({
            "section": "80C",
            "section_2025": "80C",
            "headroom": remaining_80c,
            "suggestion": f"You can invest up to ₹{remaining_80c:,.0f} in ELSS mutual funds, PPF, or 5-year tax-saving FDs before 31st March to maximize Section 80C.",
        })
    if remaining_nps > 0 and norm_regime == "old":
        recommendations.append({
            "section": "80CCD(1B)",
            "section_2025": "80CCD(1B)",
            "headroom": remaining_nps,
            "suggestion": f"Contribute ₹{remaining_nps:,.0f} to NPS Tier-1 to claim exclusive deduction over and above Section 80C.",
        })
    if norm_regime == "old" and (cap_health + 25000.0 - total_health) > 0:
        recommendations.append({
            "section": "80D",
            "section_2025": "80D",
            "headroom": max(0.0, (cap_health + 25000.0) - total_health),
            "suggestion": "Review health insurance coverage for self, family, and parents to claim up to ₹75,000 / ₹1,00,000 under Section 80D.",
        })
    if not recommendations:
        recommendations.append({
            "section": "General",
            "headroom": 0.0,
            "suggestion": "Your tax-saving investment limits are well utilized for this financial year.",
        })

    return {
        "financial_year": financial_year,
        "selected_regime": norm_regime,
        "regime": norm_regime,
        "regime_note": "Section 80C deductions are not available under the New Tax Regime." if norm_regime == "new" else "Chapter VI-A deductions are active under Old Regime.",
        "section_80c_meter": {
            "total_invested": total_80c_invested,
            "statutory_cap": cap_80c,
            "cap": cap_80c,
            "utilized_amount": allowed_80c,
            "allowed": allowed_80c,
            "total_claimed": allowed_80c,
            "remaining_limit": remaining_80c,
            "remaining_headroom": remaining_80c,
            "percentage_utilized": min(100.0, round((total_80c_invested / cap_80c) * 100, 1)),
            "utilization_pct": min(100.0, round((total_80c_invested / cap_80c) * 100, 1)),
            "components": {
                "epf": epf,
                "ppf": ppf,
                "elss": elss,
                "life_insurance": life_insurance,
                "home_loan_principal": hl_principal,
                "tuition_fees": tuition,
                "nsc": nsc,
                "five_year_fd": fd_5yr,
            },
            "regime_warning": "Section 80C deductions are not available under the New Tax Regime." if norm_regime == "new" else None,
        },
        "section_80ccd_1b_nps": {
            "invested": nps_tier1,
            "cap": cap_nps,
            "allowed": allowed_nps,
            "remaining_headroom": remaining_nps,
        },
        "section_80d_health": {
            "self_family": health_self,
            "parents": health_parents,
            "preventive_checkup": preventive,
            "cap": cap_health + 25000.0,
            "allowed": allowed_health,
            "remaining_headroom": max(0.0, (cap_health + 25000.0) - total_health) if norm_regime == "old" else 0.0,
        },
        "section_24b_home_loan_interest": {
            "interest_paid": hl_interest_sop,
            "cap": cap_24b,
            "allowed": allowed_24b,
            "remaining_headroom": remaining_24b,
        },
        "recommendations": recommendations,
        "section_caps": [
            {
                "section": "80C (Combined)",
                "limit": cap_80c,
                "utilized": allowed_80c,
                "remaining": remaining_80c,
                "allowed_in_regime": norm_regime == "old",
            },
            {
                "section": "80CCD(1B) (NPS)",
                "limit": cap_nps,
                "utilized": allowed_nps,
                "remaining": remaining_nps,
                "allowed_in_regime": norm_regime == "old",
            },
            {
                "section": "80CCD(2) (Employer NPS)",
                "limit": cap_emp_nps,
                "utilized": allowed_emp_nps,
                "remaining": max(0.0, cap_emp_nps - allowed_emp_nps),
                "allowed_in_regime": True,
            },
            {
                "section": "80D (Health Insurance)",
                "limit": cap_health + 25000.0,
                "utilized": allowed_health,
                "remaining": max(0.0, (cap_health + 25000.0) - total_health) if norm_regime == "old" else 0.0,
                "allowed_in_regime": norm_regime == "old",
            },
        ],
        "investments_list": items,
        "disclaimer": "Estimate only; not professional tax advice.",
    }
