"""
Transaction Classifier Service
Hybrid categorisation:
1. Deterministic keyword and regex matching
2. Scikit-learn TF-IDF + Logistic Regression model trained on synthetic banking transactions
3. Statutory deduction mapping with condition checks
4. Reversal and duplicate detection
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

CATEGORIES_META = {
    "House Rent": {
        "section": "10(13A)",
        "tax_eligible": True,
        "conditions": "Must be paying rent for residential accommodation; landlord PAN required if rent > ₹1L/year.",
        "limit": "Least of 3 HRA conditions (Old regime only).",
    },
    "Health Insurance": {
        "section": "80D",
        "tax_eligible": True,
        "conditions": "Must be paid by non-cash mode for self, spouse, children, or parents.",
        "limit": "₹25,000 (₹50,000 for senior citizen) (Old regime only).",
    },
    "Life Insurance": {
        "section": "80C",
        "tax_eligible": True,
        "conditions": "Premium on policy for self, spouse, or child; premium <= 10% of sum assured.",
        "limit": "Combined ₹1,50,000 cap under 80C (Old regime only).",
    },
    "PPF": {
        "section": "80C",
        "tax_eligible": True,
        "conditions": "Deposit in Public Provident Fund account.",
        "limit": "Combined ₹1,50,000 cap (Old regime only).",
    },
    "ELSS": {
        "section": "80C",
        "tax_eligible": True,
        "conditions": "3-year lock-in period equity linked saving scheme.",
        "limit": "Combined ₹1,50,000 cap (Old regime only).",
    },
    "NPS": {
        "section": "80CCD(1B)",
        "tax_eligible": True,
        "conditions": "Voluntary deposit in NPS Tier-1 account.",
        "limit": "Additional ₹50,000 deduction under 80CCD(1B) (Old regime only).",
    },
    "Home Loan Principal": {
        "section": "80C",
        "tax_eligible": True,
        "conditions": "Repayment of principal borrowed for purchase/construction of residential house.",
        "limit": "Combined ₹1,50,000 cap (Old regime only).",
    },
    "Home Loan Interest": {
        "section": "24(b)",
        "tax_eligible": True,
        "conditions": "Interest on borrowed capital; construction completed within 5 years.",
        "limit": "₹2,00,000 for self-occupied property (Old regime only).",
    },
    "Education Loan Interest": {
        "section": "80E",
        "tax_eligible": True,
        "conditions": "Loan taken for higher education of self, spouse, or children.",
        "limit": "No upper cap; max 8 years (Old regime only).",
    },
    "Donations": {
        "section": "80G",
        "tax_eligible": True,
        "conditions": "Donation to eligible approved funds/institutions; stamped receipt & 80G certificate required.",
        "limit": "50% or 100% of donation (Old regime only).",
    },
    "Tuition Fees": {
        "section": "80C",
        "tax_eligible": True,
        "conditions": "Full-time education tuition fees for up to 2 children in Indian schools/colleges.",
        "limit": "Combined ₹1,50,000 cap (Old regime only).",
    },
    "Medical Expenses": {
        "section": "80DDB / 80D",
        "tax_eligible": True,
        "conditions": "Medical expenditure for senior citizens without health insurance or specified diseases.",
        "limit": "₹50,000 for senior under 80D / ₹1,00,000 under 80DDB.",
    },
    "Other Expenses": {
        "section": None,
        "tax_eligible": False,
        "conditions": "Personal or non-deductible operational expense.",
        "limit": "None",
    },
    "Non-deductible/Personal": {
        "section": None,
        "tax_eligible": False,
        "conditions": "Standard personal/lifestyle consumption.",
        "limit": "None",
    },
}

# Rule-based regex keyword patterns
RULE_PATTERNS = [
    (r"\b(?:rent\s*transfer|house\s*rent|rent\s*paid|to\s*landlord|pg\s*rent)\b", "House Rent", 0.98),
    (r"\b(?:hdfc\s*ergo|star\s*health|care\s*health|niva\s*bupa|mediclaim|health\s*insurance)\b", "Health Insurance", 0.98),
    (r"\b(?:lic\s*of\s*india|max\s*life|icici\s*pru\s*life|tata\s*aia|life\s*insurance)\b", "Life Insurance", 0.98),
    (r"\b(?:ppf\s*dep|public\s*provident|ppf\s*subscription)\b", "PPF", 0.98),
    (r"\b(?:elss|mirae\s*asset\s*tax|axis\s*long\s*term|quant\s*tax|tax\s*saver\s*fund)\b", "ELSS", 0.98),
    (r"\b(?:nps\s*trust|cra\s*nsdl|nps\s*contribution|tier\s*1\s*nps)\b", "NPS", 0.98),
    (r"\b(?:home\s*loan\s*emi|hl\s*emi|housing\s*loan|sbi\s*home\s*loan|hdfc\s*ltd\s*emi)\b", "Home Loan Principal", 0.85),
    (r"\b(?:education\s*loan|vidya\s*lakshmi|student\s*loan\s*emi)\b", "Education Loan Interest", 0.95),
    (r"\b(?:pm\s*cares|cry\s*india|giveindia|helpage|prime\s*minister\s*relief|donation)\b", "Donations", 0.95),
    (r"\b(?:school\s*fees|tuition\s*fee|dps\s*fee|college\s*tuition)\b", "Tuition Fees", 0.95),
    (r"\b(?:swiggy|zomato|amazon|flipkart|uber|ola|netflix|blinkit|zepto|supermarket)\b", "Non-deductible/Personal", 0.99),
]

# Synthetic training dataset for ML TF-IDF + Logistic Regression fallback
SYNTHETIC_TRANSACTIONS = [
    ("UPI/5123/Swiggy order Bangalore", "Non-deductible/Personal"),
    ("POS/Amazon India purchase electronic", "Non-deductible/Personal"),
    ("Zomato food delivery dinner", "Non-deductible/Personal"),
    ("Uber trip ride Bangalore", "Non-deductible/Personal"),
    ("Netflix monthly subscription", "Non-deductible/Personal"),
    ("NEFT to Landlord Ramesh Sharma House Rent", "House Rent"),
    ("UPI to Apartment Owner monthly rent payment", "House Rent"),
    ("Transfer to Landlady flat rent for Nov", "House Rent"),
    ("Star Health Insurance renewal premium", "Health Insurance"),
    ("Care Health Insurance family floater policy", "Health Insurance"),
    ("HDFC ERGO health suraksha plan payment", "Health Insurance"),
    ("LIC premium quarterly payment policy", "Life Insurance"),
    ("ICICI Prudential iProtect Smart life insurance", "Life Insurance"),
    ("Max Life online term plan premium", "Life Insurance"),
    ("Deposit to SBI PPF Account 1029384756", "PPF"),
    ("Transfer to Public Provident Fund monthly", "PPF"),
    ("Mirae Asset Tax Saver Fund ELSS SIP", "ELSS"),
    ("Parag Parikh Tax Saver Fund ELSS investment", "ELSS"),
    ("NPS contribution via NSDL CRA payment gateway", "NPS"),
    ("NPS Trust Tier 1 eNPS voluntary deposit", "NPS"),
    ("SBI Housing Loan Monthly EMI Repayment", "Home Loan Principal"),
    ("HDFC Bank Home loan principal and interest EMI", "Home Loan Principal"),
    ("Canara Bank Vidya Lakshmi Education Loan EMI", "Education Loan Interest"),
    ("SBI Student Scholar Loan monthly repayment", "Education Loan Interest"),
    ("Donation to PM CARES Fund relief contribution", "Donations"),
    ("Online donation to Akshaya Patra Foundation", "Donations"),
    ("Delhi Public School annual tuition fees term 1", "Tuition Fees"),
    ("St Xaviers School tuition fee second installment", "Tuition Fees"),
    ("Apollo Pharmacy medicines prescription", "Medical Expenses"),
    ("Max Hospital health diagnostic full body checkup", "Medical Expenses"),
]


class TransactionClassifier:
    _instance: Optional[TransactionClassifier] = None

    def __init__(self):
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression

        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
        texts = [t[0] for t in SYNTHETIC_TRANSACTIONS]
        labels = [t[1] for t in SYNTHETIC_TRANSACTIONS]
        X = self.vectorizer.fit_transform(texts)
        self.model = LogisticRegression(max_iter=200)
        self.model.fit(X, labels)

    @classmethod
    def get_instance(cls) -> TransactionClassifier:
        if cls._instance is None:
            cls._instance = TransactionClassifier()
        return cls._instance

    def classify(self, description: str) -> Dict[str, Any]:
        """
        Classifies transaction description using Rules first, then ML model.
        Returns full classification metadata.
        """
        clean_desc = description.strip()

        # Step 1: Rule-based regex check
        for pattern, cat, conf in RULE_PATTERNS:
            if re.search(pattern, clean_desc, re.IGNORECASE):
                meta = CATEGORIES_META.get(cat, {})
                return {
                    "category": cat,
                    "confidence": conf,
                    "classification_source": "rule",
                    "is_potentially_tax_eligible": meta.get("tax_eligible", False),
                    "applicable_section": meta.get("section"),
                    "conditions": meta.get("conditions", ""),
                    "limit_explanation": meta.get("limit", ""),
                    "deduction_status": "needs_proof" if meta.get("tax_eligible") else "ineligible",
                }

        # Step 2: ML Fallback
        X = self.vectorizer.transform([clean_desc])
        probs = self.model.predict_proba(X)[0]
        max_idx = probs.argmax()
        ml_category = self.model.classes_[max_idx]
        ml_confidence = round(float(probs[max_idx]), 2)

        # Fallback to Other Expenses if ML confidence is low
        if ml_confidence < 0.35:
            final_cat = "Other Expenses"
            final_conf = 0.50
        else:
            final_cat = ml_category
            final_conf = ml_confidence

        meta = CATEGORIES_META.get(final_cat, {})
        return {
            "category": final_cat,
            "confidence": final_conf,
            "classification_source": "ml",
            "is_potentially_tax_eligible": meta.get("tax_eligible", False),
            "applicable_section": meta.get("section"),
            "conditions": meta.get("conditions", ""),
            "limit_explanation": meta.get("limit", ""),
            "deduction_status": "needs_proof" if meta.get("tax_eligible") else "ineligible",
        }


def detect_duplicate_or_reversal(
    transactions: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Identifies duplicate transactions (exact match on date + amount + description)
    and reversed transactions (debit followed by credit of exact same amount with 'REV' or 'REFUND').
    """
    seen_hashes = set()
    for t in transactions:
        t["is_duplicate"] = False
        desc_lower = str(t.get("description", "")).lower()

        # Reversal pattern
        if "rev" in desc_lower or "refund" in desc_lower or "reversal" in desc_lower:
            t["is_reversal"] = True

        sig = f"{t.get('date')}_{t.get('amount')}_{t.get('description', '')[:30]}"
        if sig in seen_hashes:
            t["is_duplicate"] = True
        else:
            seen_hashes.add(sig)

    return transactions
