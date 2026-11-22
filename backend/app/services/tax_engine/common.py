"""
Tax Engine Common Types and Mathematical Utilities
Strict Decimal arithmetic for financial and tax calculations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional


def to_decimal(val: Any) -> Decimal:
    """Converts int, float, str, or None to Decimal with 2 decimal places."""
    if val is None:
        return Decimal("0.00")
    if isinstance(val, Decimal):
        return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    try:
        return Decimal(str(val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except Exception:
        return Decimal("0.00")


def round_to_nearest_10(val: Decimal) -> Decimal:
    """
    Rounds a number to the nearest multiple of 10 as per
    Section 288A (Taxable Income) and Section 288B (Tax Liability)
    of the Income-tax Act.
    If the last digit is 5 or more, round up; otherwise round down.
    """
    integer_part = int(val.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    remainder = integer_part % 10
    if remainder >= 5:
        return Decimal(integer_part + (10 - remainder))
    else:
        return Decimal(integer_part - remainder)


@dataclass
class CalculationStep:
    step_id: str
    label: str
    section_ref: str
    formula_text: str
    inputs: Dict[str, Any]
    result: Decimal
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "label": self.label,
            "section_ref": self.section_ref,
            "formula_text": self.formula_text,
            "inputs": {k: float(v) if isinstance(v, Decimal) else v for k, v in self.inputs.items()},
            "result": float(self.result),
            "explanation": self.explanation,
        }
