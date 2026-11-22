"""
Cess Module
Health and Education Cess (4%) on income tax and surcharge.
Section 288B rounding of total tax liability to the nearest ₹10.
Pure Python, Decimal-accurate.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Tuple
from app.services.tax_engine.common import CalculationStep, to_decimal, round_to_nearest_10


def compute_cess_and_total_liability(
    tax_after_rebate: Decimal,
    net_surcharge: Decimal,
    rules: Dict[str, Any],
) -> Tuple[Decimal, Decimal, Decimal, List[CalculationStep]]:
    """
    Computes 4% Health and Education Cess and rounds total tax liability
    to the nearest ₹10 per Section 288B.
    Returns:
      cess_amount: Decimal,
      gross_tax_liability_unrounded: Decimal,
      gross_tax_liability_rounded: Decimal,
      steps: List[CalculationStep]
    """
    steps: List[CalculationStep] = []
    cess_rate = to_decimal(rules.get("cess_rate", 0.04))

    tax_plus_surcharge = tax_after_rebate + net_surcharge
    cess_amount = (tax_plus_surcharge * cess_rate).quantize(Decimal("0.01"))

    gross_unrounded = tax_plus_surcharge + cess_amount
    gross_rounded = round_to_nearest_10(gross_unrounded)

    steps.append(
        CalculationStep(
            step_id="health_and_education_cess",
            label=f"Health and Education Cess ({float(cess_rate)*100:.0f}%)",
            section_ref="Finance Act",
            formula_text=f"{float(cess_rate)*100:.0f}% of (Tax after rebate + Surcharge)",
            inputs={
                "tax_after_rebate": tax_after_rebate,
                "net_surcharge": net_surcharge,
                "tax_plus_surcharge": tax_plus_surcharge,
                "cess_rate": cess_rate,
            },
            result=cess_amount,
            explanation=f"Health & Education cess of {float(cess_rate)*100:.0f}% on ₹{tax_plus_surcharge:,.2f} is ₹{cess_amount:,.2f}.",
        )
    )

    steps.append(
        CalculationStep(
            step_id="gross_tax_liability_rounded",
            label="Gross Tax Liability (Section 288B)",
            section_ref="Section 288B",
            formula_text="round_to_nearest_10(Tax + Surcharge + Cess)",
            inputs={
                "tax_after_rebate": tax_after_rebate,
                "net_surcharge": net_surcharge,
                "cess": cess_amount,
                "unrounded_liability": gross_unrounded,
            },
            result=gross_rounded,
            explanation=f"Gross tax liability of ₹{gross_unrounded:,.2f} rounded to nearest ₹10 is ₹{gross_rounded:,.2f}.",
        )
    )

    return cess_amount, gross_unrounded, gross_rounded, steps
