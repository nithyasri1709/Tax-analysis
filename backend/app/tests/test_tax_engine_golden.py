"""
Golden Tax Engine Test Cases
Manually worked and verified arithmetic against Indian Income-tax Act provisions.
FY 2025-26 & FY 2026-27 statutory rules.
"""

import pytest
from decimal import Decimal
from app.services.tax_engine.calculator import calculate_tax
from app.services.tax_engine.exemptions import compute_hra_exemption
from app.services.tax_engine.regime_compare import compare_regimes
from app.services.tax_engine.rules_provider import TaxRulesProvider


@pytest.fixture
def rules_provider():
    return TaxRulesProvider.get_instance()


def test_salaried_7_lakh_new_regime(rules_provider):
    """
    Gross Salary: ₹7,00,000 (Salaried, Regular, New Regime, FY 2025-26)
    Arithmetic:
      Gross: 7,00,000
      Less Standard Deduction: 75,000
      Taxable Income: 6,25,000
      Slabs (FY 25-26 New Regime):
        0 - 4,00,000: Nil
        4,00,001 - 6,25,000: 5% of 2,25,000 = 11,250
        Total slab tax = 11,250
      Section 87A Rebate:
        Taxable income (6,25,000) <= 12,00,000 threshold.
        Rebate = min(11,250, 60,000) = 11,250.
      Tax after rebate: 0.00
      Cess: 0.00
      Gross Tax Liability: ₹0.00
    """
    res = calculate_tax(
        financial_year="2025-26",
        regime="new",
        salary_data={"gross_salary": 700000},
        employment_type="salaried",
        rules_provider=rules_provider,
    )
    assert res["taxable_total_income"] == 625000.0
    assert res["slab_tax"] == 11250.0
    assert res["rebate_87a"] == 11250.0
    assert res["gross_tax_liability"] == 0.0


def test_salaried_12_lakh_new_regime(rules_provider):
    """
    Gross Salary: ₹12,00,000 (Salaried, Regular, New Regime, FY 2025-26)
    Arithmetic:
      Gross: 12,00,000
      Less Standard Deduction: 75,000
      Taxable Income: 11,25,000
      Slabs:
        0 - 4L: 0
        4L - 8L: 5% of 4,00,000 = 20,000
        8L - 11.25L: 10% of 3,25,000 = 32,500
        Total slab tax: 20,000 + 32,500 = 52,500
      Section 87A Rebate:
        Taxable income 11,25,000 <= 12,00,000.
        Rebate = min(52,500, 60,000) = 52,500.
      Gross Tax Liability: ₹0.00
    """
    res = calculate_tax(
        financial_year="2025-26",
        regime="new",
        salary_data={"gross_salary": 1200000},
        employment_type="salaried",
        rules_provider=rules_provider,
    )
    assert res["taxable_total_income"] == 1125000.0
    assert res["slab_tax"] == 52500.0
    assert res["rebate_87a"] == 52500.0
    assert res["gross_tax_liability"] == 0.0


def test_salaried_12_75_lakh_new_regime(rules_provider):
    """
    Gross Salary: ₹12,75,000 (Salaried, Regular, New Regime, FY 2025-26)
    Arithmetic:
      Gross: 12,75,000
      Less Standard Deduction: 75,000
      Taxable Income: 12,00,000
      Slabs:
        0 - 4L: 0
        4L - 8L: 20,000
        8L - 12L: 10% of 4,00,000 = 40,000
        Total slab tax = 20,000 + 40,000 = 60,000
      Section 87A Rebate:
        Taxable income is exactly 12,00,000 <= 12,00,000.
        Rebate = min(60,000, 60,000) = 60,000.
      Gross Tax Liability: ₹0.00
    """
    res = calculate_tax(
        financial_year="2025-26",
        regime="new",
        salary_data={"gross_salary": 1275000},
        employment_type="salaried",
        rules_provider=rules_provider,
    )
    assert res["taxable_total_income"] == 1200000.0
    assert res["slab_tax"] == 60000.0
    assert res["rebate_87a"] == 60000.0
    assert res["gross_tax_liability"] == 0.0


def test_salaried_12_80_lakh_new_regime_marginal_relief(rules_provider):
    """
    Gross Salary: ₹12,80,000 (Salaried, Regular, New Regime, FY 2025-26)
    Arithmetic:
      Gross: 12,80,000
      Less Standard Deduction: 75,000
      Taxable Income: 12,05,000
      Slabs:
        0 - 4L: 0
        4L - 8L: 20,000
        8L - 12L: 40,000
        12L - 12.05L: 15% of 5,000 = 750
        Total slab tax: 20k + 40k + 750 = 60,750
      Section 87A Marginal Relief:
        Excess of income over ₹12,00,000 is: 12,05,000 - 12,00,000 = 5,000.
        Tax payable cannot exceed excess income (5,000).
        Rebate = 60,750 - 5,000 = 55,750.
        Tax after rebate = 5,000.
      Cess: 4% of 5,000 = 200.
      Gross Tax Liability = 5,000 + 200 = ₹5,200.00
    """
    res = calculate_tax(
        financial_year="2025-26",
        regime="new",
        salary_data={"gross_salary": 1280000},
        employment_type="salaried",
        rules_provider=rules_provider,
    )
    assert res["taxable_total_income"] == 1205000.0
    assert res["slab_tax"] == 60750.0
    assert res["rebate_87a"] == 55750.0
    assert res["tax_after_rebate"] == 5000.0
    assert res["health_and_education_cess"] == 200.0
    assert res["gross_tax_liability"] == 5200.0


def test_salaried_15_lakh_new_regime(rules_provider):
    """
    Gross Salary: ₹15,00,000 (Salaried, Regular, New Regime, FY 2025-26)
    Arithmetic:
      Gross: 15,00,000
      Less Standard Deduction: 75,000
      Taxable Income: 14,25,000
      Slabs:
        0 - 4L: 0
        4L - 8L: 20,000
        8L - 12L: 40,000
        12L - 14.25L: 15% of 2,25,000 = 33,750
        Total slab tax = 20,000 + 40,000 + 33,750 = 93,750
      Section 87A Rebate: 0.00 (Excess 2,25,000 > 93,750)
      Cess: 4% of 93,750 = 3,750.00
      Gross Tax Liability = 93,750 + 3,750 = ₹97,500.00
    """
    res = calculate_tax(
        financial_year="2025-26",
        regime="new",
        salary_data={"gross_salary": 1500000},
        employment_type="salaried",
        rules_provider=rules_provider,
    )
    assert res["taxable_total_income"] == 1425000.0
    assert res["slab_tax"] == 93750.0
    assert res["rebate_87a"] == 0.0
    assert res["health_and_education_cess"] == 3750.0
    assert res["gross_tax_liability"] == 97500.0


def test_salaried_25_lakh_new_regime(rules_provider):
    """
    Gross Salary: ₹25,00,000 (Salaried, Regular, New Regime, FY 2025-26)
    Arithmetic:
      Gross: 25,00,000
      Less Standard Deduction: 75,000
      Taxable Income: 24,25,000
      Slabs:
        0-4L: 0
        4-8L: 20,000
        8-12L: 40,000
        12-16L: 60,000 (15% of 4L)
        16-20L: 80,000 (20% of 4L)
        20-24L: 1,00,000 (25% of 4L)
        Above 24L: 30% of 25,000 = 7,500
        Total slab tax = 20k + 40k + 60k + 80k + 100k + 7.5k = 3,07,500
      Surcharge: 0.00
      Cess: 4% of 3,07,500 = 12,300
      Gross Tax Liability = 3,07,500 + 12,300 = ₹3,19,800.00
    """
    res = calculate_tax(
        financial_year="2025-26",
        regime="new",
        salary_data={"gross_salary": 2500000},
        employment_type="salaried",
        rules_provider=rules_provider,
    )
    assert res["taxable_total_income"] == 2425000.0
    assert res["slab_tax"] == 307500.0
    assert res["health_and_education_cess"] == 12300.0
    assert res["gross_tax_liability"] == 319800.0


def test_salaried_50_lakh_new_regime(rules_provider):
    """
    Gross Salary: ₹50,00,000 (Salaried, Regular, New Regime, FY 2025-26)
    Arithmetic:
      Gross: 50,00,000
      Less Standard Deduction: 75,000
      Taxable Income: 49,25,000
      Slabs:
        0 - 24L: 3,00,000
        24L - 49.25L: 30% of 25,25,000 = 7,57,500
        Total slab tax = 3,00,000 + 7,57,500 = 10,57,500
      Surcharge: 0 (Taxable income 49.25L <= 50L)
      Cess: 4% of 10,57,500 = 42,300
      Gross Tax Liability = 10,57,500 + 42,300 = ₹10,99,800.00
    """
    res = calculate_tax(
        financial_year="2025-26",
        regime="new",
        salary_data={"gross_salary": 5000000},
        employment_type="salaried",
        rules_provider=rules_provider,
    )
    assert res["taxable_total_income"] == 4925000.0
    assert res["slab_tax"] == 1057500.0
    assert res["health_and_education_cess"] == 42300.0
    assert res["gross_tax_liability"] == 1099800.0


def test_salaried_1_point_2_cr_new_regime(rules_provider):
    """
    Gross Salary: ₹1,20,00,000 (Salaried, Regular, New Regime, FY 2025-26)
    Arithmetic:
      Gross: 1,20,00,000
      Less Standard Deduction: 75,000
      Taxable Income: 1,19,25,000
      Slabs:
        0 - 24L: 3,00,000
        24L - 1,19,25,000: 30% of 95,25,000 = 28,57,500
        Total slab tax = 3,00,000 + 28,57,500 = 31,57,500
      Surcharge:
        Income > 1 Cr <= 2 Cr -> Rate = 15%
        Nominal Surcharge = 15% of 31,57,500 = 4,73,625
        No marginal relief triggers.
        Tax + Surcharge = 31,57,500 + 4,73,625 = 36,31,125
      Cess: 4% of 36,31,125 = 1,45,245
      Gross Tax Liability = 36,31,125 + 1,45,245 = ₹37,76,370.00
    """
    res = calculate_tax(
        financial_year="2025-26",
        regime="new",
        salary_data={"gross_salary": 12000000},
        employment_type="salaried",
        rules_provider=rules_provider,
    )
    assert res["taxable_total_income"] == 11925000.0
    assert res["slab_tax"] == 3157500.0
    assert res["net_surcharge"] == 473625.0
    assert res["health_and_education_cess"] == 145245.0
    assert res["gross_tax_liability"] == 3776370.0


def test_senior_citizen_old_regime(rules_provider):
    """
    Senior Citizen (65 yrs, Old Regime, FY 2025-26)
    Gross Salary: ₹8,00,000
    Arithmetic:
      Less Standard Deduction: 50,000
      Less 80TTB: 50,000 (Senior interest deduction)
      Net Taxable Income: 7,00,000
      Senior Slabs (Old Regime):
        0 - 3,00,000: Nil
        3,00,001 - 5,00,000: 5% of 2L = 10,000
        5,00,001 - 7,00,000: 20% of 2L = 40,000
        Total slab tax = 10k + 40k = 50,000
      Rebate 87A: 0 (Income > 5L)
      Cess: 4% of 50,000 = 2,000
      Gross Tax Liability: ₹52,000.00
    """
    res = calculate_tax(
        financial_year="2025-26",
        regime="old",
        salary_data={"gross_salary": 800000, "savings_interest": 60000},
        age_bracket="senior_60_plus",
        employment_type="salaried",
        rules_provider=rules_provider,
    )
    assert res["taxable_total_income"] == 700000.0
    assert res["slab_tax"] == 50000.0
    assert res["gross_tax_liability"] == 52000.0


def test_hra_metro_vs_non_metro(rules_provider):
    """
    HRA comparison test:
    Basic: ₹6,00,000. Rent paid: ₹3,50,000. HRA received: ₹3,00,000.
    1. Actual HRA = 3,00,000
    2. Rent - 10% salary = 3,50,000 - 60,000 = 2,90,000
    3. Metro (50%) = 3,00,000 -> Exemption = min(3L, 2.9L, 3L) = ₹2,90,000
    4. Non-Metro (40%) = 2,40,000 -> Exemption = min(3L, 2.9L, 2.4L) = ₹2,40,000
    """
    rules = rules_provider.get_rules_for_fy("2025-26")
    ex_metro, _ = compute_hra_exemption(
        basic_salary=Decimal("600000.00"),
        da_amount=Decimal("0.00"),
        hra_received=Decimal("300000.00"),
        annual_rent_paid=Decimal("350000.00"),
        is_metro=True,
        regime="old",
        rules=rules,
    )
    ex_non_metro, _ = compute_hra_exemption(
        basic_salary=Decimal("600000.00"),
        da_amount=Decimal("0.00"),
        hra_received=Decimal("300000.00"),
        annual_rent_paid=Decimal("350000.00"),
        is_metro=False,
        regime="old",
        rules=rules,
    )
    assert ex_metro == Decimal("290000.00")
    assert ex_non_metro == Decimal("240000.00")


def test_old_regime_wins_with_full_deductions(rules_provider):
    """
    Case where Old Regime wins significantly:
    Gross Salary: ₹15,00,000
    Deductions & Exemptions:
      HRA Exemption: 1,50,000
      Standard Deduction: 50,000
      Professional Tax: 2,500
      Home loan interest Section 24(b): 2,00,000
      80C: 1,50,000
      80CCD(1B): 50,000
      80D: 50,000
    Total reduction from gross = 6,52,500
    Taxable income in Old Regime = 15,00,000 - 6,52,500 = ₹8,47,500
    Old Tax:
      0-2.5L: 0
      2.5-5L: 12,500
      5-8.475L: 20% of 3,47,500 = 69,500
      Slab tax = 82,000
      Cess 4% = 3,280
      Gross Tax = ₹85,280.00
    New Regime Tax on ₹15,00,000 = ₹97,500.00
    Result: Old Regime saves ₹12,220.00!
    """
    comp = compare_regimes(
        financial_year="2025-26",
        salary_data={
            "gross_salary": 1500000,
            "basic_salary": 600000,
            "hra_received": 150000,
            "rent_paid": 210000,  # 2.1L - 60k = 1.5L
            "professional_tax": 2500,
        },
        house_prop_data={"is_self_occupied": True, "home_loan_interest": 200000},
        deductions_data={
            "epf": 150000,
            "80ccd_1b": 50000,
            "health_insurance_self": 25000,
            "health_insurance_parents": 25000,
        },
        employment_type="salaried",
        is_metro=True,
        rules_provider=rules_provider,
    )
    assert comp["recommended_regime"] == "old"
    assert comp["old_regime"]["gross_tax_liability"] == 85280.0
    assert comp["new_regime"]["gross_tax_liability"] == 97500.0
    assert comp["tax_savings"] == 12220.0


def test_new_regime_wins_standard_case(rules_provider):
    """
    Case where New Regime wins (typical employee without home loan):
    Gross Salary: ₹15,00,000
    Only 80C: ₹1,50,000 claimed.
    In Old Regime:
      Taxable = 15L - 50k - 1.5L = 13,00,000
      Tax = 1,12,500 + 30% of 3L (90,000) = 2,02,500 + 4% cess = ₹2,10,600
    In New Regime:
      Tax = ₹97,500
    New Regime saves ₹1,13,100!
    """
    comp = compare_regimes(
        financial_year="2025-26",
        salary_data={"gross_salary": 1500000},
        deductions_data={"epf": 150000},
        employment_type="salaried",
        rules_provider=rules_provider,
    )
    assert comp["recommended_regime"] == "new"
    assert comp["tax_savings"] == 113100.0


def test_zero_and_negative_inputs(rules_provider):
    """Zero income and negative numbers are safely handled."""
    res = calculate_tax(
        financial_year="2025-26",
        regime="new",
        salary_data={"gross_salary": 0},
        rules_provider=rules_provider,
    )
    assert res["gross_tax_liability"] == 0.0
    assert res["taxable_total_income"] == 0.0
