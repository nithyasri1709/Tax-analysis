"""
Tax-Grounded Q&A Chat Router
Provides an explainable tax assistant that answers taxpayer questions
using ONLY the taxpayer's computed breakdown, formula traces, and statutory rule configs.
Refuses to give professional legal advice or invent rules.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.db.models import FinancialProfile, TaxCalculationRecord, User
from app.db.session import get_db
from app.services.tax_engine.calculator import calculate_tax
from app.services.tax_engine.regime_compare import compare_regimes
from app.services.tax_engine.rules_provider import TaxRulesProvider

router = APIRouter(prefix="/chat", tags=["Tax-Grounded Assistant Chat"])


class ChatQueryRequest(BaseModel):
    message: str
    financial_year: str = "2025-26"
    regime: str = "new"


class ChatQueryResponse(BaseModel):
    answer: str
    citations: List[str]
    disclaimer: str = "Estimate only; not professional tax advice."


@router.post("/ask", response_model=ChatQueryResponse)
def ask_tax_grounded_assistant(
    payload: ChatQueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Tax-grounded Q&A assistant:
    Retrieves user's calculated steps and rules to explain numbers and decisions.
    """
    query = payload.message.lower().strip()
    fy = payload.financial_year
    reg = payload.regime.lower()

    # Load user's profile and run engine to get ground truth steps
    profile = db.query(FinancialProfile).filter(
        FinancialProfile.user_id == current_user.id,
        FinancialProfile.financial_year == fy,
    ).first()

    salary_data = profile.salary_data if profile else {}
    deductions_data = profile.deductions_data if profile else {}
    house_prop_data = profile.house_prop_data if profile else {}

    calc_res = calculate_tax(
        financial_year=fy,
        regime=reg,
        salary_data=salary_data,
        house_prop_data=house_prop_data,
        deductions_data=deductions_data,
        age_bracket=current_user.age_bracket,
        employment_type=current_user.employment_type,
        is_metro=current_user.is_metro,
    )

    comparison = compare_regimes(
        financial_year=fy,
        salary_data=salary_data,
        house_prop_data=house_prop_data,
        deductions_data=deductions_data,
        age_bracket=current_user.age_bracket,
        employment_type=current_user.employment_type,
        is_metro=current_user.is_metro,
    )

    provider = TaxRulesProvider.get_instance()
    sec_map = provider.get_section_mapping().get("mappings", {})

    citations: List[str] = []
    answer = ""

    # Rule-based factual answer matching over ground truth
    if "why" in query and ("tax" in query or "liability" in query or "computed" in query):
        tax = calc_res["gross_tax_liability"]
        income = calc_res["taxable_total_income"]
        rebate = calc_res["rebate_87a"]
        cess = calc_res["health_and_education_cess"]
        answer = (
            f"Your gross tax liability under the {reg.capitalize()} Regime for FY {fy} is **₹{tax:,.2f}**.\n\n"
            f"**Exact Mathematical Derivation:**\n"
            f"1. **Gross Salary:** ₹{calc_res['gross_salary']:,.2f}\n"
            f"2. **Standard Deduction (Section 16(ia)):** ₹{calc_res['standard_deduction']:,.2f}\n"
            f"3. **Taxable Total Income (Section 288A):** ₹{income:,.2f}\n"
            f"4. **Slab Tax:** ₹{calc_res['slab_tax']:,.2f}\n"
            f"5. **Section 87A Rebate:** -₹{rebate:,.2f}\n"
            f"6. **Health & Education Cess (4%):** ₹{cess:,.2f}\n"
            f"7. **Total Liability (Section 288B rounded):** ₹{tax:,.2f}."
        )
        citations.extend(["Section 16(ia)", "Section 87A", "Section 115BAC", "Section 288A", "Section 288B"])

    elif "hra" in query or "rent" in query:
        hra_ex = calc_res["exemptions_total"]
        answer = (
            f"Under Section 10(13A) and Rule 2A, House Rent Allowance (HRA) exemption is granted as the **least of the following three conditions**:\n"
            f"1. Actual HRA received from your employer\n"
            f"2. Rent paid minus 10% of salary (Basic + DA)\n"
            f"3. 50% of salary for Metro cities (Delhi, Mumbai, Kolkata, Chennai) or 40% for Non-Metro cities.\n\n"
            f"Your current allowable HRA exemption under the Old Regime is **₹{hra_ex:,.2f}**. "
            f"*(Note: HRA exemption is not available under the New Concessional Regime per Section 115BAC).*"
        )
        citations.extend(["Section 10(13A)", "Rule 2A of Income-tax Rules", "Section 115BAC"])

    elif "regime" in query or "compare" in query or "better" in query:
        rec = comparison["recommended_regime"].upper()
        savings = comparison["tax_savings"]
        be = comparison["break_even_deductions"]
        answer = (
            f"**Recommended Regime: {rec} TAX REGIME**\n\n"
            f"• Estimated Tax Saving: **₹{savings:,.2f}**\n"
            f"• Old Regime Gross Tax: ₹{comparison['old_regime']['gross_tax_liability']:,.2f}\n"
            f"• New Regime Gross Tax: ₹{comparison['new_regime']['gross_tax_liability']:,.2f}\n\n"
            f"**Break-Even Point:** For your current salary, the Old Regime would only beat the New Regime if your total deductions and exemptions exceed **₹{be:,.2f}**."
        )
        citations.extend(["Section 115BAC", "Chapter VI-A"])

    elif "standard deduction" in query:
        std = calc_res["standard_deduction"]
        answer = (
            f"Under Section 16(ia) of the Income-tax Act, salaried employees and pensioners are entitled to a flat Standard Deduction.\n"
            f"• For FY {fy} in the **New Regime**: ₹75,000\n"
            f"• For FY {fy} in the **Old Regime**: ₹50,000\n"
            f"Your applied standard deduction is **₹{std:,.2f}**."
        )
        citations.extend(["Section 16(ia)", "Finance (No. 2) Act, 2024"])

    elif "80c" in query or "investment" in query:
        claimed_80c = calc_res["deductions_breakdown"].get("80C", 0.0)
        answer = (
            f"Section 80C provides a combined deduction cap of **₹1,50,000** for eligible investments such as EPF, PPF, ELSS, Life Insurance premiums, Tuition fees, and Home loan principal repayments.\n"
            f"• Your currently claimed 80C deduction: **₹{claimed_80c:,.2f}**\n"
            f"• Remaining unutilized 80C limit: **₹{max(0.0, 150000.0 - claimed_80c):,.2f}**\n"
            f"*(Note: Section 80C deductions are not available under the New Tax Regime).* "
        )
        citations.extend(["Section 80C", "Section 80CCE"])

    else:
        answer = (
            f"I am your Intelligent Tax Assistant, grounded strictly in statutory Indian tax provisions and your personal calculation records.\n\n"
            f"You can ask me questions like:\n"
            f"• *Why is my tax liability calculated at ₹{calc_res['gross_tax_liability']:,.0f}?*\n"
            f"• *How is my HRA exemption calculated?*\n"
            f"• *Why is the {comparison['recommended_regime'].capitalize()} Regime recommended for me?*\n"
            f"• *What is my break-even deduction threshold?*\n"
            f"• *What is the standard deduction for FY {fy}?*"
        )
        citations.append("Income-tax Act, 1961 / Income-tax Act, 2025")

    return ChatQueryResponse(
        answer=answer,
        citations=list(set(citations)),
        disclaimer="Estimate only; not professional tax advice.",
    )
