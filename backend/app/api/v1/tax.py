"""
Tax API Router
Deterministic pure Python computation, Old vs New comparison, HRA calculator, and statutory rules.
"""

from decimal import Decimal
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.db.models import AuditLog, FinancialProfile, TaxCalculationRecord, User
from app.db.session import get_db
from app.schemas.tax import HraCalcRequest, TaxCalculateRequest
from app.services.tax_engine.calculator import calculate_tax
from app.services.tax_engine.exemptions import compute_hra_exemption
from app.services.tax_engine.regime_compare import compare_regimes
from app.services.tax_engine.rules_provider import TaxRulesProvider

router = APIRouter(prefix="/tax", tags=["Tax Engine & Calculation"])


def _enrich_calc_result(res: Dict[str, Any]) -> Dict[str, Any]:
    """Ensures calculation dictionary contains aliases for UI convenience."""
    res["total_tax_liability"] = res.get("gross_tax_liability", 0.0)
    res["total_deductions_allowed"] = res.get("total_chapter_vi_a_deductions", 0.0)
    res["taxable_income"] = res.get("taxable_total_income", 0.0)
    res["base_tax"] = res.get("slab_tax", 0.0)
    res["surcharge"] = res.get("net_surcharge", 0.0)
    res["cess"] = res.get("health_and_education_cess", 0.0)
    res["net_tax_payable"] = res.get("balance_payable_or_refund", 0.0)

    # Enrich slab breakdown items with aliases
    enriched_slabs = []
    for sb in res.get("slab_breakdown", []):
        enriched_slabs.append({
            "slab": sb.get("range", ""),
            "range": sb.get("range", ""),
            "taxable_in_slab": sb.get("taxable_amount", 0.0),
            "taxable_amount": sb.get("taxable_amount", 0.0),
            "rate": f"{sb.get('rate_pct', 0):.0f}%" if "rate_pct" in sb else sb.get("rate", ""),
            "rate_pct": sb.get("rate_pct", 0),
            "tax": sb.get("tax_amount", 0.0),
            "tax_amount": sb.get("tax_amount", 0.0),
        })
    res["slab_breakdown"] = enriched_slabs

    # Enrich audit trace
    res["audit_trace"] = [
        {
            "step": s.get("label", s.get("step_id", "")),
            "description": s.get("notes") or s.get("formula_text") or "",
            "amount": s.get("output_amount"),
            "rule_applied": s.get("section_ref"),
        }
        for s in res.get("calculation_breakdown", [])
    ]

    res["interest_234"] = {
        "total_interest": res.get("statutory_interest_234abc", 0.0),
        "interest_234a": 0.0,
        "interest_234b": 0.0,
        "interest_234c": res.get("statutory_interest_234abc", 0.0),
    }
    return res


@router.post("/calculate")
def calculate_tax_liability(
    payload: TaxCalculateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Computes tax liability under the specified regime and FY using the pure Python tax engine.
    Returns complete step-by-step breakdown and persists a calculation snapshot.
    """
    profile = db.query(FinancialProfile).filter(
        FinancialProfile.user_id == current_user.id,
        FinancialProfile.financial_year == payload.financial_year,
    ).first()

    salary_data = payload.salary_data or (profile.salary_data if profile else {})
    house_prop_data = payload.house_prop_data or (profile.house_prop_data if profile else {})
    other_sources_data = payload.other_sources_data or (profile.other_sources_data if profile else {})
    capital_gains_data = payload.capital_gains_data or (profile.capital_gains_data if profile else {})
    deductions_data = payload.deductions_data or (profile.deductions_data if profile else {})
    taxes_paid_data = payload.taxes_paid_data or (profile.taxes_paid_data if profile else {})

    age_bracket = payload.age_bracket or current_user.age_bracket
    employment_type = payload.employment_type or current_user.employment_type
    is_metro = payload.is_metro if payload.is_metro is not None else current_user.is_metro

    calc_res = calculate_tax(
        financial_year=payload.financial_year,
        regime=payload.regime,
        salary_data=salary_data,
        house_prop_data=house_prop_data,
        other_sources_data=other_sources_data,
        capital_gains_data=capital_gains_data,
        deductions_data=deductions_data,
        taxes_paid_data=taxes_paid_data,
        age_bracket=age_bracket,
        employment_type=employment_type,
        is_metro=is_metro,
        months_delay_filing=payload.months_delay_filing,
    )

    _enrich_calc_result(calc_res)

    audit = AuditLog(
        user_id=current_user.id,
        action="TAX_CALCULATED",
        details={"financial_year": payload.financial_year, "regime": payload.regime, "liability": calc_res["gross_tax_liability"]},
    )
    db.add(audit)
    db.commit()

    return calc_res


def _execute_comparison(
    financial_year: str,
    salary_data: Dict[str, Any],
    house_prop_data: Dict[str, Any],
    other_sources_data: Dict[str, Any],
    capital_gains_data: Dict[str, Any],
    deductions_data: Dict[str, Any],
    taxes_paid_data: Dict[str, Any],
    age_bracket: str,
    employment_type: str,
    is_metro: bool,
    current_user: User,
    db: Session,
) -> Dict[str, Any]:
    comp_res = compare_regimes(
        financial_year=financial_year,
        salary_data=salary_data,
        house_prop_data=house_prop_data,
        other_sources_data=other_sources_data,
        capital_gains_data=capital_gains_data,
        deductions_data=deductions_data,
        taxes_paid_data=taxes_paid_data,
        age_bracket=age_bracket,
        employment_type=employment_type,
        is_metro=is_metro,
    )

    _enrich_calc_result(comp_res["old_regime"])
    _enrich_calc_result(comp_res["new_regime"])

    comp_res["tax_diff"] = comp_res.get("tax_savings", 0.0)
    comp_res["tax_difference"] = comp_res.get("tax_savings", 0.0)
    comp_res["break_even_deduction"] = comp_res.get("break_even_deductions", 0.0)
    comp_res["reason"] = comp_res.get("plain_language_explanation", "")

    # Save calculation record in DB
    calc_record = TaxCalculationRecord(
        user_id=current_user.id,
        financial_year=financial_year,
        rule_config_version="1.0",
        inputs_snapshot={
            "salary_data": salary_data,
            "deductions_data": deductions_data,
            "house_prop_data": house_prop_data,
        },
        old_regime_result=comp_res["old_regime"],
        new_regime_result=comp_res["new_regime"],
        recommended_regime=comp_res["recommended_regime"],
        tax_difference=comp_res["tax_savings"],
        break_even_deductions=comp_res["break_even_deductions"],
    )
    db.add(calc_record)
    db.commit()

    comp_res["calculation_id"] = calc_record.id
    return comp_res


@router.get("/compare")
def compare_tax_regimes(
    financial_year: str = "2025-26",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Executes full comparative analysis between Old and New regimes for user's profile.
    Computes break-even deduction required for Old Regime to win.
    """
    profile = db.query(FinancialProfile).filter(
        FinancialProfile.user_id == current_user.id,
        FinancialProfile.financial_year == financial_year,
    ).first()

    salary_data = profile.salary_data if profile else {}
    house_prop_data = profile.house_prop_data if profile else {}
    other_sources_data = profile.other_sources_data if profile else {}
    capital_gains_data = profile.capital_gains_data if profile else {}
    deductions_data = profile.deductions_data if profile else {}
    taxes_paid_data = profile.taxes_paid_data if profile else {}

    return _execute_comparison(
        financial_year=financial_year,
        salary_data=salary_data,
        house_prop_data=house_prop_data,
        other_sources_data=other_sources_data,
        capital_gains_data=capital_gains_data,
        deductions_data=deductions_data,
        taxes_paid_data=taxes_paid_data,
        age_bracket=current_user.age_bracket,
        employment_type=current_user.employment_type,
        is_metro=current_user.is_metro,
        current_user=current_user,
        db=db,
    )


@router.post("/compare")
def compare_tax_regimes_post(
    payload: Optional[Any] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    POST variant of compare endpoint to support custom input overrides from client.
    Accepts both JSON dict or Pydantic models.
    """
    if hasattr(payload, "model_dump"):
        p = payload.model_dump(exclude_unset=True)
    elif isinstance(payload, dict):
        p = payload
    else:
        p = {}

    financial_year = p.get("financial_year", "2025-26")

    profile = db.query(FinancialProfile).filter(
        FinancialProfile.user_id == current_user.id,
        FinancialProfile.financial_year == financial_year,
    ).first()

    salary_data = p.get("salary_data") or (profile.salary_data if profile else {})
    house_prop_data = p.get("house_prop_data") or (profile.house_prop_data if profile else {})
    other_sources_data = p.get("other_sources_data") or (profile.other_sources_data if profile else {})
    capital_gains_data = p.get("capital_gains_data") or (profile.capital_gains_data if profile else {})
    deductions_data = p.get("deductions_data") or (profile.deductions_data if profile else {})
    taxes_paid_data = p.get("taxes_paid_data") or (profile.taxes_paid_data if profile else {})

    age_bracket = p.get("age_bracket") or current_user.age_bracket
    employment_type = p.get("employment_type") or current_user.employment_type
    is_metro = p.get("is_metro") if p.get("is_metro") is not None else current_user.is_metro

    return _execute_comparison(
        financial_year=financial_year,
        salary_data=salary_data,
        house_prop_data=house_prop_data,
        other_sources_data=other_sources_data,
        capital_gains_data=capital_gains_data,
        deductions_data=deductions_data,
        taxes_paid_data=taxes_paid_data,
        age_bracket=age_bracket,
        employment_type=employment_type,
        is_metro=is_metro,
        current_user=current_user,
        db=db,
    )


@router.post("/hra-calculator")
def interactive_hra_calculator(payload: HraCalcRequest):
    """Computes House Rent Allowance (HRA) exemption with least-of-three breakdown."""
    provider = TaxRulesProvider.get_instance()
    rules = provider.get_rules_for_fy(payload.financial_year)

    exempt_val, steps = compute_hra_exemption(
        basic_salary=Decimal(str(payload.basic_salary)),
        da_amount=Decimal(str(payload.da_amount)),
        hra_received=Decimal(str(payload.hra_received)),
        annual_rent_paid=Decimal(str(payload.annual_rent_paid)),
        is_metro=payload.is_metro,
        regime=payload.regime,
        rules=rules,
    )

    taxable_hra = max(Decimal("0.00"), Decimal(str(payload.hra_received)) - exempt_val)

    return {
        "financial_year": payload.financial_year,
        "regime": payload.regime,
        "basic_salary": payload.basic_salary,
        "da_amount": payload.da_amount,
        "hra_received": payload.hra_received,
        "annual_rent_paid": payload.annual_rent_paid,
        "is_metro": payload.is_metro,
        "exempt_hra": float(exempt_val),
        "taxable_hra": float(taxable_hra),
        "calculation_steps": [s.to_dict() for s in steps],
        "disclaimer": "Estimate only; not professional tax advice.",
    }


@router.get("/rules/{financial_year}")
def get_statutory_rules(financial_year: str):
    """Exposes loaded statutory configuration for transparency and explainability."""
    provider = TaxRulesProvider.get_instance()
    try:
        rules = provider.get_rules_for_fy(financial_year)
        section_mapping = provider.get_section_mapping()
        return {
            "financial_year": financial_year,
            "metadata": rules.get("metadata", {}),
            "new_regime": rules.get("new_regime", {}),
            "old_regime": rules.get("old_regime", {}),
            "section_mapping": section_mapping.get("mappings", {}),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rules for FY {financial_year} not found: {str(e)}",
        )
