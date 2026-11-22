"""
Deductions Module
Chapter VI-A deductions engine with section caps, age-specific limits, and regime rules.
Pure Python, Decimal-accurate.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Tuple
from app.services.tax_engine.common import CalculationStep, to_decimal, round_to_nearest_10


def compute_chapter_vi_a_deductions(
    deductions_data: Dict[str, Any],
    salary_data: Dict[str, Any],
    age_bracket: str,
    regime: str,
    gross_total_income: Decimal,
    rules: Dict[str, Any],
) -> Tuple[Decimal, Decimal, Dict[str, Decimal], List[CalculationStep]]:
    """
    Computes eligible Chapter VI-A deductions.
    Returns:
      total_deductions_allowed: Decimal,
      taxable_income: Decimal (rounded to nearest ₹10 per Section 288A),
      breakdown_by_section: Dict[str, Decimal],
      steps: List[CalculationStep]
    """
    steps: List[CalculationStep] = []
    claimed_breakdown: Dict[str, Decimal] = {}
    ded_rules = rules.get("deductions", {})

    is_senior = age_bracket in ["senior_60_plus", "super_senior_80_plus"]
    is_new_regime = regime.lower() == "new"

    # 1. Section 80CCD(2) - Employer NPS Contribution
    # Allowed in BOTH Old and New Regimes!
    basic_salary = to_decimal(salary_data.get("basic_salary", 0))
    da_amount = to_decimal(salary_data.get("da_amount", 0))
    salary_for_nps = basic_salary + da_amount

    nps_employer_claimed = to_decimal(deductions_data.get("80ccd_2", 0))
    nps_rules = ded_rules.get("80CCD_2", {})
    employer_type = deductions_data.get("employer_type", "private").lower()
    if "govt" in employer_type:
        nps_cap_pct = to_decimal(nps_rules.get("govt_percentage_limit", 0.14))
    else:
        nps_cap_pct = to_decimal(nps_rules.get("private_percentage_limit", 0.14))

    nps_max_eligible = (salary_for_nps * nps_cap_pct).quantize(Decimal("0.01"))
    nps_employer_allowed = min(nps_employer_claimed, nps_max_eligible)
    claimed_breakdown["80CCD(2)"] = nps_employer_allowed

    steps.append(
        CalculationStep(
            step_id="deduction_80ccd_2",
            label="Section 80CCD(2) - Employer NPS Contribution",
            section_ref="Section 80CCD(2)",
            formula_text=f"min(Claimed, {float(nps_cap_pct)*100:.0f}% of Basic+DA)",
            inputs={
                "claimed": nps_employer_claimed,
                "basic_plus_da": salary_for_nps,
                "percentage_limit": nps_cap_pct,
                "eligible_cap": nps_max_eligible,
                "allowed_in_new_regime": True,
            },
            result=nps_employer_allowed,
            explanation=(
                f"Employer NPS contribution of ₹{nps_employer_claimed:,.2f} is allowed up to "
                f"{float(nps_cap_pct)*100:.0f}% of Basic+DA (₹{nps_max_eligible:,.2f}). "
                f"Allowed: ₹{nps_employer_allowed:,.2f}."
            ),
        )
    )

    if is_new_regime:
        # In New Regime, almost all other Chapter VI-A deductions are NOT allowed
        total_ded = min(gross_total_income, nps_employer_allowed)
        raw_taxable = max(Decimal("0.00"), gross_total_income - total_ded)
        rounded_taxable = round_to_nearest_10(raw_taxable)

        steps.append(
            CalculationStep(
                step_id="total_deductions_summary",
                label="Total Chapter VI-A Deductions (New Regime)",
                section_ref="Section 115BAC / Section 85",
                formula_text="Section 80CCD(2) Employer NPS Only",
                inputs={"gross_total_income": gross_total_income, "allowed_deductions": total_ded},
                result=total_ded,
                explanation="Under the New Concessional Regime, other Chapter VI-A deductions are barred by statute.",
            )
        )
        steps.append(
            CalculationStep(
                step_id="taxable_income_rounded",
                label="Taxable Total Income (Section 288A)",
                section_ref="Section 288A",
                formula_text="round_to_nearest_10(Gross Total Income - Deductions)",
                inputs={"gross_total_income": gross_total_income, "deductions": total_ded, "unrounded": raw_taxable},
                result=rounded_taxable,
                explanation=f"Taxable income rounded to nearest ₹10: ₹{rounded_taxable:,.2f}.",
            )
        )
        return total_ded, rounded_taxable, claimed_breakdown, steps

    # ---------------- OLD REGIME DEDUCTIONS ----------------

    # 2. Section 80C (Combined cap ₹1,50,000)
    rule_80c = ded_rules.get("80C", {})
    cap_80c = to_decimal(rule_80c.get("limit", 150000))

    epf = to_decimal(deductions_data.get("epf", 0))
    ppf = to_decimal(deductions_data.get("ppf", 0))
    elss = to_decimal(deductions_data.get("elss", 0))
    life_insurance = to_decimal(deductions_data.get("life_insurance", 0))
    hl_principal = to_decimal(deductions_data.get("home_loan_principal", 0))
    tuition = to_decimal(deductions_data.get("tuition_fees", 0))
    nsc = to_decimal(deductions_data.get("nsc", 0))
    fd_5yr = to_decimal(deductions_data.get("five_year_fd", 0))
    other_80c = to_decimal(deductions_data.get("other_80c", 0))

    raw_80c_total = epf + ppf + elss + life_insurance + hl_principal + tuition + nsc + fd_5yr + other_80c
    allowed_80c = min(raw_80c_total, cap_80c)
    claimed_breakdown["80C"] = allowed_80c

    steps.append(
        CalculationStep(
            step_id="deduction_80c",
            label="Section 80C - Specified Investments & Savings",
            section_ref="Section 80C",
            formula_text=f"min(Sum of 80C investments, ₹{cap_80c:,.0f})",
            inputs={
                "epf": epf,
                "ppf": ppf,
                "elss": elss,
                "life_insurance": life_insurance,
                "home_loan_principal": hl_principal,
                "tuition_fees": tuition,
                "nsc": nsc,
                "five_year_fd": fd_5yr,
                "total_invested": raw_80c_total,
                "statutory_cap": cap_80c,
            },
            result=allowed_80c,
            explanation=(
                f"Total Section 80C investments of ₹{raw_80c_total:,.2f} capped at "
                f"statutory limit of ₹{cap_80c:,.2f}. Allowed: ₹{allowed_80c:,.2f}."
            ),
        )
    )

    # 3. Section 80CCD(1B) - Additional Employee NPS (Cap ₹50,000)
    rule_80ccd_1b = ded_rules.get("80CCD_1B", {})
    cap_80ccd_1b = to_decimal(rule_80ccd_1b.get("limit", 50000))
    claimed_80ccd_1b = to_decimal(deductions_data.get("80ccd_1b", 0))
    allowed_80ccd_1b = min(claimed_80ccd_1b, cap_80ccd_1b)
    claimed_breakdown["80CCD(1B)"] = allowed_80ccd_1b

    steps.append(
        CalculationStep(
            step_id="deduction_80ccd_1b",
            label="Section 80CCD(1B) - Additional NPS Contribution",
            section_ref="Section 80CCD(1B)",
            formula_text=f"min(Claimed, ₹{cap_80ccd_1b:,.0f})",
            inputs={"claimed": claimed_80ccd_1b, "statutory_cap": cap_80ccd_1b},
            result=allowed_80ccd_1b,
            explanation=f"Additional voluntary NPS deduction capped at ₹{cap_80ccd_1b:,.2f}. Allowed: ₹{allowed_80ccd_1b:,.2f}.",
        )
    )

    # 4. Section 80D - Health Insurance & Preventive Health Check-up
    rule_80d = ded_rules.get("80D", {})
    self_cap = to_decimal(rule_80d.get("self_family_senior_limit" if is_senior else "self_family_regular_limit", 25000))

    parents_senior = bool(deductions_data.get("parents_senior", False))
    parents_cap = to_decimal(rule_80d.get("parents_senior_limit" if parents_senior else "parents_regular_limit", 25000))
    preventive_sublimit = to_decimal(rule_80d.get("preventive_checkup_sublimit", 5000))

    self_insurance = to_decimal(deductions_data.get("health_insurance_self", 0))
    parents_insurance = to_decimal(deductions_data.get("health_insurance_parents", 0))
    preventive_checkup = to_decimal(deductions_data.get("preventive_health_checkup", 0))

    allowed_preventive = min(preventive_checkup, preventive_sublimit)

    # Self bucket (insurance + preventive up to self_cap)
    self_bucket_raw = self_insurance + allowed_preventive
    self_bucket_allowed = min(self_bucket_raw, self_cap)

    # Parents bucket
    parents_bucket_allowed = min(parents_insurance, parents_cap)

    total_80d = self_bucket_allowed + parents_bucket_allowed
    claimed_breakdown["80D"] = total_80d

    steps.append(
        CalculationStep(
            step_id="deduction_80d",
            label="Section 80D - Health Insurance Premium",
            section_ref="Section 80D",
            formula_text="min(Self+Preventive, Self Cap) + min(Parents, Parents Cap)",
            inputs={
                "health_insurance_self": self_insurance,
                "preventive_checkup": preventive_checkup,
                "preventive_sublimit": preventive_sublimit,
                "self_cap": self_cap,
                "self_is_senior": is_senior,
                "health_insurance_parents": parents_insurance,
                "parents_cap": parents_cap,
                "parents_is_senior": parents_senior,
            },
            result=total_80d,
            explanation=(
                f"Self/family deduction: ₹{self_bucket_allowed:,.2f} (cap: ₹{self_cap:,.2f}); "
                f"Parents deduction: ₹{parents_bucket_allowed:,.2f} (cap: ₹{parents_cap:,.2f}). "
                f"Total Section 80D: ₹{total_80d:,.2f}."
            ),
        )
    )

    # 5. Section 80E - Higher Education Loan Interest
    claimed_80e = to_decimal(deductions_data.get("80e_interest", 0))
    allowed_80e = claimed_80e  # No statutory cap for 80E
    claimed_breakdown["80E"] = allowed_80e

    steps.append(
        CalculationStep(
            step_id="deduction_80e",
            label="Section 80E - Higher Education Loan Interest",
            section_ref="Section 80E",
            formula_text="Actual Interest Paid (No Statutory Cap, Max 8 Years)",
            inputs={"claimed": claimed_80e},
            result=allowed_80e,
            explanation=f"Full interest on higher education loan allowed: ₹{allowed_80e:,.2f}.",
        )
    )

    # 6. Section 80G - Donations
    claimed_80g = to_decimal(deductions_data.get("80g_donations", 0))
    claimed_breakdown["80G"] = claimed_80g
    steps.append(
        CalculationStep(
            step_id="deduction_80g",
            label="Section 80G - Donations to Charitable Funds",
            section_ref="Section 80G",
            formula_text="Eligible Donations",
            inputs={"claimed": claimed_80g},
            result=claimed_80g,
            explanation=f"Donations eligible under Section 80G: ₹{claimed_80g:,.2f}.",
        )
    )

    # 7. Section 80TTA / 80TTB - Savings / Deposit Interest
    interest_income = to_decimal(salary_data.get("savings_interest", 0))
    if is_senior:
        rule_ttb = ded_rules.get("80TTB", {})
        cap_ttb = to_decimal(rule_ttb.get("limit", 50000))
        allowed_ttb = min(interest_income, cap_ttb)
        claimed_breakdown["80TTB"] = allowed_ttb
        steps.append(
            CalculationStep(
                step_id="deduction_80ttb",
                label="Section 80TTB - Interest on Deposits (Senior Citizens)",
                section_ref="Section 80TTB",
                formula_text=f"min(Deposit Interest, ₹{cap_ttb:,.0f})",
                inputs={"interest_income": interest_income, "statutory_cap": cap_ttb},
                result=allowed_ttb,
                explanation=f"Senior citizen interest deduction under Section 80TTB: ₹{allowed_ttb:,.2f}.",
            )
        )
    else:
        rule_tta = ded_rules.get("80TTA", {})
        cap_tta = to_decimal(rule_tta.get("limit", 10000))
        allowed_tta = min(interest_income, cap_tta)
        claimed_breakdown["80TTA"] = allowed_tta
        steps.append(
            CalculationStep(
                step_id="deduction_80tta",
                label="Section 80TTA - Interest on Savings Account",
                section_ref="Section 80TTA",
                formula_text=f"min(Savings Interest, ₹{cap_tta:,.0f})",
                inputs={"savings_interest": interest_income, "statutory_cap": cap_tta},
                result=allowed_tta,
                explanation=f"Savings bank interest deduction under Section 80TTA: ₹{allowed_tta:,.2f}.",
            )
        )

    # Sum of all Chapter VI-A deductions
    raw_total_deductions = sum(claimed_breakdown.values(), Decimal("0.00"))

    # Statutory ceiling: Chapter VI-A deductions cannot exceed Gross Total Income (Section 80A(2))
    allowed_total_deductions = min(gross_total_income, raw_total_deductions)
    raw_taxable_income = max(Decimal("0.00"), gross_total_income - allowed_total_deductions)
    rounded_taxable_income = round_to_nearest_10(raw_taxable_income)

    steps.append(
        CalculationStep(
            step_id="chapter_vi_a_total",
            label="Total Chapter VI-A Deductions",
            section_ref="Chapter VI-A / Section 80A(2)",
            formula_text="min(Sum of Eligible Deductions, Gross Total Income)",
            inputs={
                "sum_of_deductions": raw_total_deductions,
                "gross_total_income": gross_total_income,
            },
            result=allowed_total_deductions,
            explanation=(
                f"Sum of Chapter VI-A deductions is ₹{raw_total_deductions:,.2f}, capped at "
                f"Gross Total Income of ₹{gross_total_income:,.2f} per Section 80A(2)."
            ),
        )
    )

    steps.append(
        CalculationStep(
            step_id="taxable_income_rounded",
            label="Taxable Total Income (Section 288A)",
            section_ref="Section 288A",
            formula_text="round_to_nearest_10(Gross Total Income - Deductions)",
            inputs={
                "gross_total_income": gross_total_income,
                "total_deductions": allowed_total_deductions,
                "unrounded_taxable_income": raw_taxable_income,
            },
            result=rounded_taxable_income,
            explanation=f"Taxable total income rounded to the nearest multiple of ₹10: ₹{rounded_taxable_income:,.2f}.",
        )
    )

    return allowed_total_deductions, rounded_taxable_income, claimed_breakdown, steps
