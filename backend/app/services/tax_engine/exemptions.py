"""
Exemptions Module
Implements Section 10(13A) (House Rent Allowance Exemption) and related allowances.
Pure Python, Decimal-accurate.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Tuple
from app.services.tax_engine.common import CalculationStep, to_decimal


def compute_hra_exemption(
    basic_salary: Decimal,
    da_amount: Decimal,
    hra_received: Decimal,
    annual_rent_paid: Decimal,
    is_metro: bool,
    regime: str,
    rules: Dict[str, Any],
) -> Tuple[Decimal, List[CalculationStep]]:
    """
    Computes House Rent Allowance (HRA) exemption under Section 10(13A) (Old Regime only).
    Formula: Least of the following three:
      1. Actual HRA received
      2. Rent paid - 10% of (Basic Salary + DA)
      3. 50% of (Basic Salary + DA) if Metro, else 40%
    """
    steps: List[CalculationStep] = []

    if regime.lower() == "new":
        steps.append(
            CalculationStep(
                step_id="hra_new_regime",
                label="HRA Exemption in New Regime",
                section_ref="Section 115BAC / Section 85",
                formula_text="0.00 (Not allowed under New Tax Regime)",
                inputs={"regime": regime},
                result=Decimal("0.00"),
                explanation="House Rent Allowance exemption under Section 10(13A) is not allowable under the New Concessional Regime.",
            )
        )
        return Decimal("0.00"), steps

    salary_for_hra = basic_salary + da_amount
    hra_rules = rules.get("deductions", {}).get("hra", {})
    metro_pct = to_decimal(hra_rules.get("metro_percent", 0.50))
    non_metro_pct = to_decimal(hra_rules.get("non_metro_percent", 0.40))
    rent_excess_pct = to_decimal(hra_rules.get("rent_excess_percent", 0.10))

    applicable_pct = metro_pct if is_metro else non_metro_pct
    metro_label = "Metro (50%)" if is_metro else "Non-Metro (40%)"

    # Condition 1: Actual HRA received
    cond_1 = hra_received

    # Condition 2: Rent paid - 10% of salary
    ten_pct_salary = (salary_for_hra * rent_excess_pct).quantize(Decimal("0.01"))
    cond_2 = max(Decimal("0.00"), annual_rent_paid - ten_pct_salary)

    # Condition 3: 50% or 40% of salary
    cond_3 = (salary_for_hra * applicable_pct).quantize(Decimal("0.01"))

    # If no rent paid, exemption is 0
    if annual_rent_paid <= Decimal("0.00"):
        exempt_hra = Decimal("0.00")
    else:
        exempt_hra = min(cond_1, cond_2, cond_3)

    steps.append(
        CalculationStep(
            step_id="hra_calc_least_of_three",
            label="HRA Exemption (Least of Three)",
            section_ref="Section 10(13A) / Rule 2A",
            formula_text="min(Actual HRA, Rent Paid - 10% Salary, 50%/40% Salary)",
            inputs={
                "basic_salary": basic_salary,
                "da_amount": da_amount,
                "salary_for_hra": salary_for_hra,
                "hra_received": cond_1,
                "rent_paid": annual_rent_paid,
                "rent_minus_10pct": cond_2,
                "salary_percentage_limit": cond_3,
                "is_metro": is_metro,
                "metro_classification": metro_label,
            },
            result=exempt_hra,
            explanation=(
                f"HRA Exemption is the least of (1) Actual HRA: ₹{cond_1:,.2f}, "
                f"(2) Rent paid minus 10% salary: ₹{cond_2:,.2f}, and "
                f"(3) {metro_label} of salary: ₹{cond_3:,.2f}."
            ),
        )
    )

    return exempt_hra, steps
