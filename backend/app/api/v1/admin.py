"""
Admin and Operations API Router
Health endpoint, audit logs, and system dependency checks.
"""

import shutil
from typing import Any, Dict, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.core.config import settings
from app.db.models import AuditLog, User
from app.db.session import get_db
from app.services.tax_engine.rules_provider import TaxRulesProvider

router = APIRouter(tags=["Admin & System"])


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """System health check and diagnostic inspection."""
    provider = TaxRulesProvider.get_instance()
    available_fys = provider.get_available_financial_years()
    tesseract_installed = shutil.which("tesseract") is not None

    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "database": "connected",
        "supported_financial_years": available_fys,
        "ocr_engine_available": tesseract_installed,
        "storage_dir": settings.STORAGE_DIR,
        "llm_provider": settings.LLM_PROVIDER,
        "disclaimer": "Estimate only; not professional tax advice.",
    }


@router.get("/audit-logs")
def get_user_audit_logs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves security and calculation audit logs for current user."""
    logs = (
        db.query(AuditLog)
        .filter(AuditLog.user_id == current_user.id)
        .order_by(AuditLog.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id": l.id,
            "action": l.action,
            "details": l.details,
            "created_at": l.created_at.isoformat(),
        }
        for l in logs
    ]
