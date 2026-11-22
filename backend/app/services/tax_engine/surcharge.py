"""
Surcharge Module
Calculates surcharge rates, brackets, and marginal relief for high-income earners.
Follows Section 2 of Finance Act marginal relief provisos.
Pure Python, Decimal-accurate.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Callable, Dict, List, Tuple
from app.services.tax_engine.common import CalculationStep, to_decimal


def compute_surcharge_with_marginal_relief(
    taxable_income: Decimal,
    tax_after_rebate: Decimal,
    regime: str,
    rules: Dict[str, Any],
    slab_tax_calculator_fn: Callable[[Decimal], Decimal],
) -> Tuple[Decimal, Decimal, Decimal, List[CalculationStep]]:
    """
    Computes statutory surcharge with marginal relief.
    Statutory marginal relief rule:
    Total tax and surcharge on income exceeding threshold T shall not exceed:
      (Tax on T + applicable Surcharge on T) + (Income - T)
    Returns:
      nominal_surcharge: Decimal,
      marginal_relief: Decimal,
      net_surcharge: Decimal,
      steps: List[CalculationStep]
    """
    steps: List[CalculationStep] = []
    reg_rules = rules.get(f"{regime.lower()}_regime", {})
    brackets = reg_rules.get("surcharge_brackets", [])

    if not brackets or taxable_income <= Decimal("5000000.00") or tax_after_rebate <= Decimal("0.00"):
        steps.append(
            CalculationStep(
                step_id="surcharge_nil",
                label="Surcharge (Not Applicable)",
                section_ref="Finance Act",
                formula_text="0.00 (Taxable income <= ₹50 Lakhs)",
                inputs={"taxable_income": taxable_income},
                result=Decimal("0.00"),
                explanation="No surcharge applies as taxable income is ₹50 Lakhs or less.",
            )
        )
        return Decimal("0.00"), Decimal("0.00"), Decimal("0.00"), steps

    # Sort brackets by threshold ascending: e.g. 50L (10%), 1Cr (15%), 2Cr (25%), 5Cr (37%)
    asc_brackets = sorted(brackets, key=lambda b: to_decimal(b["threshold"]))

    # Find the applicable bracket index
    applied_idx = -1
    for idx, b in enumerate(asc_brackets):
        th = to_decimal(b["threshold"])
        if taxable_income > th:
            applied_idx = idx

    if applied_idx == -1:
        return Decimal("0.00"), Decimal("0.00"), Decimal("0.00"), steps

    applicable_bracket = asc_brackets[applied_idx]
    rate = to_decimal(applicable_bracket["rate"])
    threshold = to_decimal(applicable_bracket["threshold"])
    nominal_surcharge = (tax_after_rebate * rate).quantize(Decimal("0.01"))

    # Surcharge rate on the threshold itself (from preceding bracket if any)
    if applied_idx == 0:
        # At 50L threshold, surcharge on 50L is 0%
        prior_surcharge_rate = Decimal("0.00")
    else:
        prior_bracket = asc_brackets[applied_idx - 1]
        prior_surcharge_rate = to_decimal(prior_bracket["rate"])

    marginal_relief = Decimal("0.00")
    if applicable_bracket.get("marginal_relief", True):
        # Tax on threshold income:
        tax_on_threshold = slab_tax_calculator_fn(threshold)
        surcharge_on_threshold = (tax_on_threshold * prior_surcharge_rate).quantize(Decimal("0.01"))
        total_tax_at_threshold = tax_on_threshold + surcharge_on_threshold

        # Excess income over threshold:
        excess_income = taxable_income - threshold

        # Maximum permissible total tax + surcharge per Finance Act proviso:
        max_permissible_total = total_tax_at_threshold + excess_income

        # Proposed total tax + nominal surcharge:
        proposed_total = tax_after_rebate + nominal_surcharge

        if proposed_total > max_permissible_total:
            marginal_relief = proposed_total - max_permissible_total

    net_surcharge = max(Decimal("0.00"), nominal_surcharge - marginal_relief)

    steps.append(
        CalculationStep(
            step_id="surcharge_computation",
            label=f"Surcharge ({float(rate)*100:.0f}%) & Marginal Relief",
            section_ref="Finance Act / Section 2",
            formula_text="Tax * Rate - Marginal Relief",
            inputs={
                "taxable_income": taxable_income,
                "tax_after_rebate": tax_after_rebate,
                "threshold": threshold,
                "surcharge_rate": rate,
                "nominal_surcharge": nominal_surcharge,
                "marginal_relief": marginal_relief,
            },
            result=net_surcharge,
            explanation=(
                f"Surcharge at {float(rate)*100:.0f}% is ₹{nominal_surcharge:,.2f}. "
                + (f"Marginal relief of ₹{marginal_relief:,.2f} granted to limit combined tax and surcharge. " if marginal_relief > 0 else "")
                + f"Net surcharge payable: ₹{net_surcharge:,.2f}."
            ),
        )
    )

    return nominal_surcharge, marginal_relief, net_surcharge, steps
