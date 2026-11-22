"""
Tax Calculation and Regime Comparison Schemas
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class TaxCalculateRequest(BaseModel):
    financial_year: str = "2025-26"
    regime: str = "new"
    salary_data: Optional[Dict[str, Any]] = None
    house_prop_data: Optional[Dict[str, Any]] = None
    other_sources_data: Optional[Dict[str, Any]] = None
    capital_gains_data: Optional[Dict[str, Any]] = None
    deductions_data: Optional[Dict[str, Any]] = None
    taxes_paid_data: Optional[Dict[str, Any]] = None
    age_bracket: Optional[str] = "regular"
    employment_type: Optional[str] = "salaried"
    is_metro: Optional[bool] = False
    months_delay_filing: int = 0


class HraCalcRequest(BaseModel):
    basic_salary: float
    da_amount: float = 0.0
    hra_received: float
    annual_rent_paid: float
    is_metro: bool = False
    regime: str = "old"
    financial_year: str = "2025-26"
