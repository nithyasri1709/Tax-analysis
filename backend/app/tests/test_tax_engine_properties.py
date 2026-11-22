"""
Property-based and Invariant Tests
Verifies fundamental mathematical invariants across hundreds of pseudo-random scenarios:
1. Non-negativity: Tax liability, taxable income, and cess are >= 0.
2. Rebate cap: Section 87A rebate never exceeds the computed slab tax.
3. Cess exactness: Cess is exactly 4% of (Tax after rebate + Surcharge).
4. Monotonicity: Holding other deductions constant, a higher gross income never yields lower tax.
5. Rounding: Taxable income and Gross Tax Liability are rounded to nearest ₹10 per Sections 288A & 288B.
"""

import random
from decimal import Decimal
from app.services.tax_engine.calculator import calculate_tax
from app.services.tax_engine.rules_provider import TaxRulesProvider

provider = TaxRulesProvider.get_instance()


def test_tax_never_negative_randomized():
    """Property 1: Tax liability, taxable income, and cess must never be negative."""
    random.seed(42)
    fys = ["2024-25", "2025-26", "2026-27"]
    regimes = ["old", "new"]

    for _ in range(100):
        salary = random.randint(0, 30_000_000)  # up to ₹3 Crore
        fy = random.choice(fys)
        regime = random.choice(regimes)

        res = calculate_tax(
            financial_year=fy,
            regime=regime,
            salary_data={"gross_salary": salary},
            rules_provider=provider,
        )
        assert res["gross_tax_liability"] >= 0.0
        assert res["taxable_total_income"] >= 0.0
        assert res["rebate_87a"] >= 0.0
        assert res["health_and_education_cess"] >= 0.0


def test_rebate_never_exceeds_slab_tax_randomized():
    """Property 2: Section 87A rebate must never exceed computed slab tax."""
    random.seed(1337)
    for _ in range(100):
        salary = random.randint(0, 15_000_000)
        regime = random.choice(["old", "new"])
        res = calculate_tax(
            financial_year="2025-26",
            regime=regime,
            salary_data={"gross_salary": salary},
            rules_provider=provider,
        )
        assert res["rebate_87a"] <= res["slab_tax"] + 0.001
        assert res["tax_after_rebate"] >= 0.0


def test_cess_is_four_percent_randomized():
    """Property 3: Health & Education Cess is exactly 4% of (Tax after rebate + Surcharge)."""
    random.seed(999)
    for _ in range(100):
        salary = random.randint(100_000, 30_000_000)
        regime = random.choice(["old", "new"])
        res = calculate_tax(
            financial_year="2025-26",
            regime=regime,
            salary_data={"gross_salary": salary},
            rules_provider=provider,
        )
        base = Decimal(str(res["tax_after_rebate"])) + Decimal(str(res["net_surcharge"]))
        expected_cess = (base * Decimal("0.04")).quantize(Decimal("0.01"))
        actual_cess = Decimal(str(res["health_and_education_cess"])).quantize(Decimal("0.01"))
        assert actual_cess == expected_cess


def test_tax_monotonicity_new_regime_randomized():
    """
    Property 4: Monotonicity
    A higher gross salary must never lead to a lower gross tax liability in the New Regime
    (including through the marginal relief transition zone around ₹12 Lakhs).
    """
    random.seed(2026)
    for _ in range(100):
        salary_1 = random.randint(0, 25_000_000)
        increment = random.randint(1_000, 500_000)
        salary_2 = salary_1 + increment

        res1 = calculate_tax(
            financial_year="2025-26",
            regime="new",
            salary_data={"gross_salary": salary_1},
            rules_provider=provider,
        )
        res2 = calculate_tax(
            financial_year="2025-26",
            regime="new",
            salary_data={"gross_salary": salary_2},
            rules_provider=provider,
        )
        assert res2["gross_tax_liability"] >= res1["gross_tax_liability"], (
            f"Monotonicity failed: Tax on ₹{salary_2:,} (₹{res2['gross_tax_liability']:,}) "
            f"< Tax on ₹{salary_1:,} (₹{res1['gross_tax_liability']:,})"
        )


def test_section_288a_and_288b_rounding():
    """Property 5: Taxable total income and gross tax liability must be multiples of 10."""
    random.seed(777)
    for _ in range(50):
        salary = random.randint(100_000, 20_000_000)
        res = calculate_tax(
            financial_year="2025-26",
            regime="new",
            salary_data={"gross_salary": salary},
            rules_provider=provider,
        )
        taxable = int(res["taxable_total_income"])
        liability = int(res["gross_tax_liability"])
        assert taxable % 10 == 0, f"Taxable income {taxable} is not rounded to nearest 10"
        assert liability % 10 == 0, f"Gross tax liability {liability} is not rounded to nearest 10"
