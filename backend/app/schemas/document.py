"""
Document and Extraction Pydantic Schemas
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class ExtractedFieldOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: str
    field_key: str
    field_label: str
    field_value: str
    normalized_value: Optional[float] = None
    confidence: float
    source_page: Optional[int] = None
    source_snippet: Optional[str] = None
    status: str
    conflict_flag: bool
    conflict_details: Optional[Dict[str, Any]] = None
    created_at: datetime


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    financial_year: str
    file_name: str
    file_type: str
    file_size: int
    doc_type: str
    status: str
    is_password_protected: bool
    error_message: Optional[str] = None
    created_at: datetime
    extracted_fields: List[ExtractedFieldOut] = []


class FieldUpdateRequest(BaseModel):
    field_value: str
    normalized_value: Optional[float] = None


class ConflictResolveRequest(BaseModel):
    chosen_field_id: str
    custom_value: Optional[float] = None
