# Statutory Tax Rules & Financial Year Configuration Guide

The **INTELLIGENT TAX ASSISTANT** executes tax mathematics using a pure-Python, deterministic rules engine. **No statutory rate, threshold, rebate cap, or deduction limit is ever hardcoded in the codebase.**

All tax law parameters are loaded from versioned, schema-validated JSON configuration files located at:
`backend/app/services/tax_engine/rules/`

---

## 1. Statutory Configuration Structure

Each Financial Year config (`fy2024_25.json`, `fy2025_26.json`, `fy2026_27.json`) adheres to `schema.json`.

### Metadata Block
```json
"metadata": {
  "financial_year": "2025-26",
  "assessment_year": "2026-27",
  "applicable_act": "Income-tax Act, 1961",
  "last_verified_date": "2026-03-31",
  "source_url": "https://incometax.gov.in"
}
```

### New Regime Block (`new_regime`)
- `standard_deduction`: Salaried deduction (e.g. ₹75,000 in FY 25-26 and FY 26-27).
- `slabs`: Progressive income bands and tax rates.
- `rebate_87a`: Threshold (e.g., ₹12,00,000 for FY 25-26/26-27), maximum rebate (₹60,000), and `marginal_relief_formula`.
- `surcharge`: Rates (10%, 15%, 25%) and bracket thresholds.
- `cess_rate`: 0.04 (4% Health and Education Cess).
- `allowed_deductions`: Explicit list of permissible deductions (e.g., `80ccd_2`).

### Old Regime Block (`old_regime`)
- `standard_deduction`: ₹50,000.
- `age_brackets`: Separate basic exemption thresholds for `regular` (₹2.5L), `senior` (₹3.0L), and `super_senior` (₹5.0L).
- `slabs`: Progressive rate brackets.
- `rebate_87a`: Threshold ₹5,00,000, max rebate ₹12,500.
- `surcharge`: Rates up to 37% with marginal relief calculations.
- `cess_rate`: 0.04 (4%).
- `chapter_via`: Full limits for Section 80C, 80CCD(1B), 80D, 80E, 80G, 80TTA, 80TTB, and 24(b).

---

## 2. Income-tax Act, 1961 vs Income-tax Act, 2025 Crosswalk

From 1 April 2026, the **Income-tax Act, 2025** superseded the **Income-tax Act, 1961**.
The section crosswalk is configured in `backend/app/services/tax_engine/rules/section_mapping.json`:

| Description | 1961 Act Section | 2025 Act Section | Status |
| :--- | :--- | :--- | :--- |
| Concessional Tax Regime | Section 115BAC | Section 115BAC | Verified |
| Standard Deduction (Salary) | Section 16(ia) | Section 16(ia) | Verified |
| HRA Exemption | Section 10(13A) | Section 10(13A) | Verify |
| Investments (EPF, PPF, ELSS, Life Ins) | Section 80C | Section 80C | Verify |
| Additional NPS Tier-1 | Section 80CCD(1B) | Section 80CCD(1B) | Verify |
| Employer NPS Contribution | Section 80CCD(2) | Section 80CCD(2) | Verified |
| Health Insurance Mediclaim | Section 80D | Section 80D | Verify |
| Education Loan Interest | Section 80E | Section 80E | Verify |
| Charitable Donations | Section 80G | Section 80G | Verify |
| Home Loan Interest (Self-Occupied) | Section 24(b) | Section 24(b) | Verify |
| Savings Account Interest | Section 80TTA / 80TTB | Section 80TTA / 80TTB | Verify |
| Tax Rebate & Marginal Relief | Section 87A | Section 87A | Verified |
| Rounding of Taxable Income | Section 288A | Section 288A | Verified |
| Rounding of Tax Payable | Section 288B | Section 288B | Verified |

Any mapping that has not been confirmed with gazette notification is flagged as `"status": "verify"`, and rendered in the UI with a `[verify]` pill to prevent misleading taxpayers.

---

## 3. How to Add a New Financial Year (e.g., FY 2027-28)

To add support for a new financial year:

1. **Create the Config File**:
   Copy `backend/app/services/tax_engine/rules/fy2026_27.json` to:
   `backend/app/services/tax_engine/rules/fy2027_28.json`

2. **Update Metadata**:
   ```json
   "metadata": {
     "financial_year": "2027-28",
     "assessment_year": "2028-29",
     "applicable_act": "Income-tax Act, 2025",
     "last_verified_date": "YYYY-MM-DD",
     "source_url": "https://incometax.gov.in"
   }
   ```

3. **Adjust Slabs and Statutory Limits**:
   Update any changes introduced in the relevant Union Budget for that year.

4. **Validate Schema**:
   Run the CLI validator:
   ```bash
   python backend/app/services/tax_engine/validate_rules.py
   ```

5. **Expose in Frontend Selector**:
   Add `"2027-28"` to the dropdown options in `frontend/src/components/layout/Navbar.tsx`.

---

## 4. Statutory Rounding Rules

As mandated by Indian Tax Law:
- **Section 288A**: Total Taxable Income is rounded to the nearest multiple of ten rupees (₹10).
- **Section 288B**: Total Tax Payable or Refund Due is rounded to the nearest multiple of ten rupees (₹10).

Both rounding rules are strictly enforced in Python using high-precision `decimal.Decimal` calculations.
