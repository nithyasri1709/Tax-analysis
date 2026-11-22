"""
SQLAlchemy 2.0 ORM Models
Declarative schemas for Users, Documents, Extractions, Transactions, Tax Computations, Reports, and Audit Trails.
Strict UUID keys and user_id foreign keys for IDOR security.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    dob: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)  # YYYY-MM-DD
    age_bracket: Mapped[str] = mapped_column(String(32), default="regular")  # regular, senior_60_plus, super_senior_80_plus
    residential_status: Mapped[str] = mapped_column(String(32), default="resident")  # resident, nri, rnor
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_metro: Mapped[bool] = mapped_column(Boolean, default=False)
    employment_type: Mapped[str] = mapped_column(String(32), default="salaried")  # salaried, pensioner, self_employed
    encrypted_pan: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pan_masked: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    documents: Mapped[List["Document"]] = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    transactions: Mapped[List["Transaction"]] = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    profiles: Mapped[List["FinancialProfile"]] = relationship("FinancialProfile", back_populates="user", cascade="all, delete-orphan")
    calculations: Mapped[List["TaxCalculationRecord"]] = relationship("TaxCalculationRecord", back_populates="user", cascade="all, delete-orphan")
    reports: Mapped[List["ReportRecord"]] = relationship("ReportRecord", back_populates="user", cascade="all, delete-orphan")
    audit_logs: Mapped[List["AuditLog"]] = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")


class FinancialProfile(Base):
    __tablename__ = "financial_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    financial_year: Mapped[str] = mapped_column(String(16), default="2025-26", index=True)
    selected_regime: Mapped[str] = mapped_column(String(16), default="new")
    salary_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    house_prop_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    other_sources_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    capital_gains_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    exemptions_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    deductions_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    taxes_paid_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    completeness_score: Mapped[int] = mapped_column(Integer, default=20)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    user: Mapped["User"] = relationship("User", back_populates="profiles")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    financial_year: Mapped[str] = mapped_column(String(16), default="2025-26", index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(64), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    doc_type: Mapped[str] = mapped_column(String(64), default="other")
    status: Mapped[str] = mapped_column(String(32), default="uploaded")  # uploaded, processing, needs_review, confirmed, failed
    is_password_protected: Mapped[bool] = mapped_column(Boolean, default=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    user: Mapped["User"] = relationship("User", back_populates="documents")
    extracted_fields: Mapped[List["ExtractedField"]] = relationship("ExtractedField", back_populates="document", cascade="all, delete-orphan")


class ExtractedField(Base):
    __tablename__ = "extracted_fields"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    field_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    field_label: Mapped[str] = mapped_column(String(128), nullable=False)
    field_value: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    source_page: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source_snippet: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="auto")  # auto, user_edited, confirmed
    conflict_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    conflict_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    document: Mapped["Document"] = relationship("Document", back_populates="extracted_fields")


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    financial_year: Mapped[str] = mapped_column(String(16), default="2025-26", index=True)
    date: Mapped[str] = mapped_column(String(32), nullable=False)  # YYYY-MM-DD
    description: Mapped[str] = mapped_column(Text, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(16), default="debit")  # debit, credit
    category: Mapped[str] = mapped_column(String(64), default="Other Expenses", index=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.95)
    classification_source: Mapped[str] = mapped_column(String(16), default="rule")  # rule, ml, llm, user
    is_potentially_tax_eligible: Mapped[bool] = mapped_column(Boolean, default=False)
    applicable_section: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    deduction_status: Mapped[str] = mapped_column(String(32), default="needs_proof")  # claimed, needs_proof, ineligible, ignored
    proof_document_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False)
    parent_transaction_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    user: Mapped["User"] = relationship("User", back_populates="transactions")


class TaxCalculationRecord(Base):
    __tablename__ = "tax_calculations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    financial_year: Mapped[str] = mapped_column(String(16), default="2025-26", index=True)
    rule_config_version: Mapped[str] = mapped_column(String(64), default="1.0")
    inputs_snapshot: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    old_regime_result: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    new_regime_result: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    recommended_regime: Mapped[str] = mapped_column(String(16), default="new")
    tax_difference: Mapped[float] = mapped_column(Float, default=0.0)
    break_even_deductions: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    user: Mapped["User"] = relationship("User", back_populates="calculations")


class ReportRecord(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    financial_year: Mapped[str] = mapped_column(String(16), default="2025-26", index=True)
    calculation_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("tax_calculations.id", ondelete="SET NULL"), nullable=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    report_summary: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    user: Mapped["User"] = relationship("User", back_populates="reports")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    details: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    user: Mapped["User"] = relationship("User", back_populates="audit_logs")
