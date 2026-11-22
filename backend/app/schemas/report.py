"""
Report Pydantic Schemas
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    financial_year: str
    calculation_id: Optional[str] = None
    file_name: str
    report_summary: Dict[str, Any]
    created_at: datetime


class ReportGenerateRequest(BaseModel):
    financial_year: str = "2025-26"
    calculation_id: Optional[str] = None


class ReportCompareResponse(BaseModel):
    report_1: Dict[str, Any]
    report_2: Dict[str, Any]
    tax_diff: float
    analysis: str
