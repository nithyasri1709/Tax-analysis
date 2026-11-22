"""
Deductions Advisor API Router
Flagship missed-deduction detection, interactive clarifying questionnaire, and live What-If simulation.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.db.models import AuditLog, FinancialProfile, Transaction, User
from app.db.session import get_db
from app.schemas.deduction import QuestionAnswerRequest, WhatIfRequest
from app.services.deductions_advisor.advisor import (
    analyze_missed_deductions,
    simulate_what_if_scenario,
)

router = APIRouter(prefix="/deductions", tags=["Missed-Deductions Advisor & What-If"])


@router.get("/missed")
def get_missed_deductions(
    financial_year: str = "2025-26",
    regime: str = "new",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Flagship rule-driven deduction gap analyzer.
    Detects unutilized limits, computes marginal tax savings, and surfaces clarifying questions.
    """
    profile = db.query(FinancialProfile).filter(
        FinancialProfile.user_id == current_user.id,
        FinancialProfile.financial_year == financial_year,
    ).first()

    salary_data = profile.salary_data if profile else {}
    deductions_data = profile.deductions_data if profile else {}
    house_prop_data = profile.house_prop_data if profile else {}

    res = analyze_missed_deductions(
        financial_year=financial_year,
        selected_regime=regime,
        salary_data=salary_data,
        deductions_data=deductions_data,
        house_prop_data=house_prop_data,
        age_bracket=current_user.age_bracket,
        employment_type=current_user.employment_type,
    )

    # Provide standardized aliases for frontend
    res["total_potential_tax_savings"] = res.get("total_potential_savings", 0.0)
    res["missed_deductions"] = [
        {
            "section_1961": o.get("section", ""),
            "section_2025": o.get("section", ""),
            "name": o.get("category", ""),
            "category": o.get("category", ""),
            "max_limit": o.get("statutory_limit", 0.0),
            "current_claimed": o.get("claimed_amount", 0.0),
            "potential_additional": o.get("remaining_eligible", 0.0),
            "estimated_tax_savings": o.get("estimated_tax_savings", 0.0),
            "status": "CLAIMED" if o.get("remaining_eligible", 0.0) <= 0 else "ELIGIBLE",
            "condition_description": o.get("conditions", ""),
            "action_needed": o.get("required_documents", ""),
            "regime_availability": o.get("regime_relevance", ""),
        }
        for o in res.get("opportunities", [])
    ]
    res["clarifying_questions"] = [
        {
            "id": q.get("question_id", ""),
            "question": q.get("title", ""),
            "field_target": q.get("field_target", ""),
            "section": q.get("section", "80"),
            "input_type": "number" if q.get("input_type") == "currency" else q.get("input_type", "number"),
            "help_text": q.get("description", ""),
        }
        for q in res.get("clarifying_questions", [])
    ]
    res["disclaimer"] = "Estimate only; not professional tax advice."
    return res


@router.post("/answer-question")
def submit_question_answer(
    payload: QuestionAnswerRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Submits user response to clarifying questionnaire, updates the profile live,
    and returns updated missed deductions.
    """
    profile = db.query(FinancialProfile).filter(
        FinancialProfile.user_id == current_user.id,
        FinancialProfile.financial_year == payload.financial_year,
    ).first()

    if not profile:
        profile = FinancialProfile(
            user_id=current_user.id,
            financial_year=payload.financial_year,
            selected_regime="new",
        )
        db.add(profile)
        db.flush()

    deductions_data = dict(profile.deductions_data or {})
    try:
        val = float(payload.answer_value)
    except Exception:
        val = payload.answer_value

    deductions_data[payload.field_target] = val
    profile.deductions_data = deductions_data
    profile.completeness_score = min(100, (profile.completeness_score or 30) + 10)

    audit = AuditLog(
        user_id=current_user.id,
        action="QUESTION_ANSWERED",
        details={"question_id": payload.question_id, "field": payload.field_target, "value": val},
    )
    db.add(audit)
    db.commit()

    return {"message": "Answer recorded and profile updated successfully."}


@router.post("/what-if")
def live_what_if_simulation(
    payload: WhatIfRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    What-If Simulator:
    Recalculates tax savings dynamically when taxpayer adjusts sliders for 80C, NPS, or Health Insurance.
    """
    profile = db.query(FinancialProfile).filter(
        FinancialProfile.user_id == current_user.id,
        FinancialProfile.financial_year == payload.financial_year,
    ).first()

    salary_data = profile.salary_data if profile else {"gross_salary": 1500000.0, "basic_salary": 600000.0}
    deductions_data = profile.deductions_data if profile else {}

    additions = {
        "elss": payload.additional_80c,
        "80ccd_1b": payload.additional_nps_tier1,
        "health_insurance_self": payload.additional_80d_health,
        "80ccd_2": payload.additional_employer_nps,
    }

    sim_res = simulate_what_if_scenario(
        financial_year=payload.financial_year,
        regime=payload.regime,
        base_salary_data=salary_data,
        base_deductions_data=deductions_data,
        additional_investments=additions,
        age_bracket=current_user.age_bracket,
        employment_type=current_user.employment_type,
    )

    sim_res["tax_saved"] = sim_res.get("tax_savings", 0.0)
    sim_res["baseline_deductions"] = sum(float(v) for v in deductions_data.values() if isinstance(v, (int, float)))
    sim_res["simulated_deductions"] = sim_res["baseline_deductions"] + sum(additions.values())
    sim_res["disclaimer"] = "Estimate only; not professional tax advice."
    return sim_res
