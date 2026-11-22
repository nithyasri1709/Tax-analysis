"""
Tabular Extractor
Extracts structured table and transaction data from CSV, XLS, and XLSX spreadsheets using Pandas.
"""

from __future__ import annotations

import io
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd


def parse_tabular_file(file_bytes: bytes, file_type: str) -> Tuple[bool, List[Dict[str, Any]], str]:
    """
    Parses CSV, XLSX, or XLS files into list of row dictionaries.
    Returns:
      (success: bool, rows: List[Dict[str, Any]], summary_text: str)
    """
    try:
        if "csv" in file_type.lower():
            # Try utf-8 first, then latin1
            try:
                df = pd.read_csv(io.BytesIO(file_bytes), encoding="utf-8")
            except UnicodeDecodeError:
                df = pd.read_csv(io.BytesIO(file_bytes), encoding="latin1")
        elif "excel" in file_type.lower() or "sheet" in file_type.lower() or "openxml" in file_type.lower():
            df = pd.read_excel(io.BytesIO(file_bytes))
        else:
            return False, [], f"Unsupported tabular MIME type: {file_type}"

        # Clean column names
        df.columns = [str(c).strip() for c in df.columns]
        # Drop completely empty rows
        df = df.dropna(how="all")

        rows = df.to_dict(orient="records")
        text_summary = f"Spreadsheet containing {len(rows)} records and columns: {', '.join(df.columns)}"
        return True, rows, text_summary
    except Exception as e:
        return False, [], f"Error parsing spreadsheet: {str(e)}"
