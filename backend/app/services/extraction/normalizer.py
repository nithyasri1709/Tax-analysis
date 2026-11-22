"""
Extraction Normalizer
Normalizes Indian currency notations (Lakhs, Crores, INR formatting), dates, and Financial Years.
"""

from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal
from typing import Optional, Tuple


def parse_inr_amount(val_str: str) -> Optional[float]:
    """
    Parses strings containing INR currency values into float.
    Handles:
      '₹ 1,50,000.00' -> 150000.0
      '1,25,000' -> 125000.0
      '1.5 Lakh' / '1.5L' -> 150000.0
      '2.5 Cr' / '2.5 Crore' -> 25000000.0
      'Rs. 50,000/-' -> 50000.0
    """
    if not val_str:
        return None

    clean = str(val_str).strip()
    # Check for Lakhs / Crores suffix
    lakh_match = re.search(r"([\d\.]+)\s*(?:lakh|lac|l)\b", clean, re.IGNORECASE)
    if lakh_match:
        try:
            return float(Decimal(lakh_match.group(1)) * Decimal("100000"))
        except Exception:
            pass

    cr_match = re.search(r"([\d\.]+)\s*(?:crore|cr)\b", clean, re.IGNORECASE)
    if cr_match:
        try:
            return float(Decimal(cr_match.group(1)) * Decimal("10000000"))
        except Exception:
            pass

    # Remove currency symbols, commas, and trailing /-, but PRESERVE the decimal dot (.)
    clean = re.sub(r"[₹Rs\s/-]", "", clean)
    clean = clean.replace(",", "")

    # Look for standard number
    num_match = re.search(r"-?\d+(?:\.\d+)?", clean)
    if num_match:
        try:
            return float(Decimal(num_match.group(0)))
        except Exception:
            return None

    return None


def parse_indian_date(date_str: str) -> Optional[str]:
    """
    Parses various Indian date representations into standard ISO format (YYYY-MM-DD).
    Accepts:
      DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY, YYYY-MM-DD, DD-Mon-YYYY
    """
    if not date_str:
        return None

    clean = str(date_str).strip()
    formats = [
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d.%m.%Y",
        "%Y-%m-%d",
        "%d-%b-%Y",
        "%d %b %Y",
        "%d %B %Y",
        "%d/%m/%y",
        "%d-%m-%y",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(clean, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    # Regex search within messy strings
    m = re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b", clean)
    if m:
        day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            dt = datetime(year, month, day)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass

    return None


def detect_financial_year_from_text(text: str) -> Optional[str]:
    """
    Detects Financial Year from document text or returns None.
    Handles:
      'FY 2025-26', 'Financial Year 2025-2026', 'AY 2026-27' (Assessment Year is FY + 1).
    """
    if not text:
        return None

    # Check for direct FY
    fy_match = re.search(r"(?:FY|Financial Year|F\.Y\.)\s*[:\-]?\s*(20\d{2})[-/](20\d{2}|\d{2})", text, re.IGNORECASE)
    if fy_match:
        y1 = int(fy_match.group(1))
        y2_str = fy_match.group(2)
        y2 = int(y2_str) if len(y2_str) == 4 else int(str(y1)[:2] + y2_str)
        return f"{y1}-{str(y2)[-2:]}"

    # Check for Assessment Year (AY): AY 2026-27 means FY 2025-26
    ay_match = re.search(r"(?:AY|Assessment Year|A\.Y\.)\s*[:\-]?\s*(20\d{2})[-/](20\d{2}|\d{2})", text, re.IGNORECASE)
    if ay_match:
        y1 = int(ay_match.group(1))
        y2_str = ay_match.group(2)
        y2 = int(y2_str) if len(y2_str) == 4 else int(str(y1)[:2] + y2_str)
        fy_start = y1 - 1
        fy_end = y2 - 1
        return f"{fy_start}-{str(fy_end)[-2:]}"

    return None
