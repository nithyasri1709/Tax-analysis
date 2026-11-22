"""
Advance Tax and Interest Estimation Module (Sections 234A, 234B, 234C)
Computes installment schedule, shortfall, and estimated statutory interest.
Pure Python, Decimal-accurate.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Tuple
from app.services.tax_engine.common import CalculationStep, to_decimal, round_to_nearest_10


def compute_advance_tax_and_interest(
    gross_tax_liability: Decimal,
    taxes_paid_data: Dict[str, Any],
    rules: Dict[str, Any],
    months_delay_filing: int = 0,
) -> Tuple[Dict[str, Any], Decimal, List[CalculationStep]]:
    """
    Computes advance tax schedule, tax balance payable/refund, and estimated interest
    under Sections 234A, 234B, and 234C.
    Returns:
      taxes_summary: Dict[str, Any],
      balance_payable_or_refund: Decimal (positive = payable, negative = refund),
      steps: List[CalculationStep]
    """
    steps: List[CalculationStep] = []

    tds_salary = to_decimal(taxes_paid_data.get("tds_salary", 0))
    tds_other = to_decimal(taxes_paid_data.get("tds_other", 0))
    tcs = to_decimal(taxes_paid_data.get("tcs", 0))
    total_tds_tcs = tds_salary + tds_other + tcs

    adv_q1 = to_decimal(taxes_paid_data.get("advance_tax_q1", 0))
    adv_q2 = to_decimal(taxes_paid_data.get("advance_tax_q2", 0))
    adv_q3 = to_decimal(taxes_paid_data.get("advance_tax_q3", 0))
    adv_q4 = to_decimal(taxes_paid_data.get("advance_tax_q4", 0))
    total_advance_tax = adv_q1 + adv_q2 + adv_q3 + adv_q4

    self_assessment_tax = to_decimal(taxes_paid_data.get("self_assessment_tax", 0))
    total_prepaid_taxes = total_tds_tcs + total_advance_tax + self_assessment_tax

    # Assessed Tax for Advance Tax purposes (Section 209) = Gross Tax - TDS/TCS
    assessed_tax = max(Decimal("0.00"), gross_tax_liability - total_tds_tcs)

    # If assessed tax is under ₹10,000, Section 208 advance tax requirement does not trigger
    requires_advance_tax = assessed_tax >= Decimal("10000.00")

    interest_234c = Decimal("0.00")
    schedule_breakdown: List[Dict[str, Any]] = []

    if requires_advance_tax:
        # Schedule:
        # Q1 (15 June): 15% due (buffer threshold 12%)
        # Q2 (15 Sept): 45% due (buffer threshold 36%)
        # Q3 (15 Dec): 75% due (threshold 75%)
        # Q4 (15 Mar): 100% due (threshold 100%)
        cum_q1 = adv_q1
        cum_q2 = adv_q1 + adv_q2
        cum_q3 = adv_q1 + adv_q2 + adv_q3
        cum_q4 = total_advance_tax

        target_q1 = (assessed_tax * Decimal("0.15")).quantize(Decimal("1"))
        target_q2 = (assessed_tax * Decimal("0.45")).quantize(Decimal("1"))
        target_q3 = (assessed_tax * Decimal("0.75")).quantize(Decimal("1"))
        target_q4 = assessed_tax

        # Section 234C computation
        # Q1: if cumulative paid < 12% of assessed tax, 1% per month for 3 months
        shortfall_q1 = max(Decimal("0.00"), target_q1 - cum_q1)
        if cum_q1 < (assessed_tax * Decimal("0.12")):
            int_q1 = (shortfall_q1 * Decimal("0.01") * 3).quantize(Decimal("1"))
        else:
            int_q1 = Decimal("0.00")

        # Q2: if cumulative paid < 36% of assessed tax, 1% per month for 3 months
        shortfall_q2 = max(Decimal("0.00"), target_q2 - cum_q2)
        if cum_q2 < (assessed_tax * Decimal("0.36")):
            int_q2 = (shortfall_q2 * Decimal("0.01") * 3).quantize(Decimal("1"))
        else:
            int_q2 = Decimal("0.00")

        # Q3: if cumulative paid < 75% of assessed tax, 1% per month for 3 months
        shortfall_q3 = max(Decimal("0.00"), target_q3 - cum_q3)
        if cum_q3 < target_q3:
            int_q3 = (shortfall_q3 * Decimal("0.01") * 3).quantize(Decimal("1"))
        else:
            int_q3 = Decimal("0.00")

        # Q4: if cumulative paid < 100% of assessed tax, 1% per month for 1 month
        shortfall_q4 = max(Decimal("0.00"), target_q4 - cum_q4)
        if cum_q4 < target_q4:
            int_q4 = (shortfall_q4 * Decimal("0.01") * 1).quantize(Decimal("1"))
        else:
            int_q4 = Decimal("0.00")

        interest_234c = int_q1 + int_q2 + int_q3 + int_q4

        schedule_breakdown = [
            {"quarter": "Q1 (15 June)", "due_pct": 15, "target_amount": float(target_q1), "paid_cum": float(cum_q1), "shortfall": float(shortfall_q1), "interest_234c": float(int_q1)},
            {"quarter": "Q2 (15 Sept)", "due_pct": 45, "target_amount": float(target_q2), "paid_cum": float(cum_q2), "shortfall": float(shortfall_q2), "interest_234c": float(int_q2)},
            {"quarter": "Q3 (15 Dec)", "due_pct": 75, "target_amount": float(target_q3), "paid_cum": float(cum_q3), "shortfall": float(shortfall_q3), "interest_234c": float(int_q3)},
            {"quarter": "Q4 (15 Mar)", "due_pct": 100, "target_amount": float(target_q4), "paid_cum": float(cum_q4), "shortfall": float(shortfall_q4), "interest_234c": float(int_q4)},
        ]

    # Section 234B Interest:
    # 1% simple interest per month from 1st April of AY if advance tax paid is < 90% of assessed tax
    interest_234b = Decimal("0.00")
    if requires_advance_tax and total_advance_tax < (assessed_tax * Decimal("0.90")):
        shortfall_234b = assessed_tax - total_advance_tax
        # Default estimation: 1 month or specified months
        months_b = max(1, months_delay_filing)
        interest_234b = (shortfall_234b * Decimal("0.01") * months_b).quantize(Decimal("1"))

    # Section 234A Interest:
    # 1% simple interest per month on net unpaid tax for delay in filing return beyond due date
    net_tax_before_234a = gross_tax_liability - total_prepaid_taxes
    interest_234a = Decimal("0.00")
    if months_delay_filing > 0 and net_tax_before_234a > Decimal("0.00"):
        interest_234a = (net_tax_before_234a * Decimal("0.01") * months_delay_filing).quantize(Decimal("1"))

    total_statutory_interest = interest_234a + interest_234b + interest_234c
    final_tax_with_interest = gross_tax_liability + total_statutory_interest
    balance_payable_or_refund = round_to_nearest_10(final_tax_with_interest - total_prepaid_taxes)

    steps.append(
        CalculationStep(
            step_id="advance_tax_and_interest",
            label="Advance Tax & Statutory Interest Estimate (234A/B/C)",
            section_ref="Sections 208, 234A, 234B, 234C",
            formula_text="Interest 234A + 234B + 234C (Estimated)",
            inputs={
                "gross_tax_liability": gross_tax_liability,
                "assessed_tax": assessed_tax,
                "total_advance_tax_paid": total_advance_tax,
                "interest_234a": interest_234a,
                "interest_234b": interest_234b,
                "interest_234c": interest_234c,
                "total_interest": total_statutory_interest,
            },
            result=total_statutory_interest,
            explanation=(
                f"Assessed tax is ₹{assessed_tax:,.2f}. Estimated interest: 234A: ₹{interest_234a:,.2f}, "
                f"234B: ₹{interest_234b:,.2f}, 234C: ₹{interest_234c:,.2f}. "
                f"Total estimated statutory interest: ₹{total_statutory_interest:,.2f}."
            ),
        )
    )

    steps.append(
        CalculationStep(
            step_id="net_tax_payable_or_refund",
            label="Net Tax Payable / (Refund Due)",
            section_ref="Section 143 / Section 288B",
            formula_text="Gross Liability + Interest - Total Taxes Paid (TDS + TCS + Advance Tax + Self Assessment)",
            inputs={
                "gross_tax_liability": gross_tax_liability,
                "total_interest": total_statutory_interest,
                "total_prepaid_taxes": total_prepaid_taxes,
                "total_tds_tcs": total_tds_tcs,
                "total_advance_tax": total_advance_tax,
                "self_assessment_tax": self_assessment_tax,
            },
            result=balance_payable_or_refund,
            explanation=(
                f"Final liability including interest is ₹{final_tax_with_interest:,.2f}. "
                f"After crediting prepaid taxes of ₹{total_prepaid_taxes:,.2f}, "
                + (f"Net Balance Tax Payable is ₹{balance_payable_or_refund:,.2f}." if balance_payable_or_refund >= 0 else f"Net Tax Refund Due is ₹{abs(balance_payable_or_refund):,.2f}.")
            ),
        )
    )

    taxes_summary = {
        "gross_tax_liability": gross_tax_liability,
        "tds_salary": tds_salary,
        "tds_other": tds_other,
        "tcs": tcs,
        "total_tds_tcs": total_tds_tcs,
        "total_advance_tax": total_advance_tax,
        "self_assessment_tax": self_assessment_tax,
        "total_prepaid_taxes": total_prepaid_taxes,
        "interest_234a": interest_234a,
        "interest_234b": interest_234b,
        "interest_234c": interest_234c,
        "total_statutory_interest": total_statutory_interest,
        "balance_payable_or_refund": balance_payable_or_refund,
        "is_refund": balance_payable_or_refund < 0,
        "advance_tax_schedule": schedule_breakdown,
    }

    return taxes_summary, balance_payable_or_refund, steps
