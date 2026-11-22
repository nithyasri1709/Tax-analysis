"""
Missed-Deductions Advisor Service (Flagship Module)
Evaluates financial profiles against statutory limits to detect unclaimed deductions,
computes tax savings at marginal rate, generates clarifying questions,
and provides live What-If simulation.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Optional
from app.services.tax_engine.calculator import calculate_tax
from app.services.tax_engine.common import to_decimal
from app.services.tax_engine.rules_provider import TaxRulesProvider


def get_user_marginal_rate(
    financial_year: str,
    regime: str,
    salary_data: Dict[str, Any],
    deductions_data: Dict[str, Any],
    age_bracket: str = "regular",
    employment_type: str = "salaried",
) -> float:
    """
    Computes user's effective marginal tax rate including 4% cess.
    Tests an incremental ₹10,000 income to find (delta_tax / delta_income).
    """
    gross = float(salary_data.get("gross_salary", 0.0))
    if gross <= 0:
        return 0.0

    res1 = calculate_tax(
        financial_year=financial_year,
        regime=regime,
        salary_data=salary_data,
        deductions_data=deductions_data,
        age_bracket=age_bracket,
        employment_type=employment_type,
    )
    tax1 = float(res1["gross_tax_liability"])

    salary_bump = dict(salary_data)
    salary_bump["gross_salary"] = gross + 10000.0
    res2 = calculate_tax(
        financial_year=financial_year,
        regime=regime,
        salary_data=salary_bump,
        deductions_data=deductions_data,
        age_bracket=age_bracket,
        employment_type=employment_type,
    )
    tax2 = float(res2["gross_tax_liability"])

    marginal = (tax2 - tax1) / 10000.0
    return round(marginal, 4)


def analyze_missed_deductions(
    financial_year: str,
    selected_regime: str,
    salary_data: Dict[str, Any],
    deductions_data: Dict[str, Any],
    house_prop_data: Dict[str, Any],
    age_bracket: str = "regular",
    employment_type: str = "salaried",
    transactions: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Runs rule-driven advisor over the taxpayer's profile.
    Returns:
      opportunities: List[Dict[str, Any]],
      clarifying_questions: List[Dict[str, Any]],
      total_potential_savings: float,
      regime_notice: Optional[str]
    """
    provider = TaxRulesProvider.get_instance()
    rules = provider.get_rules_for_fy(financial_year)
    norm_regime = selected_regime.lower().strip()

    marginal_rate = get_user_marginal_rate(
        financial_year=financial_year,
        regime=norm_regime,
        salary_data=salary_data,
        deductions_data=deductions_data,
        age_bracket=age_bracket,
        employment_type=employment_type,
    )

    opportunities: List[Dict[str, Any]] = []
    questions: List[Dict[str, Any]] = []

    # 1. Section 80C Gap
    cap_80c = 150000.0
    epf = float(deductions_data.get("epf", 0.0))
    ppf = float(deductions_data.get("ppf", 0.0))
    elss = float(deductions_data.get("elss", 0.0))
    life_ins = float(deductions_data.get("life_insurance", 0.0))
    hl_princ = float(deductions_data.get("home_loan_principal", 0.0))
    tuition = float(deductions_data.get("tuition_fees", 0.0))

    claimed_80c = epf + ppf + elss + life_ins + hl_princ + tuition
    gap_80c = max(0.0, cap_80c - claimed_80c)

    if norm_regime == "new":
        regime_msg = "Chapter VI-A deductions (80C, 80D, etc.) are barred under the New Regime. Switch to Old Regime in comparison view to see if these deductions beat the New Regime."
    else:
        regime_msg = None

    if gap_80c > 0:
        savings = round(gap_80c * marginal_rate, 2)
        opportunities.append({
            "category": "Section 80C Investment Gap",
            "section": "80C",
            "statutory_limit": cap_80c,
            "claimed_amount": claimed_80c,
            "remaining_eligible": gap_80c,
            "estimated_tax_savings": savings if norm_regime == "old" else 0.0,
            "priority": "HIGH" if savings > 5000 else "MEDIUM",
            "conditions": "Invest in ELSS (3-yr lock-in), PPF, voluntary PF, or tax-saving 5-yr fixed deposit.",
            "required_documents": "Investment receipt, Mutual fund statement, or PPF passbook copy.",
            "regime_relevance": "Allowed in Old Regime only" if norm_regime == "new" else "Active Old Regime opportunity",
        })

    # 2. Section 80CCD(1B) - Additional NPS
    claimed_nps = float(deductions_data.get("80ccd_1b", 0.0))
    cap_nps = 50000.0
    gap_nps = max(0.0, cap_nps - claimed_nps)
    if gap_nps > 0:
        savings_nps = round(gap_nps * marginal_rate, 2)
        opportunities.append({
            "category": "National Pension System (NPS Tier-1)",
            "section": "80CCD(1B)",
            "statutory_limit": cap_nps,
            "claimed_amount": claimed_nps,
            "remaining_eligible": gap_nps,
            "estimated_tax_savings": savings_nps if norm_regime == "old" else 0.0,
            "priority": "HIGH",
            "conditions": "Exclusive deduction over and above the ₹1.5L Section 80C limit for Tier-1 NPS accounts.",
            "required_documents": "PRAN statement / transaction confirmation receipt from CRA (NSDL/KFintech).",
            "regime_relevance": "Allowed in Old Regime only",
        })

    # 3. Section 80CCD(2) - Employer NPS Contribution
    # Allowed in BOTH Old and New Regimes!
    basic = float(salary_data.get("basic_salary", 0.0))
    da = float(salary_data.get("da_amount", 0.0))
    salary_nps = basic + da
    cap_emp_nps = round(salary_nps * 0.14, 2)
    claimed_emp_nps = float(deductions_data.get("80ccd_2", 0.0))
    gap_emp_nps = max(0.0, cap_emp_nps - claimed_emp_nps)

    if salary_nps > 0 and gap_emp_nps > 0:
        savings_emp = round(gap_emp_nps * marginal_rate, 2)
        opportunities.append({
            "category": "Employer NPS Contribution (Both Regimes)",
            "section": "80CCD(2)",
            "statutory_limit": cap_emp_nps,
            "claimed_amount": claimed_emp_nps,
            "remaining_eligible": gap_emp_nps,
            "estimated_tax_savings": savings_emp,
            "priority": "HIGH",
            "conditions": "Up to 14% of Basic + DA contributed directly by your employer into your NPS account. Eligible in BOTH Old and New Regimes!",
            "required_documents": "Corporate salary restructure letter / Form 16 Part B / Employer CTC annexure.",
            "regime_relevance": "Valid in BOTH Old and New Regimes!",
        })

    # 4. Section 80D - Health Insurance & Preventive Health Checkup
    claimed_health_self = float(deductions_data.get("health_insurance_self", 0.0))
    claimed_health_parents = float(deductions_data.get("health_insurance_parents", 0.0))
    preventive = float(deductions_data.get("preventive_health_checkup", 0.0))

    if claimed_health_self == 0.0:
        questions.append({
            "question_id": "health_insurance_self_q",
            "field_target": "health_insurance_self",
            "title": "Do you pay health insurance premiums for yourself or your family?",
            "description": "Medical insurance paid by non-cash modes qualifies for up to ₹25,000 deduction (₹50,000 if senior).",
            "input_type": "currency",
            "default_value": 15000,
        })
    if claimed_health_parents == 0.0:
        questions.append({
            "question_id": "health_insurance_parents_q",
            "field_target": "health_insurance_parents",
            "title": "Do you pay medical insurance or medical expenses for your parents?",
            "description": "Additional ₹25,000 deduction (₹50,000 if parents are senior citizens aged 60+).",
            "input_type": "currency",
            "default_value": 25000,
        })

    if preventive < 5000.0:
        opportunities.append({
            "category": "Preventive Health Check-up Sublimit",
            "section": "80D",
            "statutory_limit": 5000.0,
            "claimed_amount": preventive,
            "remaining_eligible": 5000.0 - preventive,
            "estimated_tax_savings": round((5000.0 - preventive) * marginal_rate, 2) if norm_regime == "old" else 0.0,
            "priority": "MEDIUM",
            "conditions": "Routine blood tests, health screenings, or master health checkups (cash payments permitted).",
            "required_documents": "Diagnostic center / pathology laboratory bills.",
            "regime_relevance": "Allowed in Old Regime only",
        })

    # 5. HRA Check: Did user pay rent in bank transactions or profile but claimed ₹0 HRA?
    rent_paid = float(salary_data.get("rent_paid", 0.0))
    hra_rec = float(salary_data.get("hra_received", 0.0))
    if rent_paid > 0 and hra_rec == 0:
        questions.append({
            "question_id": "rent_paid_no_hra_q",
            "field_target": "hra_received",
            "title": "Rent payments detected, but no HRA component received from employer?",
            "description": "If your employer does not provide HRA, you may be eligible to claim deduction under Section 80GG (up to ₹60,000/year).",
            "input_type": "boolean",
            "default_value": False,
        })

    # Landlord PAN reminder if rent > ₹1,00,000/year
    if rent_paid > 100000.0:
        opportunities.append({
            "category": "Landlord PAN Compliance for HRA",
            "section": "10(13A) / CBDT Circular",
            "statutory_limit": rent_paid,
            "claimed_amount": rent_paid,
            "remaining_eligible": 0.0,
            "estimated_tax_savings": 0.0,
            "priority": "MEDIUM",
            "conditions": "Annual rent paid exceeds ₹1,00,000. Mandatory to collect and quote landlord's PAN on Form 12BB to avoid HRA claim disallowance by employer/ITD.",
            "required_documents": "Rent receipts + Landlord's PAN card copy / declaration Form 60.",
            "regime_relevance": "Mandatory compliance for rent > ₹1L",
        })

    # 6. Education Loan Interest (Section 80E)
    if "80e_interest" not in deductions_data:
        questions.append({
            "question_id": "education_loan_q",
            "field_target": "80e_interest",
            "title": "Do you pay interest on a higher education loan for yourself, spouse, or children?",
            "description": "Section 80E provides 100% tax deduction on education loan interest with NO upper limit for up to 8 consecutive years.",
            "input_type": "currency",
            "default_value": 0,
        })

    # Sort opportunities by estimated savings descending
    sorted_opps = sorted(opportunities, key=lambda x: x["estimated_tax_savings"], reverse=True)
    total_savings = sum(o["estimated_tax_savings"] for o in sorted_opps)

    return {
        "financial_year": financial_year,
        "selected_regime": norm_regime,
        "marginal_tax_rate_percent": round(marginal_rate * 100, 2),
        "total_potential_savings": round(total_savings, 2),
        "regime_notice": regime_msg,
        "opportunities": sorted_opps,
        "clarifying_questions": questions,
    }


def simulate_what_if_scenario(
    financial_year: str,
    regime: str,
    base_salary_data: Dict[str, Any],
    base_deductions_data: Dict[str, Any],
    additional_investments: Dict[str, float],
    age_bracket: str = "regular",
    employment_type: str = "salaried",
) -> Dict[str, Any]:
    """
    Live What-If Simulator:
    Recalculates baseline tax vs scenario tax given slider adjustments in 80C, NPS, or 80D.
    """
    # 1. Base calculation
    base_res = calculate_tax(
        financial_year=financial_year,
        regime=regime,
        salary_data=base_salary_data,
        deductions_data=base_deductions_data,
        age_bracket=age_bracket,
        employment_type=employment_type,
    )
    base_tax = float(base_res["gross_tax_liability"])

    # 2. Adjusted deductions
    adj_deductions = dict(base_deductions_data)
    for k, val in additional_investments.items():
        current_val = float(adj_deductions.get(k, 0.0))
        adj_deductions[k] = current_val + float(val)

    # 3. New calculation
    scenario_res = calculate_tax(
        financial_year=financial_year,
        regime=regime,
        salary_data=base_salary_data,
        deductions_data=adj_deductions,
        age_bracket=age_bracket,
        employment_type=employment_type,
    )
    scenario_tax = float(scenario_res["gross_tax_liability"])

    tax_reduction = max(0.0, base_tax - scenario_tax)

    return {
        "financial_year": financial_year,
        "regime": regime,
        "baseline_tax": base_tax,
        "simulated_tax": scenario_tax,
        "tax_savings": round(tax_reduction, 2),
        "additional_investments_made": additional_investments,
        "baseline_taxable_income": float(base_res["taxable_total_income"]),
        "simulated_taxable_income": float(scenario_res["taxable_total_income"]),
    }
