"""
Authentication Pydantic Schemas
"""

import re
from typing import Optional
from pydantic import BaseModel, Field, field_validator

EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2)
    dob: Optional[str] = None  # YYYY-MM-DD
    age_bracket: str = "regular"  # regular, senior_60_plus, super_senior_80_plus
    residential_status: str = "resident"  # resident, nri, rnor
    state: Optional[str] = None
    city: Optional[str] = None
    is_metro: bool = False
    employment_type: str = "salaried"  # salaried, pensioner, self_employed
    pan: Optional[str] = None

    @field_validator("email")
    def validate_email_format(cls, v: str) -> str:
        clean = v.strip().lower()
        if not EMAIL_REGEX.match(clean):
            raise ValueError("Invalid email format.")
        return clean


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    def validate_email_format(cls, v: str) -> str:
        clean = v.strip().lower()
        if not EMAIL_REGEX.match(clean):
            raise ValueError("Invalid email format.")
        return clean


class RefreshRequest(BaseModel):
    refresh_token: str


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict
