"""
Master Tax Calculator
Pure Python deterministic tax computation engine. Zero external DB/HTTP dependencies.
Adheres strictly to Indian Income-tax statutory provisions.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Optional
from app.services.tax_engine.common import CalculationStep, to_decimal
from app.services.tax_engine.rules_provider import TaxRulesProvider
from app.services.tax_engine.exemptions import compute_hra_exemption
from app.services.tax_engine.income import compute_heads_of_income
from app.services.tax_engine.deductions import compute_chapter_vi_a_deductions
from app.services.tax_engine.slabs import compute_slab_tax
from app.services.tax_engine.rebate import compute_section_87a_rebate
from app.services.tax_engine.surcharge import compute_surcharge_with_marginal_relief
from app.services.tax_engine.cess import compute_cess_and_total_liability
from app.services.tax_engine.advance_tax import compute_advance_tax_and_interest


def calculate_tax(
    financial_year: str,
    regime: str,
    salary_data: Optional[Dict[str, Any]] = None,
    house_prop_data: Optional[Dict[str, Any]] = None,
    other_sources_data: Optional[Dict[str, Any]] = None,
    capital_gains_data: Optional[Dict[str, Any]] = None,
    deductions_data: Optional[Dict[str, Any]] = None,
    taxes_paid_data: Optional[Dict[str, Any]] = None,
    age_bracket: str = "regular",
    employment_type: str = "salaried",
    is_metro: bool = False,
    rules_provider: Optional[TaxRulesProvider] = None,
    months_delay_filing: int = 0,
) -> Dict[str, Any]:
    """
    Pure Python deterministic calculation of income tax.
    """
    salary_data = salary_data or {}
    house_prop_data = house_prop_data or {}
    other_sources_data = other_sources_data or {}
    capital_gains_data = capital_gains_data or {}
    deductions_data = deductions_data or {}
    taxes_paid_data = taxes_paid_data or {}

    provider = rules_provider or TaxRulesProvider.get_instance()
    rules = provider.get_rules_for_fy(financial_year)
    norm_regime = regime.lower().strip()
    if norm_regime not in ["old", "new"]:
        raise ValueError(f"Invalid regime: '{regime}'. Must be 'old' or 'new'.")

    all_steps: List[CalculationStep] = []

    # 1. HRA Exemption
    basic_salary = to_decimal(salary_data.get("basic_salary", 0))
    da_amount = to_decimal(salary_data.get("da_amount", 0))
    hra_received = to_decimal(salary_data.get("hra_received", 0))
    rent_paid = to_decimal(salary_data.get("rent_paid", 0))

    hra_exempt, hra_steps = compute_hra_exemption(
        basic_salary=basic_salary,
        da_amount=da_amount,
        hra_received=hra_received,
        annual_rent_paid=rent_paid,
        is_metro=is_metro,
        regime=norm_regime,
        rules=rules,
    )
    all_steps.extend(hra_steps)

    # 2. Heads of Income & Gross Total Income
    income_results, income_steps = compute_heads_of_income(
        salary_data=salary_data,
        house_prop_data=house_prop_data,
        other_sources_data=other_sources_data,
        capital_gains_data=capital_gains_data,
        employment_type=employment_type,
        regime=norm_regime,
        rules=rules,
        exemptions_total=hra_exempt,
    )
    all_steps.extend(income_steps)
    gross_total_income = income_results["gross_total_income"]

    # 3. Chapter VI-A Deductions & Taxable Total Income
    total_deductions, taxable_income, ded_breakdown, ded_steps = compute_chapter_vi_a_deductions(
        deductions_data=deductions_data,
        salary_data=salary_data,
        age_bracket=age_bracket,
        regime=norm_regime,
        gross_total_income=gross_total_income,
        rules=rules,
    )
    all_steps.extend(ded_steps)

    # 4. Slab Tax Computation
    slab_tax, slab_breakdown, slab_steps = compute_slab_tax(
        taxable_income=taxable_income,
        regime=norm_regime,
        age_bracket=age_bracket,
        rules=rules,
    )
    all_steps.extend(slab_steps)

    # 5. Section 87A Rebate & Marginal Relief
    rebate_87a, tax_after_rebate, rebate_steps = compute_section_87a_rebate(
        taxable_income=taxable_income,
        slab_tax=slab_tax,
        regime=norm_regime,
        rules=rules,
    )
    all_steps.extend(rebate_steps)

    # 6. Surcharge & Marginal Relief
    def _slab_calc_helper(inc: Decimal) -> Decimal:
        st, _, _ = compute_slab_tax(inc, norm_regime, age_bracket, rules)
        rb, ar, _ = compute_section_87a_rebate(inc, st, norm_regime, rules)
        return ar

    nominal_sc, sc_relief, net_surcharge, sc_steps = compute_surcharge_with_marginal_relief(
        taxable_income=taxable_income,
        tax_after_rebate=tax_after_rebate,
        regime=norm_regime,
        rules=rules,
        slab_tax_calculator_fn=_slab_calc_helper,
    )
    all_steps.extend(sc_steps)

    # 7. Cess (4%) and Gross Tax Liability
    cess_amount, gross_unrounded, gross_liability, cess_steps = compute_cess_and_total_liability(
        tax_after_rebate=tax_after_rebate,
        net_surcharge=net_surcharge,
        rules=rules,
    )
    all_steps.extend(cess_steps)

    # 8. Advance Tax, TDS Credits, Statutory Interest & Net Balance
    tax_summary, balance_payable_refund, adv_steps = compute_advance_tax_and_interest(
        gross_tax_liability=gross_liability,
        taxes_paid_data=taxes_paid_data,
        rules=rules,
        months_delay_filing=months_delay_filing,
    )
    all_steps.extend(adv_steps)

    # Effective tax rate computation
    effective_tax_rate = (
        float((gross_liability / gross_total_income * 100).quantize(Decimal("0.01")))
        if gross_total_income > Decimal("0.00")
        else 0.0
    )

    return {
        "financial_year": financial_year,
        "regime": norm_regime,
        "age_bracket": age_bracket,
        "employment_type": employment_type,
        "governing_act": rules.get("governing_act", ""),
        "verification_date": rules.get("verification_date", ""),
        "source_url": rules.get("source_url", ""),
        "disclaimer": "Estimate only; not professional tax advice.",
        # Income Summary
        "gross_salary": float(to_decimal(salary_data.get("gross_salary", 0))),
        "exemptions_total": float(hra_exempt),
        "standard_deduction": float(income_steps[0].inputs.get("standard_deduction", 0)),
        "professional_tax": float(income_steps[0].inputs.get("professional_tax", 0)),
        "net_salary": float(income_results["net_salary"]),
        "net_house_property": float(income_results["net_house_property"]),
        "net_other_sources": float(income_results["net_other_sources"]),
        "net_capital_gains": float(income_results["net_capital_gains"]),
        "gross_total_income": float(gross_total_income),
        # Deductions
        "total_chapter_vi_a_deductions": float(total_deductions),
        "deductions_breakdown": {k: float(v) for k, v in ded_breakdown.items()},
        "taxable_total_income": float(taxable_income),
        # Tax Calculation
        "slab_tax": float(slab_tax),
        "slab_breakdown": slab_breakdown,
        "rebate_87a": float(rebate_87a),
        "tax_after_rebate": float(tax_after_rebate),
        "nominal_surcharge": float(nominal_sc),
        "surcharge_marginal_relief": float(sc_relief),
        "net_surcharge": float(net_surcharge),
        "health_and_education_cess": float(cess_amount),
        "gross_tax_liability": float(gross_liability),
        "effective_tax_rate_percent": effective_tax_rate,
        # Taxes Paid & Balance
        "total_taxes_paid": float(tax_summary["total_prepaid_taxes"]),
        "tds_total": float(tax_summary["total_tds_tcs"]),
        "advance_tax_total": float(tax_summary["total_advance_tax"]),
        "statutory_interest_234abc": float(tax_summary["total_statutory_interest"]),
        "balance_payable_or_refund": float(balance_payable_refund),
        "is_refund": balance_payable_refund < 0,
        "advance_tax_schedule": tax_summary["advance_tax_schedule"],
        # Audit Trail / Explainability
        "calculation_breakdown": [step.to_dict() for step in all_steps],
    }
