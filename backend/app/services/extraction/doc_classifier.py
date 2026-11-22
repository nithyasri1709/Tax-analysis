"""
Document Classifier
Classifies ingested documents into statutory Indian tax document categories based on keywords, layout, and headers.
"""

from __future__ import annotations

import re
from typing import Tuple

CLASSIFIER_RULES = {
    "form_16": [
        (r"\bform\s*(?:no\.?|number)?\s*16\b", 0.40),
        (r"\bcertificate\s+under\s+section\s+203\b", 0.35),
        (r"\btax\s+deducted\s+at\s+source\b", 0.15),
        (r"\bpart\s+[ab]\b", 0.15),
        (r"\bquarterly\s+receipt\b", 0.15),
    ],
    "salary_slip": [
        (r"\b(?:pay\s*slip|salary\s*slip|payslip)\b", 0.40),
        (r"\b(?:basic\s*salary|basic\s*pay)\b", 0.25),
        (r"\bhouse\s*rent\s*allowance\b|\bhra\b", 0.20),
        (r"\b(?:net\s*pay|gross\s*salary|gross\s*earnings)\b", 0.20),
        (r"\bprovident\s*fund\b|\bepf\b|\bpf\s*deduction\b", 0.15),
    ],
    "bank_statement": [
        (r"\b(?:statement\s+of\s+account|account\s+statement|bank\s+statement)\b", 0.40),
        (r"\b(?:account\s*no|a/c\s*no)\b", 0.20),
        (r"\b(?:withdrawal|deposit|debit|credit|balance)\b", 0.25),
        (r"\b(?:ifsc|micr|upi/|neft/|rtgs/|imps/)\b", 0.20),
    ],
    "insurance_receipt": [
        (r"\b(?:premium\s*receipt|renewal\s*premium|insurance\s*policy)\b", 0.40),
        (r"\b(?:life\s*insurance|health\s*insurance|mediclaim)\b", 0.30),
        (r"\b(?:policy\s*no|sum\s*assured|insured\s*person)\b", 0.20),
        (r"\bsection\s*80d\b|\bsection\s*80c\b", 0.15),
    ],
    "home_loan_statement": [
        (r"\b(?:housing\s*loan|home\s*loan|home\s*loan\s*statement)\b", 0.40),
        (r"\b(?:provisional\s*interest\s*certificate|interest\s*certificate)\b", 0.35),
        (r"\b(?:principal\s*paid|principal\s*component)\b", 0.25),
        (r"\b(?:interest\s*paid|interest\s*component)\b", 0.25),
        (r"\bsection\s*24\b|\bsection\s*80c\b", 0.15),
    ],
    "education_loan_certificate": [
        (r"\b(?:education\s*loan|student\s*loan)\b", 0.45),
        (r"\bsection\s*80e\b", 0.40),
        (r"\bhigher\s*education\b", 0.20),
    ],
    "rent_receipt": [
        (r"\b(?:rent\s*receipt|house\s*rent\s*receipt)\b", 0.50),
        (r"\breceived\s+from\b", 0.20),
        (r"\brent\s+paid\b|\bpremises\b|\blandlord\b", 0.25),
        (r"\bsection\s*10\(13a\)\b", 0.20),
    ],
    "investment_proof": [
        (r"\b(?:public\s*provident\s*fund|ppf|elss|tax\s*saving\s*mutual\s*fund)\b", 0.40),
        (r"\b(?:national\s*pension\s*system|nps|tier[\s-]*1)\b", 0.40),
        (r"\b(?:nsc|national\s*savings\s*certificate|tax\s*saving\s*fd)\b", 0.35),
        (r"\bfolio\s*no\b|\bnav\b|\bunits\s*allotted\b", 0.20),
    ],
    "donation_receipt": [
        (r"\b(?:donation\s*receipt|receipt\s*for\s*donation)\b", 0.50),
        (r"\bsection\s*80g\b", 0.40),
        (r"\bexempt\s+under\s+section\s+80g\b", 0.30),
    ],
    "ais_26as": [
        (r"\b(?:form\s*26as|annual\s*information\s*statement|ais|tis)\b", 0.50),
        (r"\btax\s+credit\s+statement\b", 0.35),
        (r"\btds\s+deposited\b", 0.20),
    ],
}


def classify_document(text: str, filename: str = "") -> Tuple[str, float]:
    """
    Evaluates text against classification rules and returns (best_category, confidence).
    """
    combined = f"{filename}\n{text}".lower()
    scores = {}

    for category, rules in CLASSIFIER_RULES.items():
        total_score = 0.0
        for pattern, weight in rules:
            if re.search(pattern, combined, re.IGNORECASE):
                total_score += weight
        if total_score > 0:
            scores[category] = min(1.0, total_score)

    if not scores:
        return "other", 0.50

    best_category = max(scores, key=scores.get)
    best_confidence = round(scores[best_category], 2)

    # Threshold for confident assignment
    if best_confidence < 0.35:
        return "other", 0.40

    return best_category, best_confidence
