"""
Extraction Pipeline Tests on Synthetic Documents
Verifies document classifier, field extraction precision, password detection, and tabular parsing.
"""

from pathlib import Path
import pytest
from app.services.extraction.doc_classifier import classify_document
from app.services.extraction.field_extractors import regex_extract_fields
from app.services.extraction.pdf_extractor import extract_text_from_pdf, is_pdf_password_protected
from app.services.extraction.tabular_extractor import parse_tabular_file

SAMPLES_DIR = Path(__file__).parent.parent.parent / "scripts" / "sample_documents"


def test_salary_slip_extraction():
    slip_path = SAMPLES_DIR / "sample_salary_slip.pdf"
    assert slip_path.exists()

    with open(slip_path, "rb") as f:
        data = f.read()

    success, pages, text = extract_text_from_pdf(data)
    assert success is True
    assert "INFOSYS" in text

    # Classification test
    category, conf = classify_document(text, "sample_salary_slip.pdf")
    assert category == "salary_slip"
    assert conf >= 0.70

    # Field extraction test
    fields = regex_extract_fields(text, category)
    assert "gross_salary" in fields
    assert fields["gross_salary"]["normalized_value"] == 125000.0 or fields["gross_salary"]["normalized_value"] == 1500000.0
    assert "basic_salary" in fields
    assert fields["basic_salary"]["normalized_value"] == 50000.0
    assert "hra_received" in fields
    assert fields["hra_received"]["normalized_value"] == 20000.0
    assert "epf" in fields
    assert fields["epf"]["normalized_value"] == 6000.0


def test_form_16_classification_and_extraction():
    f16_path = SAMPLES_DIR / "sample_form_16.pdf"
    assert f16_path.exists()

    with open(f16_path, "rb") as f:
        data = f.read()

    success, _, text = extract_text_from_pdf(data)
    assert success is True

    cat, conf = classify_document(text, "sample_form_16.pdf")
    assert cat == "form_16"
    assert conf >= 0.70

    fields = regex_extract_fields(text, cat)
    assert "gross_salary" in fields
    assert fields["gross_salary"]["normalized_value"] == 1500000.0
    assert "tds_total" in fields
    assert fields["tds_total"]["normalized_value"] == 97500.0


def test_password_protected_pdf_handling():
    pwd_pdf_path = SAMPLES_DIR / "sample_password_protected.pdf"
    assert pwd_pdf_path.exists()

    with open(pwd_pdf_path, "rb") as f:
        data = f.read()

    # 1. Detect password protection
    assert is_pdf_password_protected(data) is True

    # 2. Extract without password raises ValueError
    with pytest.raises(ValueError) as excinfo:
        extract_text_from_pdf(data, password=None)
    assert "password required" in str(excinfo.value).lower()

    # 3. Extract with wrong password raises ValueError
    with pytest.raises(ValueError):
        extract_text_from_pdf(data, password="WRONG_PASSWORD")

    # 4. Extract with correct password succeeds
    success, pages, text = extract_text_from_pdf(data, password="TEST1234")
    assert success is True
    assert "CONFIDENTIAL TAX DOCUMENT" in text


def test_bank_statement_csv_parsing():
    csv_path = SAMPLES_DIR / "sample_bank_statement.csv"
    assert csv_path.exists()

    with open(csv_path, "rb") as f:
        data = f.read()

    success, rows, summary = parse_tabular_file(data, "text/csv")
    assert success is True
    assert len(rows) >= 10
    assert any("INFOSYS" in str(r.get("Description")) for r in rows)
    assert any("Rent" in str(r.get("Description")) for r in rows)
