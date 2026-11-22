"""
Transaction Pydantic Schemas
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: Optional[str] = None
    financial_year: str
    date: str
    description: str
    amount: float
    transaction_type: str
    category: str
    confidence: float
    classification_source: str
    is_potentially_tax_eligible: bool
    applicable_section: Optional[str] = None
    deduction_status: str
    proof_document_id: Optional[str] = None
    is_duplicate: bool
    parent_transaction_id: Optional[str] = None
    created_at: datetime


class TransactionUpdate(BaseModel):
    category: Optional[str] = None
    deduction_status: Optional[str] = None
    apply_to_similar: bool = False  # If true, applies this category to matching descriptions


class BulkCategoriseRequest(BaseModel):
    description_pattern: str
    new_category: str


class SplitItem(BaseModel):
    category: str
    amount: float
    description: Optional[str] = None


class TransactionSplitRequest(BaseModel):
    splits: List[SplitItem]


class CategoryTotalItem(BaseModel):
    category: str
    total_amount: float
    count: int
    tax_eligible_amount: float
    applicable_section: Optional[str] = None


class CategorySummaryResponse(BaseModel):
    financial_year: str
    total_expenses: float
    total_tax_deductible_expenses: float
    categories: List[CategoryTotalItem]
