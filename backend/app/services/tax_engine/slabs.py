"""
Slabs Module
Computes income-tax liability slab-by-slab based on regime and age bracket.
Pure Python, Decimal-accurate.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Tuple
from app.services.tax_engine.common import CalculationStep, to_decimal


def compute_slab_tax(
    taxable_income: Decimal,
    regime: str,
    age_bracket: str,
    rules: Dict[str, Any],
) -> Tuple[Decimal, List[Dict[str, Any]], List[CalculationStep]]:
    """
    Computes tax on taxable income across statutory tax slabs.
    Returns:
      total_slab_tax: Decimal,
      slab_breakdown: List[Dict[str, Any]],
      steps: List[CalculationStep]
    """
    steps: List[CalculationStep] = []
    reg_rules = rules.get(f"{regime.lower()}_regime", {})
    slab_breakdown: List[Dict[str, Any]] = []

    if regime.lower() == "new":
        slabs = reg_rules.get("slabs", [])
    else:
        old_slabs_dict = reg_rules.get("slabs", {})
        if age_bracket == "super_senior_80_plus":
            slabs = old_slabs_dict.get("super_senior_80_plus", [])
        elif age_bracket == "senior_60_plus":
            slabs = old_slabs_dict.get("senior_60_plus", [])
        else:
            slabs = old_slabs_dict.get("regular", [])

    total_tax = Decimal("0.00")
    remaining_income = taxable_income

    for idx, slab in enumerate(slabs):
        slab_min = to_decimal(slab.get("min", 0))
        slab_max = to_decimal(slab.get("max")) if slab.get("max") is not None else None
        rate = to_decimal(slab.get("rate", 0))

        if taxable_income <= slab_min:
            taxed_in_slab = Decimal("0.00")
            tax_amount = Decimal("0.00")
        else:
            if slab_max is not None:
                taxable_in_this_bracket = min(taxable_income, slab_max) - slab_min
            else:
                taxable_in_this_bracket = taxable_income - slab_min

            taxed_in_slab = max(Decimal("0.00"), taxable_in_this_bracket)
            tax_amount = (taxed_in_slab * rate).quantize(Decimal("0.01"))

        total_tax += tax_amount

        slab_label = (
            f"₹{slab_min:,.0f} - ₹{slab_max:,.0f}" if slab_max is not None else f"Above ₹{slab_min:,.0f}"
        )
        slab_breakdown.append(
            {
                "slab_index": idx + 1,
                "range": slab_label,
                "rate_pct": float(rate * 100),
                "taxable_amount": float(taxed_in_slab),
                "tax_amount": float(tax_amount),
            }
        )

    steps.append(
        CalculationStep(
            step_id="slab_tax_computation",
            label=f"Income Tax by Slabs ({regime.capitalize()} Regime)",
            section_ref="Finance Act / Section 115BAC",
            formula_text="Sum(taxable_amount_in_slab * slab_rate)",
            inputs={
                "taxable_income": taxable_income,
                "regime": regime,
                "age_bracket": age_bracket,
                "slab_breakdown": slab_breakdown,
            },
            result=total_tax,
            explanation=(
                f"Taxable income of ₹{taxable_income:,.2f} computed across {len(slabs)} statutory slabs "
                f"totals ₹{total_tax:,.2f} before rebate and surcharge."
            ),
        )
    )

    return total_tax, slab_breakdown, steps
