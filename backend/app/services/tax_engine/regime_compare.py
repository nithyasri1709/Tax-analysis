"""
Regime Comparison Module
Computes side-by-side Old vs New regime calculations, exact rupee savings,
break-even deduction threshold, and explainable templated comparison summaries.
Pure Python, Decimal-accurate.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, Optional
from app.services.tax_engine.calculator import calculate_tax
from app.services.tax_engine.common import to_decimal, round_to_nearest_10


def calculate_break_even_deductions(
    financial_year: str,
    salary_data: Dict[str, Any],
    age_bracket: str = "regular",
    employment_type: str = "salaried",
    other_sources_data: Optional[Dict[str, Any]] = None,
    rules_provider: Any = None,
) -> Decimal:
    """
    Computes the exact 'Break-Even Deductions' threshold:
    The minimum amount of total deductions (Exemptions + Chapter VI-A)
    required under the Old Regime so that Old Regime tax is equal to or less than New Regime tax.
    Uses binary search / root finding against the pure Python tax calculator.
    """
    # 1. Calculate New Regime tax with zero deductions (except statutory standard deduction & 80CCD(2))
    new_res = calculate_tax(
        financial_year=financial_year,
        regime="new",
        salary_data=salary_data,
        age_bracket=age_bracket,
        employment_type=employment_type,
        other_sources_data=other_sources_data,
        rules_provider=rules_provider,
    )
    new_regime_tax = to_decimal(new_res["gross_tax_liability"])

    if new_regime_tax <= Decimal("0.00"):
        # Under New Regime, tax is already 0. Old regime cannot beat ₹0.
        return Decimal("0.00")

    # Binary search for break-even deduction in Old Regime
    low = Decimal("0.00")
    # Upper bound: Gross Salary + Other sources
    gross_salary = to_decimal(salary_data.get("gross_salary", 0))
    other_sources = to_decimal(other_sources_data.get("savings_interest", 0)) if other_sources_data else Decimal("0.00")
    high = gross_salary + other_sources

    break_even = high
    for _ in range(35):  # 35 iterations achieves precision under ₹1
        mid = (low + high) / Decimal("2.0")
        # Test old regime with deduction = mid
        test_deductions = {"80c": mid}
        old_test_res = calculate_tax(
            financial_year=financial_year,
            regime="old",
            salary_data=salary_data,
            deductions_data=test_deductions,
            age_bracket=age_bracket,
            employment_type=employment_type,
            other_sources_data=other_sources_data,
            rules_provider=rules_provider,
        )
        old_tax = to_decimal(old_test_res["gross_tax_liability"])
        if old_tax <= new_regime_tax:
            break_even = mid
            high = mid
        else:
            low = mid

    return round_to_nearest_10(break_even)


def compare_regimes(
    financial_year: str,
    salary_data: Optional[Dict[str, Any]] = None,
    house_prop_data: Optional[Dict[str, Any]] = None,
    other_sources_data: Optional[Dict[str, Any]] = None,
    capital_gains_data: Optional[Dict[str, Any]] = None,
    deductions_data: Optional[Dict[str, Any]] = None,
    taxes_paid_data: Optional[Dict[str, Any]] = None,
    age_bracket: str = "regular",
    employment_type: str = "salaried",
    is_metro: bool = False,
    rules_provider: Any = None,
) -> Dict[str, Any]:
    """
    Executes full comparison between Old and New Tax Regimes.
    """
    salary_data = salary_data or {}
    deductions_data = deductions_data or {}

    old_result = calculate_tax(
        financial_year=financial_year,
        regime="old",
        salary_data=salary_data,
        house_prop_data=house_prop_data,
        other_sources_data=other_sources_data,
        capital_gains_data=capital_gains_data,
        deductions_data=deductions_data,
        taxes_paid_data=taxes_paid_data,
        age_bracket=age_bracket,
        employment_type=employment_type,
        is_metro=is_metro,
        rules_provider=rules_provider,
    )

    new_result = calculate_tax(
        financial_year=financial_year,
        regime="new",
        salary_data=salary_data,
        house_prop_data=house_prop_data,
        other_sources_data=other_sources_data,
        capital_gains_data=capital_gains_data,
        deductions_data=deductions_data,
        taxes_paid_data=taxes_paid_data,
        age_bracket=age_bracket,
        employment_type=employment_type,
        is_metro=is_metro,
        rules_provider=rules_provider,
    )

    old_tax = to_decimal(old_result["gross_tax_liability"])
    new_tax = to_decimal(new_result["gross_tax_liability"])

    diff = abs(old_tax - new_tax)

    if new_tax < old_tax:
        recommended_regime = "new"
        savings = old_tax - new_tax
        explanation = (
            f"The New Tax Regime is more beneficial, saving you ₹{savings:,.2f} in tax. "
            f"Under the New Regime, your gross tax liability is ₹{new_tax:,.2f} compared to "
            f"₹{old_tax:,.2f} under the Old Regime, due to lower concessional slab rates "
            f"and a higher standard deduction of ₹{new_result['standard_deduction']:,.0f}."
        )
    elif old_tax < new_tax:
        recommended_regime = "old"
        savings = new_tax - old_tax
        explanation = (
            f"The Old Tax Regime is more beneficial, saving you ₹{savings:,.2f} in tax. "
            f"Your total claimed deductions and exemptions of ₹{old_result['total_chapter_vi_a_deductions'] + old_result['exemptions_total']:,.2f} "
            f"substantially reduce your taxable income under the Old Regime, yielding a tax liability of "
            f"₹{old_tax:,.2f} versus ₹{new_tax:,.2f} in the New Regime."
        )
    else:
        recommended_regime = "equal"
        savings = Decimal("0.00")
        explanation = (
            f"Both tax regimes yield an identical tax liability of ₹{new_tax:,.2f}. "
            "You may choose either regime based on compliance convenience."
        )

    # Compute break-even deduction point
    break_even = calculate_break_even_deductions(
        financial_year=financial_year,
        salary_data=salary_data,
        age_bracket=age_bracket,
        employment_type=employment_type,
        other_sources_data=other_sources_data,
        rules_provider=rules_provider,
    )

    comparison_table = [
        {"metric": "Gross Total Income", "old_regime": old_result["gross_total_income"], "new_regime": new_result["gross_total_income"]},
        {"metric": "Standard Deduction", "old_regime": old_result["standard_deduction"], "new_regime": new_result["standard_deduction"]},
        {"metric": "Exemptions (HRA / LTA)", "old_regime": old_result["exemptions_total"], "new_regime": new_result["exemptions_total"]},
        {"metric": "Chapter VI-A Deductions", "old_regime": old_result["total_chapter_vi_a_deductions"], "new_regime": new_result["total_chapter_vi_a_deductions"]},
        {"metric": "Taxable Total Income", "old_regime": old_result["taxable_total_income"], "new_regime": new_result["taxable_total_income"]},
        {"metric": "Slab Tax", "old_regime": old_result["slab_tax"], "new_regime": new_result["slab_tax"]},
        {"metric": "Section 87A Rebate", "old_regime": old_result["rebate_87a"], "new_regime": new_result["rebate_87a"]},
        {"metric": "Surcharge", "old_regime": old_result["net_surcharge"], "new_regime": new_result["net_surcharge"]},
        {"metric": "Health & Education Cess (4%)", "old_regime": old_result["health_and_education_cess"], "new_regime": new_result["health_and_education_cess"]},
        {"metric": "Gross Tax Liability", "old_regime": old_result["gross_tax_liability"], "new_regime": new_result["gross_tax_liability"]},
        {"metric": "Taxes Already Paid", "old_regime": old_result["total_taxes_paid"], "new_regime": new_result["total_taxes_paid"]},
        {"metric": "Balance Payable / (Refund)", "old_regime": old_result["balance_payable_or_refund"], "new_regime": new_result["balance_payable_or_refund"]},
    ]

    return {
        "financial_year": financial_year,
        "recommended_regime": recommended_regime,
        "tax_savings": float(savings),
        "break_even_deductions": float(break_even),
        "plain_language_explanation": explanation,
        "old_regime": old_result,
        "new_regime": new_result,
        "comparison_table": comparison_table,
        "disclaimer": "Estimate only; not professional tax advice.",
    }
