"""
Intelligent Tax Assistant - FastAPI Application Entrypoint
Wires all domain routers, CORS policies, security headers, and database lifecycle.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.v1.admin import router as admin_router
from app.api.v1.auth import router as auth_router
from app.api.v1.chat import router as chat_router
from app.api.v1.deductions import router as deductions_router
from app.api.v1.documents import router as documents_router
from app.api.v1.extraction import router as extraction_router
from app.api.v1.investments import router as investments_router
from app.api.v1.profile import router as profile_router
from app.api.v1.reconciliation import router as reconciliation_router
from app.api.v1.reports import router as reports_router
from app.api.v1.tax import router as tax_router
from app.api.v1.transactions import router as transactions_router
from app.api.v1.users import router as users_router
from app.core.config import settings
from app.db.session import init_db
from app.services.tax_engine.rules_provider import TaxRulesProvider


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database tables and pre-cache statutory tax rules
    init_db()
    provider = TaxRulesProvider.get_instance()
    for fy in ["2024-25", "2025-26", "2026-27"]:
        try:
            provider.get_rules_for_fy(fy)
        except Exception:
            pass
    yield
    # Shutdown logic if needed


app = FastAPI(
    title="INTELLIGENT TAX ASSISTANT – Smart Tax Planning and Deduction Detection System",
    description="End-to-end explainable Indian Income Tax calculator, document extractor, and deduction detection assistant.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permits dev and production origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers under /api/v1
api_v1 = "/api/v1"
app.include_router(auth_router, prefix=api_v1)
app.include_router(users_router, prefix=api_v1)
app.include_router(documents_router, prefix=api_v1)
app.include_router(extraction_router, prefix=api_v1)
app.include_router(transactions_router, prefix=api_v1)
app.include_router(investments_router, prefix=api_v1)
app.include_router(tax_router, prefix=api_v1)
app.include_router(deductions_router, prefix=api_v1)
app.include_router(reports_router, prefix=api_v1)
app.include_router(reconciliation_router, prefix=api_v1)
app.include_router(profile_router, prefix=api_v1)
app.include_router(chat_router, prefix=api_v1)
app.include_router(admin_router, prefix=api_v1)


@app.get("/")
def root_endpoint():
    return {
        "app": "INTELLIGENT TAX ASSISTANT",
        "status": "online",
        "docs_url": "/docs",
        "openapi_url": "/openapi.json",
        "supported_financial_years": ["2024-25", "2025-26", "2026-27"],
        "disclaimer": "Estimate only; not professional tax advice.",
    }
