"""
User Schemas
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    full_name: str
    dob: Optional[str] = None
    age_bracket: str
    residential_status: str
    state: Optional[str] = None
    city: Optional[str] = None
    is_metro: bool
    employment_type: str
    pan_masked: Optional[str] = None
    is_active: bool
    created_at: datetime


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    dob: Optional[str] = None
    age_bracket: Optional[str] = None
    residential_status: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    is_metro: Optional[bool] = None
    employment_type: Optional[str] = None


class PanUpdateRequest(BaseModel):
    pan: str


class UserDataExport(BaseModel):
    user_profile: Dict[str, Any]
    profiles: List[Dict[str, Any]]
    documents: List[Dict[str, Any]]
    transactions: List[Dict[str, Any]]
    calculations: List[Dict[str, Any]]
    reports: List[Dict[str, Any]]
    exported_at: str
