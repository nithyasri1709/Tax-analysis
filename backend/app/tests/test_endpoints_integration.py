"""
Integration tests for newly repaired endpoints:
- /api/v1/investments (summary & 80C meter breakdown)
- /api/v1/transactions/category-totals (aggregations and chart data)
- /api/v1/tax/compare (POST and GET regime comparison)
- /api/v1/deductions/missed & what-if (missed deduction advisor & simulations)
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.v1.auth import register_user
from app.api.v1.deductions import get_missed_deductions, live_what_if_simulation
from app.api.v1.investments import get_investment_analysis
from app.api.v1.tax import compare_tax_regimes, compare_tax_regimes_post
from app.api.v1.transactions import get_category_totals
from app.db.models import Base, FinancialProfile, Transaction, User
from app.schemas.auth import RegisterRequest
from app.schemas.deduction import WhatIfRequest
from app.schemas.tax import TaxCalculateRequest

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
Base.metadata.create_all(bind=test_engine)


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_user(db):
    user = db.query(User).filter(User.email == "test_endpoints@example.com").first()
    if not user:
        register_user(
            RegisterRequest(
                email="test_endpoints@example.com",
                password="Password123!",
                full_name="Endpoint Test User",
                pan="ABCDE1234F",
                employment_type="salaried",
                is_metro=True,
            ),
            db=db,
        )
        user = db.query(User).filter(User.email == "test_endpoints@example.com").first()

    # Seed or update profile
    profile = db.query(FinancialProfile).filter(
        FinancialProfile.user_id == user.id,
        FinancialProfile.financial_year == "2025-26",
    ).first()
    if not profile:
        profile = FinancialProfile(user_id=user.id, financial_year="2025-26")
        db.add(profile)

    profile.salary_data = {
        "basic_salary": 900000.0,
        "hra_received": 300000.0,
        "gross_salary": 1200000.0,
    }
    profile.deductions_data = {
        "epf": 50000.0,
        "ppf": 70000.0,
        "elss": 30000.0,
        "80ccd_1b": 25000.0,
        "80d_self": 20000.0,
        "80d_parents": 15000.0,
    }
    profile.house_prop_data = {"interest_self_occupied": 120000.0}
    db.commit()

    return user


def test_investment_analysis_returns_meter_and_breakdowns(db, test_user):
    """Verifies GET /investments returns meter80C, meterNPS, meter80D, meter24B and recommendations."""
    res = get_investment_analysis(financial_year="2025-26", regime="old", current_user=test_user, db=db)

    assert "section_80c_meter" in res
    meter = res["section_80c_meter"]
    assert meter["cap"] == 150000.0
    assert "components" in meter
    assert meter["components"]["epf"] == 50000.0
    assert meter["components"]["ppf"] == 70000.0
    assert meter["components"]["elss"] == 30000.0
    assert meter["total_claimed"] == 150000.0

    assert "section_80ccd_1b_nps" in res
    assert res["section_80ccd_1b_nps"]["invested"] == 25000.0

    assert "section_80d_health" in res
    assert res["section_80d_health"]["self_family"] == 20000.0

    assert "section_24b_home_loan_interest" in res
    assert res["section_24b_home_loan_interest"]["interest_paid"] == 120000.0

    assert "recommendations" in res
    assert isinstance(res["recommendations"], list)


def test_transaction_category_totals_returns_categories_list(db, test_user):
    """Verifies /transactions/category-totals returns structured payload with categories list."""
    # Seed transactions
    tx1 = Transaction(
        user_id=test_user.id,
        financial_year="2025-26",
        date="2025-05-10",
        description="Life Insurance Premium",
        amount=25000.0,
        transaction_type="debit",
        category="insurance_life",
        is_potentially_tax_eligible=True,
        applicable_section="80C",
        deduction_status="claimed",
    )
    tx2 = Transaction(
        user_id=test_user.id,
        financial_year="2025-26",
        date="2025-06-15",
        description="Pharmacy Bill",
        amount=5000.0,
        transaction_type="debit",
        category="medical_general",
        is_potentially_tax_eligible=False,
        applicable_section=None,
        deduction_status="ineligible",
    )
    db.add(tx1)
    db.add(tx2)
    db.commit()

    summary = get_category_totals(financial_year="2025-26", current_user=test_user, db=db)
    assert summary.financial_year == "2025-26"
    assert summary.total_expenses >= 30000.0
    assert summary.total_tax_deductible_expenses >= 25000.0
    assert len(summary.categories) >= 2


def test_tax_compare_post_and_get(db, test_user):
    """Verifies both POST and GET /tax/compare return enriched calculations and recommendations."""
    # GET comparison
    get_res = compare_tax_regimes(financial_year="2025-26", current_user=test_user, db=db)
    assert "recommended_regime" in get_res
    assert "tax_savings" in get_res
    assert "old_regime" in get_res
    assert "new_regime" in get_res
    assert "tax_diff" in get_res
    assert "break_even_deduction" in get_res
    assert "total_tax_liability" in get_res["old_regime"]
    assert "total_tax_liability" in get_res["new_regime"]

    # POST comparison
    calc_req = TaxCalculateRequest(
        financial_year="2025-26",
        salary_data={"gross_salary": 1500000.0, "basic_salary": 750000.0},
        deductions_data={"epf": 150000.0, "80ccd_1b": 50000.0},
    )
    post_res = compare_tax_regimes_post(payload=calc_req, current_user=test_user, db=db)
    assert post_res["recommended_regime"] in ["old", "new"]
    assert "tax_difference" in post_res
    assert post_res["old_regime"]["taxable_income"] > 0
    assert post_res["new_regime"]["taxable_income"] > 0


def test_missed_deductions_and_what_if_endpoints(db, test_user):
    """Verifies /deductions/missed and /deductions/what-if return correct fields expected by frontend."""
    missed = get_missed_deductions(financial_year="2025-26", regime="old", current_user=test_user, db=db)
    assert "missed_deductions" in missed
    assert "total_potential_tax_savings" in missed
    assert "clarifying_questions" in missed
    assert isinstance(missed["missed_deductions"], list)

    what_if_req = WhatIfRequest(
        financial_year="2025-26",
        target_regime="old",
        additional_80c=50000.0,
        additional_80ccd_1b=25000.0,
    )
    sim = live_what_if_simulation(payload=what_if_req, current_user=test_user, db=db)
    assert "tax_saved" in sim
    assert "baseline_tax" in sim
    assert "simulated_tax" in sim
    assert "baseline_deductions" in sim
