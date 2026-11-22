"""
Income Module
Computes income under various heads of income and derives Gross Total Income (GTI).
Pure Python, Decimal-accurate.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Tuple
from app.services.tax_engine.common import CalculationStep, to_decimal


def compute_heads_of_income(
    salary_data: Dict[str, Any],
    house_prop_data: Dict[str, Any],
    other_sources_data: Dict[str, Any],
    capital_gains_data: Dict[str, Any],
    employment_type: str,
    regime: str,
    rules: Dict[str, Any],
    exemptions_total: Decimal = Decimal("0.00"),
) -> Tuple[Dict[str, Decimal], List[CalculationStep]]:
    """
    Computes income under each head:
    1. Salary (Gross - Exemptions - Standard Deduction - Professional Tax)
    2. House Property (Self-occupied interest cap ₹2L, let-out NAV - 30% - interest, loss setoff cap)
    3. Other Sources (Savings, FDs, Dividend, etc.)
    4. Capital Gains (STCG, LTCG)
    Returns:
      dictionary of heads and Gross Total Income (GTI),
      list of CalculationStep audit objects.
    """
    steps: List[CalculationStep] = []
    reg_rules = rules.get(f"{regime.lower()}_regime", {})

    # ---------------- 1. SALARY HEAD ----------------
    gross_salary = to_decimal(salary_data.get("gross_salary", 0))
    prof_tax_raw = to_decimal(salary_data.get("professional_tax", 0))

    # Standard Deduction from config
    std_ded_config = reg_rules.get("standard_deduction", {})
    allowed_std_ded_limit = to_decimal(std_ded_config.get(employment_type.lower(), 0))
    # Standard deduction cannot exceed gross salary after exemptions
    salary_after_exemp = max(Decimal("0.00"), gross_salary - exemptions_total)
    actual_std_ded = min(salary_after_exemp, allowed_std_ded_limit)

    # Professional tax is only deductible in Old Regime under Section 16(iii)
    if regime.lower() == "old":
        prof_tax = min(prof_tax_raw, Decimal("2500.00"))
    else:
        prof_tax = Decimal("0.00")

    net_salary = max(Decimal("0.00"), salary_after_exemp - actual_std_ded - prof_tax)

    steps.append(
        CalculationStep(
            step_id="income_salary",
            label="Income from Salary",
            section_ref="Section 15-17",
            formula_text="Gross Salary - Exemptions - Standard Deduction - Professional Tax",
            inputs={
                "gross_salary": gross_salary,
                "exemptions": exemptions_total,
                "standard_deduction": actual_std_ded,
                "standard_deduction_limit": allowed_std_ded_limit,
                "professional_tax": prof_tax,
                "regime": regime,
                "employment_type": employment_type,
            },
            result=net_salary,
            explanation=(
                f"Gross salary ₹{gross_salary:,.2f} minus exemptions ₹{exemptions_total:,.2f}, "
                f"standard deduction ₹{actual_std_ded:,.2f}, and professional tax ₹{prof_tax:,.2f} "
                f"results in Net Salary of ₹{net_salary:,.2f}."
            ),
        )
    )

    # ---------------- 2. HOUSE PROPERTY HEAD ----------------
    is_self_occupied = bool(house_prop_data.get("is_self_occupied", True))
    rent_received = to_decimal(house_prop_data.get("rent_received", 0))
    municipal_taxes = to_decimal(house_prop_data.get("municipal_taxes", 0))
    home_loan_interest = to_decimal(house_prop_data.get("home_loan_interest", 0))

    loss_setoff_cap = to_decimal(reg_rules.get("house_property_loss_setoff_cap", 200000))
    hp_rules = rules.get("deductions", {}).get("24_b", {})
    self_occ_interest_cap = to_decimal(hp_rules.get("self_occupied_interest_limit", 200000))

    if regime.lower() == "new":
        # Under New Regime:
        # Deduction under section 24(b) for self-occupied property is Nil (0).
        # Loss from house property cannot be set off against other heads.
        if is_self_occupied:
            net_hp = Decimal("0.00")
            hp_explanation = "Under New Regime, Section 24(b) interest for self-occupied property is not allowed."
        else:
            # Let-out in new regime: NAV - 30% deduction - actual interest
            nav = max(Decimal("0.00"), rent_received - municipal_taxes)
            std_30 = (nav * Decimal("0.30")).quantize(Decimal("0.01"))
            computed_income = nav - std_30 - home_loan_interest
            # Any loss cannot be set off against other heads in new regime
            net_hp = max(Decimal("0.00"), computed_income)
            hp_explanation = f"Let-out property income in New Regime: NAV ₹{nav:,.2f} minus 30% deduction ₹{std_30:,.2f} and interest ₹{home_loan_interest:,.2f}. Loss set-off is restricted."
    else:
        # Old Regime
        if is_self_occupied:
            allowed_interest = min(home_loan_interest, self_occ_interest_cap)
            net_hp = -allowed_interest
            hp_explanation = f"Self-occupied property interest under Section 24(b) capped at ₹{self_occ_interest_cap:,.2f}. Loss: -₹{allowed_interest:,.2f}."
        else:
            nav = max(Decimal("0.00"), rent_received - municipal_taxes)
            std_30 = (nav * Decimal("0.30")).quantize(Decimal("0.01"))
            computed_hp = nav - std_30 - home_loan_interest
            if computed_hp < Decimal("0.00"):
                # Loss set-off against other heads capped at ₹2,00,000 per section 71(3A)
                net_hp = max(-loss_setoff_cap, computed_hp)
                hp_explanation = f"Let-out house property loss of ₹{abs(computed_hp):,.2f} capped at set-off limit of ₹{loss_setoff_cap:,.2f}."
            else:
                net_hp = computed_hp
                hp_explanation = f"Let-out property income: NAV ₹{nav:,.2f} - 30% std deduction ₹{std_30:,.2f} - interest ₹{home_loan_interest:,.2f} = ₹{net_hp:,.2f}."

    steps.append(
        CalculationStep(
            step_id="income_house_property",
            label="Income / (Loss) from House Property",
            section_ref="Section 24 / Section 71(3A)",
            formula_text="NAV - 30% Std Deduction - Section 24(b) Interest (Capped)",
            inputs={
                "is_self_occupied": is_self_occupied,
                "rent_received": rent_received,
                "municipal_taxes": municipal_taxes,
                "home_loan_interest": home_loan_interest,
                "loss_setoff_cap": loss_setoff_cap,
                "regime": regime,
            },
            result=net_hp,
            explanation=hp_explanation,
        )
    )

    # ---------------- 3. OTHER SOURCES HEAD ----------------
    savings_interest = to_decimal(other_sources_data.get("savings_interest", 0))
    fd_interest = to_decimal(other_sources_data.get("fd_interest", 0))
    dividend_income = to_decimal(other_sources_data.get("dividend_income", 0))
    other_income = to_decimal(other_sources_data.get("other_income", 0))

    net_other = savings_interest + fd_interest + dividend_income + other_income

    steps.append(
        CalculationStep(
            step_id="income_other_sources",
            label="Income from Other Sources",
            section_ref="Section 56",
            formula_text="Savings Interest + FD/Term Interest + Dividend + Other",
            inputs={
                "savings_interest": savings_interest,
                "fd_interest": fd_interest,
                "dividend_income": dividend_income,
                "other_income": other_income,
            },
            result=net_other,
            explanation=f"Sum of interest, dividends, and other taxable receipts: ₹{net_other:,.2f}.",
        )
    )

    # ---------------- 4. CAPITAL GAINS HEAD ----------------
    stcg_equity = to_decimal(capital_gains_data.get("stcg_equity", 0))
    ltcg_equity = to_decimal(capital_gains_data.get("ltcg_equity", 0))
    other_cg = to_decimal(capital_gains_data.get("other_capital_gains", 0))

    # Basic equity LTCG exemption (e.g. ₹1,25,000 per Finance Act 2024, or ₹1,00,000 previously)
    ltcg_exemption_limit = to_decimal(capital_gains_data.get("ltcg_exemption_limit", 125000))
    taxable_ltcg = max(Decimal("0.00"), ltcg_equity - ltcg_exemption_limit)
    net_cg = stcg_equity + taxable_ltcg + other_cg

    steps.append(
        CalculationStep(
            step_id="income_capital_gains",
            label="Income from Capital Gains",
            section_ref="Section 45 / 111A / 112A",
            formula_text="STCG + max(0, LTCG - Exemption) + Other CG",
            inputs={
                "stcg_equity": stcg_equity,
                "ltcg_equity": ltcg_equity,
                "ltcg_exemption_limit": ltcg_exemption_limit,
                "taxable_ltcg": taxable_ltcg,
                "other_cg": other_cg,
            },
            result=net_cg,
            explanation=(
                f"STCG ₹{stcg_equity:,.2f} plus taxable LTCG ₹{taxable_ltcg:,.2f} "
                f"(after ₹{ltcg_exemption_limit:,.2f} exemption) plus other CG ₹{other_cg:,.2f}."
            ),
        )
    )

    # ---------------- 5. GROSS TOTAL INCOME ----------------
    # Sum of all heads, ensuring total does not fall below zero
    raw_gti = net_salary + net_hp + net_other + net_cg
    gti = max(Decimal("0.00"), raw_gti)

    steps.append(
        CalculationStep(
            step_id="gross_total_income",
            label="Gross Total Income (GTI)",
            section_ref="Section 80B(5)",
            formula_text="Net Salary + House Property Income/(Loss) + Other Sources + Capital Gains",
            inputs={
                "net_salary": net_salary,
                "net_house_property": net_hp,
                "net_other_sources": net_other,
                "net_capital_gains": net_cg,
            },
            result=gti,
            explanation=f"Gross Total Income before Chapter VI-A deductions: ₹{gti:,.2f}.",
        )
    )

    results = {
        "net_salary": net_salary,
        "net_house_property": net_hp,
        "net_other_sources": net_other,
        "net_capital_gains": net_cg,
        "gross_total_income": gti,
    }

    return results, steps
