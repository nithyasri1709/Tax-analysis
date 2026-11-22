"""
Rebate Module
Section 87A Tax Rebate with exact Marginal Relief computation.
Pure Python, Decimal-accurate.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Tuple
from app.services.tax_engine.common import CalculationStep, to_decimal


def compute_section_87a_rebate(
    taxable_income: Decimal,
    slab_tax: Decimal,
    regime: str,
    rules: Dict[str, Any],
) -> Tuple[Decimal, Decimal, List[CalculationStep]]:
    """
    Computes Section 87A tax rebate and marginal relief.
    Returns:
      rebate_amount: Decimal,
      tax_after_rebate: Decimal,
      steps: List[CalculationStep]
    """
    steps: List[CalculationStep] = []
    reg_rules = rules.get(f"{regime.lower()}_regime", {})
    rebate_config = reg_rules.get("rebate_87a", {})

    threshold = to_decimal(rebate_config.get("threshold", 0))
    max_rebate = to_decimal(rebate_config.get("max_rebate", 0))
    has_marginal_relief = bool(rebate_config.get("marginal_relief", False))

    rebate_amount = Decimal("0.00")
    explanation = ""

    if taxable_income <= threshold:
        # Full or capped rebate
        rebate_amount = min(slab_tax, max_rebate)
        explanation = (
            f"Taxable income of ₹{taxable_income:,.2f} is within Section 87A threshold of ₹{threshold:,.2f}. "
            f"Rebate of ₹{rebate_amount:,.2f} applied, reducing tax to ₹0."
        )
    elif has_marginal_relief and taxable_income > threshold:
        # Check Marginal Relief under Section 87A proviso:
        # Tax payable cannot exceed the amount by which taxable income exceeds the threshold.
        excess_income = taxable_income - threshold
        if slab_tax > excess_income:
            # Marginal relief applies!
            rebate_amount = slab_tax - excess_income
            explanation = (
                f"Taxable income of ₹{taxable_income:,.2f} exceeds ₹{threshold:,.2f} by ₹{excess_income:,.2f}. "
                f"Under Section 87A marginal relief proviso, tax payable cannot exceed ₹{excess_income:,.2f}. "
                f"Marginal relief rebate of ₹{rebate_amount:,.2f} granted."
            )
        else:
            rebate_amount = Decimal("0.00")
            explanation = (
                f"Taxable income of ₹{taxable_income:,.2f} exceeds threshold ₹{threshold:,.2f}. "
                f"Normal slab tax (₹{slab_tax:,.2f}) is lower than excess income (₹{excess_income:,.2f}); "
                f"marginal relief does not apply."
            )
    else:
        rebate_amount = Decimal("0.00")
        explanation = f"Taxable income of ₹{taxable_income:,.2f} exceeds ₹{threshold:,.2f}; Section 87A rebate not applicable."

    tax_after_rebate = max(Decimal("0.00"), slab_tax - rebate_amount)

    steps.append(
        CalculationStep(
            step_id="rebate_87a_computation",
            label="Section 87A Tax Rebate & Marginal Relief",
            section_ref="Section 87A",
            formula_text="min(Slab Tax, Max Rebate) or Marginal Relief: max(0, Slab Tax - (Taxable Income - Threshold))",
            inputs={
                "taxable_income": taxable_income,
                "slab_tax": slab_tax,
                "threshold": threshold,
                "max_rebate": max_rebate,
                "has_marginal_relief": has_marginal_relief,
                "regime": regime,
            },
            result=rebate_amount,
            explanation=explanation,
        )
    )

    steps.append(
        CalculationStep(
            step_id="tax_after_rebate",
            label="Tax Payable after Section 87A Rebate",
            section_ref="Section 87A",
            formula_text="max(0, Slab Tax - Section 87A Rebate)",
            inputs={"slab_tax": slab_tax, "rebate_87a": rebate_amount},
            result=tax_after_rebate,
            explanation=f"Tax liability after Section 87A rebate: ₹{tax_after_rebate:,.2f}.",
        )
    )

    return rebate_amount, tax_after_rebate, steps
