"""
Field Extractors
Rule-based and regex field extraction engine with confidence scoring,
source snippet extraction, and financial sanity validation.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from app.core.encryption import mask_pan
from app.services.extraction.normalizer import parse_inr_amount


def _extract_field_with_regex(
    patterns: List[str],
    text: str,
    key: str,
    label: str,
    default_confidence: float = 0.90,
) -> Optional[Dict[str, Any]]:
    """Helper to match regex patterns against text and extract snippet and value."""
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            val_str = m.group(1).strip()
            num_val = parse_inr_amount(val_str)
            # Find surrounding snippet (up to 50 chars before and after)
            start = max(0, m.start() - 30)
            end = min(len(text), m.end() + 30)
            snippet = text[start:end].replace("\n", " ").strip()

            return {
                "field_key": key,
                "field_label": label,
                "field_value": val_str,
                "normalized_value": num_val,
                "confidence": default_confidence,
                "source_snippet": snippet,
                "conflict_flag": False,
            }
    return None


def regex_extract_fields(text: str, doc_type: str) -> Dict[str, Any]:
    """Offline rule-based field extractor across all document types."""
    results: Dict[str, Any] = {}

    # 1. PAN extraction
    pan_match = re.search(r"\b([A-Z]{5}[0-9]{4}[A-Z])\b", text)
    if pan_match:
        pan_raw = pan_match.group(1)
        results["pan"] = {
            "field_key": "pan",
            "field_label": "PAN (Permanent Account Number)",
            "field_value": pan_raw,
            "normalized_value": None,
            "confidence": 0.98,
            "source_snippet": f"PAN: {mask_pan(pan_raw)}",
            "conflict_flag": False,
        }

    # 2. Gross Salary
    gross_patterns = [
        r"(?:total\s+gross\s+salary)[\s:\-]*(?:₹|Rs\.?|I)?\s*([\d,]+(?:\.\d{2})?)",
        r"(?:salary\s+as\s+per\s+provisions.*?17\(1\))[\s:\-]*(?:₹|Rs\.?|I)?\s*([\d,]+(?:\.\d{2})?)",
        r"(?:gross\s+earnings|gross\s+salary|gross\s+pay|total\s+earnings|gross\s+amount)[\s:\-]*(?:₹|Rs\.?|I)?\s*([\d,]+(?:\.\d{2})?)",
        r"(?:salary\s+credited)[\s:\-]*(?:₹|Rs\.?|I)?\s*([\d,]+(?:\.\d{2})?)",
    ]
    f = _extract_field_with_regex(gross_patterns, text, "gross_salary", "Gross Annual / Period Salary")
    if f:
        results["gross_salary"] = f

    # 3. Basic Salary
    basic_patterns = [
        r"(?:basic\s+salary|basic\s+pay|basic)[\s:\-]*(?:₹|Rs\.?|I)?\s*([\d,]+(?:\.\d{2})?)",
    ]
    f = _extract_field_with_regex(basic_patterns, text, "basic_salary", "Basic Salary")
    if f:
        results["basic_salary"] = f

    # 4. HRA (House Rent Allowance)
    hra_patterns = [
        r"(?:house\s+rent\s+allowance|hra|h\.r\.a\.)(?:\s*\(.*?\))?[\s:\-]*(?:₹|Rs\.?|I)?\s*([\d,]+(?:\.\d{2})?)",
    ]
    f = _extract_field_with_regex(hra_patterns, text, "hra_received", "House Rent Allowance (HRA)")
    if f:
        results["hra_received"] = f

    # 5. Dearness Allowance (DA)
    da_patterns = [
        r"(?:dearness\s+allowance|d\.a\.|da)(?:\s*\(.*?\))?[\s:\-]*(?:₹|Rs\.?|I)?\s*([\d,]+(?:\.\d{2})?)",
    ]
    f = _extract_field_with_regex(da_patterns, text, "da_amount", "Dearness Allowance (DA)")
    if f:
        results["da_amount"] = f

    # 6. Professional Tax
    pt_patterns = [
        r"(?:professional\s+tax|prof\s+tax|p\.tax|pt|tax\s+on\s+employment)(?:\s*\(.*?\))?[\s:\-]*(?:₹|Rs\.?|I)?\s*([\d,]+(?:\.\d{2})?)",
    ]
    f = _extract_field_with_regex(pt_patterns, text, "professional_tax", "Professional Tax (Section 16(iii))")
    if f:
        results["professional_tax"] = f

    # 7. Employee PF
    pf_patterns = [
        r"(?:provident\s+fund|employee\s+pf|epf|pf\s+deduction)(?:\s*\(.*?\))?[\s:\-]*(?:₹|Rs\.?|I)?\s*([\d,]+(?:\.\d{2})?)",
    ]
    f = _extract_field_with_regex(pf_patterns, text, "epf", "Employee Provident Fund (EPF)")
    if f:
        results["epf"] = f

    # 8. TDS (Tax Deducted at Source)
    tds_patterns = [
        r"(?:total\s+tax\s+deducted\s+at\s+source|tax\s+deducted\s+at\s+source|tds|income\s+tax\s+deducted|tax\s+deducted)(?:\s*\(.*?\))?[\s:\-]*(?:₹|Rs\.?|I)?\s*([\d,]+(?:\.\d{2})?)",
    ]
    f = _extract_field_with_regex(tds_patterns, text, "tds_total", "Tax Deducted at Source (TDS)")
    if f:
        results["tds_total"] = f

    # 9. Health Insurance (Section 80D)
    health_patterns = [
        r"(?:health\s*insurance|mediclaim|medical\s*insurance|section\s*80d)\s*[:\-\s]\s*(?:₹|Rs\.?)?\s*([\d,]+(?:\.\d{2})?)",
        r"(?:premium\s*amount|total\s*premium)\s*[:\-\s]\s*(?:₹|Rs\.?)?\s*([\d,]+(?:\.\d{2})?)",
    ]
    if doc_type == "insurance_receipt":
        f = _extract_field_with_regex(health_patterns, text, "health_insurance_self", "Health Insurance Premium (80D)")
        if f:
            results["health_insurance_self"] = f

    # 10. Home Loan Principal & Interest (Section 80C & 24(b))
    hl_principal_patterns = [
        r"(?:principal\s*repaid|principal\s*amount|principal\s*component)\s*[:\-\s]\s*(?:₹|Rs\.?)?\s*([\d,]+(?:\.\d{2})?)",
    ]
    hl_interest_patterns = [
        r"(?:interest\s*payable|interest\s*component|interest\s*paid|section\s*24)\s*[:\-\s]\s*(?:₹|Rs\.?)?\s*([\d,]+(?:\.\d{2})?)",
    ]
    if doc_type == "home_loan_statement":
        f_p = _extract_field_with_regex(hl_principal_patterns, text, "home_loan_principal", "Home Loan Principal (80C)")
        if f_p:
            results["home_loan_principal"] = f_p
        f_i = _extract_field_with_regex(hl_interest_patterns, text, "home_loan_interest", "Home Loan Interest (Section 24(b))")
        if f_i:
            results["home_loan_interest"] = f_i

    # 11. Rent Paid
    rent_patterns = [
        r"(?:rent\s*paid|monthly\s*rent|rent\s*amount)\s*[:\-\s]\s*(?:₹|Rs\.?)?\s*([\d,]+(?:\.\d{2})?)",
    ]
    if doc_type == "rent_receipt":
        f = _extract_field_with_regex(rent_patterns, text, "rent_paid", "Annual / Monthly Rent Paid")
        if f:
            results["rent_paid"] = f

    # 12. Donations (Section 80G)
    donation_patterns = [
        r"(?:donation\s*amount|amount\s*donated|contribution)\s*[:\-\s]\s*(?:₹|Rs\.?)?\s*([\d,]+(?:\.\d{2})?)",
    ]
    if doc_type == "donation_receipt":
        f = _extract_field_with_regex(donation_patterns, text, "80g_donations", "Donations Eligible under Section 80G")
        if f:
            results["80g_donations"] = f

    # 13. Education Loan Interest (Section 80E)
    edu_patterns = [
        r"(?:interest\s*paid|interest\s*certificate|education\s*loan\s*interest)\s*[:\-\s]\s*(?:₹|Rs\.?)?\s*([\d,]+(?:\.\d{2})?)",
    ]
    if doc_type == "education_loan_certificate":
        f = _extract_field_with_regex(edu_patterns, text, "80e_interest", "Higher Education Loan Interest (Section 80E)")
        if f:
            results["80e_interest"] = f

    # 14. Investment Proofs (PPF, ELSS, NPS)
    inv_patterns = [
        r"(?:amount\s*invested|deposit\s*amount|subscription\s*amount|total\s*amount)\s*[:\-\s]\s*(?:₹|Rs\.?)?\s*([\d,]+(?:\.\d{2})?)",
    ]
    if doc_type == "investment_proof":
        if re.search(r"\bppf\b|\bpublic\s*provident\b", text, re.IGNORECASE):
            f = _extract_field_with_regex(inv_patterns, text, "ppf", "Public Provident Fund (PPF - 80C)")
            if f:
                results["ppf"] = f
        elif re.search(r"\bnps\b|\bnational\s*pension\b", text, re.IGNORECASE):
            f = _extract_field_with_regex(inv_patterns, text, "80ccd_1b", "National Pension System (NPS - 80CCD(1B))")
            if f:
                results["80ccd_1b"] = f
        else:
            f = _extract_field_with_regex(inv_patterns, text, "elss", "ELSS Mutual Fund (80C)")
            if f:
                results["elss"] = f

    # ---------------- SANITY CHECKS ----------------
    gross = results.get("gross_salary", {}).get("normalized_value")
    basic = results.get("basic_salary", {}).get("normalized_value")
    hra = results.get("hra_received", {}).get("normalized_value")

    if gross and basic and basic > gross:
        # Sanity conflict: basic cannot exceed gross
        results["basic_salary"]["conflict_flag"] = True
        results["basic_salary"]["confidence"] = 0.50

    if gross and hra and hra > gross:
        results["hra_received"]["conflict_flag"] = True
        results["hra_received"]["confidence"] = 0.50

    return results
