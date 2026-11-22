"""
Deductions and What-If Schemas
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class QuestionAnswerRequest(BaseModel):
    financial_year: str = "2025-26"
    question_id: str
    field_target: str
    answer_value: Any


class WhatIfRequest(BaseModel):
    financial_year: str = "2025-26"
    regime: str = "old"
    additional_80c: float = 0.0
    additional_nps_tier1: float = 0.0
    additional_80d_health: float = 0.0
    additional_employer_nps: float = 0.0
