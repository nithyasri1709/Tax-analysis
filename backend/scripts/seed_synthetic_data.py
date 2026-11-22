"""
Synthetic Data Generator & Seeder
Generates realistic, synthetic Indian tax documents (Salary Slip, Form 16, Bank Statement CSV/XLSX,
Insurance Receipt, Home Loan Statement, Rent Receipt, Donation Receipt, and a Password-Protected PDF).
All names, PANs, employer names, and bank accounts are strictly synthetic and privacy-compliant.
Seeds a default demo taxpayer account: demo.taxpayer@example.com / Password123!
"""

from __future__ import annotations

import io
import os
from pathlib import Path
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import pymupdf as fitz

from app.core.encryption import encrypt_text, mask_pan
from app.core.security import get_password_hash
from app.db.models import Base, FinancialProfile, User
from app.db.session import SessionLocal, init_db
from app.services.documents.storage import save_encrypted_file
from app.services.extraction.pipeline import run_document_extraction_pipeline

SAMPLES_DIR = Path(__file__).parent / "sample_documents"
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)


def create_salary_slip_pdf(filepath: Path) -> None:
    doc = SimpleDocTemplate(str(filepath), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle("T", fontName="Helvetica-Bold", fontSize=14, leading=18, alignment=1)
    sub_style = ParagraphStyle("S", fontName="Helvetica", fontSize=9, leading=12, alignment=1, textColor=colors.HexColor("#475569"))
    body = ParagraphStyle("B", fontName="Helvetica", fontSize=9, leading=12)

    story.append(Paragraph("INFOSYS BHARAT TECHNOLOGIES PRIVATE LIMITED", title_style))
    story.append(Paragraph("Electronics City, Hosur Road, Bengaluru, Karnataka - 560100<br/><b>PAYSLIP FOR THE MONTH OF MARCH 2026</b>", sub_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#0284c7"), spaceAfter=10))

    meta_table = [
        ["Employee Name:", "Aditya Sharma", "Employee ID:", "INFY-884920"],
        ["Designation:", "Lead Software Architect", "PAN:", "ABCDE1234F"],
        ["Bank A/C No:", "992837465012", "IFSC:", "HDFC0001234"],
        ["Days in Month:", "31", "Payable Days:", "31"],
    ]
    t_meta = Table(meta_table, colWidths=[110, 160, 110, 160])
    t_meta.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("PADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 12))

    pay_table = [
        ["Earnings Component", "Amount (₹)", "Deductions Component", "Amount (₹)"],
        ["Basic Salary", "50,000.00", "Provident Fund (EPF)", "6,000.00"],
        ["Dearness Allowance (DA)", "5,000.00", "Professional Tax (PT)", "200.00"],
        ["House Rent Allowance (HRA)", "20,000.00", "Tax Deducted at Source (TDS)", "8,500.00"],
        ["Special Allowance", "50,000.00", "Voluntary NPS Deduction", "4,166.00"],
        ["Gross Earnings", "1,25,000.00", "Total Deductions", "18,866.00"],
    ]
    t_pay = Table(pay_table, colWidths=[150, 120, 150, 120])
    t_pay.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e2e8f0")),
    ]))
    story.append(t_pay)
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>Annualized Gross Salary (12 Months):</b> ₹ 15,00,000.00", body))
    story.append(Paragraph("<b>Net Salary Payable:</b> ₹ 1,06,134.00 (One Lakh Six Thousand One Hundred Thirty Four Only)", body))

    doc.build(story)


def create_form16_pdf(filepath: Path) -> None:
    doc = SimpleDocTemplate(str(filepath), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()

    story.append(Paragraph("FORM NO. 16", ParagraphStyle("H", fontName="Helvetica-Bold", fontSize=14, alignment=1)))
    story.append(Paragraph("[See rule 31(1)(a)]<br/><b>PART B - CERTIFICATE UNDER SECTION 203 OF THE INCOME-TAX ACT, 1961</b>", ParagraphStyle("S", fontName="Helvetica", fontSize=9, alignment=1)))
    story.append(Spacer(1, 10))

    f16_data = [
        ["1. Gross Salary", "", ""],
        ["  (a) Salary as per provisions contained in section 17(1)", "₹ 15,00,000.00", ""],
        ["  (b) Value of perquisites under section 17(2)", "₹ 0.00", ""],
        ["2. Total Gross Salary", "₹ 15,00,000.00", ""],
        ["3. Less: Standard Deduction under section 16(ia)", "₹ 75,000.00", ""],
        ["4. Less: Tax on employment (Professional Tax) under sec 16(iii)", "₹ 2,400.00", ""],
        ["5. Income chargeable under the head 'Salaries'", "₹ 14,22,600.00", ""],
        ["6. Deductions under Chapter VI-A:", "", ""],
        ["  (a) Section 80C (EPF, PPF, Life Insurance, ELSS)", "₹ 1,50,000.00", "(Max ₹1.5L)"],
        ["  (b) Section 80CCD(1B) (NPS voluntary deposit)", "₹ 50,000.00", "(Max ₹50k)"],
        ["  (c) Section 80D (Health Insurance Premium)", "₹ 25,000.00", "(Max ₹25k)"],
        ["7. Total Taxable Income", "₹ 11,97,600.00", ""],
        ["8. Total Tax Deducted at Source (TDS)", "₹ 97,500.00", ""],
    ]
    t = Table(f16_data, colWidths=[280, 140, 120])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("PADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    doc.build(story)


def create_insurance_receipt_pdf(filepath: Path) -> None:
    doc = SimpleDocTemplate(str(filepath), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()

    story.append(Paragraph("HDFC ERGO GENERAL INSURANCE COMPANY LIMITED", ParagraphStyle("H", fontName="Helvetica-Bold", fontSize=13, alignment=1)))
    story.append(Paragraph("<b>PREMIUM RECEIPT - SECTION 80D CERTIFICATE</b>", ParagraphStyle("S", fontName="Helvetica-Bold", fontSize=10, alignment=1, textColor=colors.HexColor("#1e3a8a"))))
    story.append(Spacer(1, 10))

    data = [
        ["Policy Number:", "2825-9948-1102-00", "Policy Type:", "my:Health Suraksha Family Floater"],
        ["Insured Proposer:", "Aditya Sharma", "Insured Persons:", "Self (32 Yrs), Spouse (30 Yrs)"],
        ["Period of Insurance:", "01-Apr-2025 to 31-Mar-2026", "Sum Assured:", "₹ 15,00,000.00"],
        ["Net Premium:", "₹ 21,186.44", "GST (18%):", "₹ 3,813.56"],
        ["Total Premium Paid:", "₹ 25,000.00", "Payment Mode:", "Net Banking (Non-Cash)"],
    ]
    t = Table(data, colWidths=[130, 140, 130, 140])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("PADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))
    story.append(Paragraph("<i>This is to certify that the premium of ₹25,000.00 was paid via non-cash banking mode, eligible for tax deduction under Section 80D of the Income-tax Act, 1961.</i>", ParagraphStyle("I", fontName="Helvetica-Oblique", fontSize=8.5)))
    doc.build(story)


def create_home_loan_pdf(filepath: Path) -> None:
    doc = SimpleDocTemplate(str(filepath), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()

    story.append(Paragraph("STATE BANK OF INDIA - RACPC BENGALURU", ParagraphStyle("H", fontName="Helvetica-Bold", fontSize=13, alignment=1)))
    story.append(Paragraph("<b>PROVISIONAL CERTIFICATE OF INTEREST & PRINCIPAL PAID (FY 2025-26)</b>", ParagraphStyle("S", fontName="Helvetica-Bold", fontSize=10, alignment=1)))
    story.append(Spacer(1, 10))

    data = [
        ["Borrower Name:", "Aditya Sharma", "Loan Account No:", "30987654321"],
        ["Property Address:", "Flat 402, Green Glen Heights, Bellandur, Bengaluru", "Occupancy Status:", "Self-Occupied"],
        ["Principal Repaid (Sec 80C):", "₹ 1,20,000.00", "Interest Paid (Sec 24(b)):", "₹ 1,85,000.00"],
    ]
    t = Table(data, colWidths=[140, 130, 140, 130])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("PADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    doc.build(story)


def create_rent_receipt_pdf(filepath: Path) -> None:
    doc = SimpleDocTemplate(str(filepath), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()

    story.append(Paragraph("HOUSE RENT RECEIPT", ParagraphStyle("H", fontName="Helvetica-Bold", fontSize=14, alignment=1)))
    story.append(Spacer(1, 10))

    receipt_text = (
        "Received a sum of <b>₹ 20,000.00</b> (Twenty Thousand Rupees Only) from <b>Aditya Sharma</b> "
        "towards monthly rent for the residential premises situated at: <i>#42, 4th Cross, Koramangala, Bengaluru - 560034</i> "
        "for the month of <b>January 2026</b>.<br/><br/>"
        "<b>Landlord Name:</b> Rajesh Kumar V.<br/>"
        "<b>Landlord PAN:</b> BPNPK9821L<br/>"
        "<b>Annualized Rent:</b> ₹ 2,40,000.00<br/>"
        "Payment Mode: Bank Account Transfer (UPI/IMPS)"
    )
    story.append(Paragraph(receipt_text, ParagraphStyle("B", fontName="Helvetica", fontSize=9.5, leading=15)))
    doc.build(story)


def create_password_protected_pdf(filepath: Path, password: str = "TEST1234") -> None:
    """Creates a password-protected PDF file."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), "CONFIDENTIAL TAX DOCUMENT - PASSWORD PROTECTED", fontsize=14)
    page.insert_text((50, 100), "Gross Salary: ₹ 14,50,000.00\nTDS Deposited: ₹ 88,000.00", fontsize=10)
    # Encrypt PDF
    perm = int(
        fitz.PDF_PERM_ACCESSIBILITY
        | fitz.PDF_PERM_PRINT
        | fitz.PDF_PERM_COPY
        | fitz.PDF_PERM_ANNOTATE
    )
    doc.save(
        str(filepath),
        encryption=fitz.PDF_ENCRYPT_AES_256,
        user_pw=password,
        owner_pw="OWNER9999",
        permissions=perm,
    )
    doc.close()


def create_bank_statement_csv(filepath: Path) -> None:
    transactions = [
        {"Date": "01/04/2025", "Description": "SALARY CREDIT INFOSYS TECH", "Withdrawal (Dr)": "", "Deposit (Cr)": "106134.00", "Balance": "106134.00"},
        {"Date": "05/04/2025", "Description": "UPI/5123/Swiggy order Bangalore", "Withdrawal (Dr)": "650.00", "Deposit (Cr)": "", "Balance": "105484.00"},
        {"Date": "07/04/2025", "Description": "NEFT to Landlord Ramesh Sharma House Rent", "Withdrawal (Dr)": "20000.00", "Deposit (Cr)": "", "Balance": "85484.00"},
        {"Date": "12/04/2025", "Description": "Star Health Insurance renewal premium", "Withdrawal (Dr)": "25000.00", "Deposit (Cr)": "", "Balance": "60484.00"},
        {"Date": "15/04/2025", "Description": "Deposit to SBI PPF Account 1029384756", "Withdrawal (Dr)": "12500.00", "Deposit (Cr)": "", "Balance": "47984.00"},
        {"Date": "20/04/2025", "Description": "Mirae Asset Tax Saver Fund ELSS SIP", "Withdrawal (Dr)": "10000.00", "Deposit (Cr)": "", "Balance": "37984.00"},
        {"Date": "25/04/2025", "Description": "NPS contribution via NSDL CRA payment gateway", "Withdrawal (Dr)": "4166.00", "Deposit (Cr)": "", "Balance": "33818.00"},
        {"Date": "28/04/2025", "Description": "POS/Amazon India purchase electronic", "Withdrawal (Dr)": "3200.00", "Deposit (Cr)": "", "Balance": "30618.00"},
        {"Date": "01/05/2025", "Description": "SALARY CREDIT INFOSYS TECH", "Withdrawal (Dr)": "", "Deposit (Cr)": "106134.00", "Balance": "136752.00"},
        {"Date": "06/05/2025", "Description": "NEFT to Landlord Ramesh Sharma House Rent", "Withdrawal (Dr)": "20000.00", "Deposit (Cr)": "", "Balance": "116752.00"},
        {"Date": "10/05/2025", "Description": "SBI Housing Loan Monthly EMI Repayment", "Withdrawal (Dr)": "25000.00", "Deposit (Cr)": "", "Balance": "91752.00"},
        {"Date": "15/05/2025", "Description": "Deposit to SBI PPF Account 1029384756", "Withdrawal (Dr)": "12500.00", "Deposit (Cr)": "", "Balance": "79252.00"},
        {"Date": "18/05/2025", "Description": "Donation to PM CARES Fund relief contribution", "Withdrawal (Dr)": "5000.00", "Deposit (Cr)": "", "Balance": "74252.00"},
        {"Date": "20/05/2025", "Description": "Mirae Asset Tax Saver Fund ELSS SIP", "Withdrawal (Dr)": "10000.00", "Deposit (Cr)": "", "Balance": "64252.00"},
        {"Date": "22/05/2025", "Description": "Uber trip ride Bangalore", "Withdrawal (Dr)": "420.00", "Deposit (Cr)": "", "Balance": "63832.00"},
        {"Date": "25/05/2025", "Description": "NPS contribution via NSDL CRA payment gateway", "Withdrawal (Dr)": "4166.00", "Deposit (Cr)": "", "Balance": "59666.00"},
    ]
    df = pd.DataFrame(transactions)
    df.to_csv(filepath, index=False)


def seed_database_with_synthetic_user() -> None:
    """Creates default taxpayer user and seeds synthetic profile and documents."""
    init_db()
    db = SessionLocal()

    email = "demo.taxpayer@example.com"
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            hashed_password=get_password_hash("Password123!"),
            full_name="Aditya Sharma",
            dob="1994-06-15",
            age_bracket="regular",
            residential_status="resident",
            state="Karnataka",
            city="Bengaluru",
            is_metro=False,
            employment_type="salaried",
            encrypted_pan=encrypt_text("ABCDE1234F"),
            pan_masked=mask_pan("ABCDE1234F"),
        )
        db.add(user)
        db.flush()

        profile = FinancialProfile(
            user_id=user.id,
            financial_year="2025-26",
            selected_regime="new",
            salary_data={
                "gross_salary": 1500000.0,
                "basic_salary": 600000.0,
                "da_amount": 60000.0,
                "hra_received": 240000.0,
                "rent_paid": 240000.0,
                "professional_tax": 2400.0,
            },
            deductions_data={
                "epf": 72000.0,
                "ppf": 50000.0,
                "elss": 30000.0,
                "80ccd_1b": 50000.0,
                "80ccd_2": 84000.0,
                "health_insurance_self": 25000.0,
                "health_insurance_parents": 25000.0,
                "home_loan_principal": 120000.0,
            },
            house_prop_data={
                "is_self_occupied": True,
                "home_loan_interest": 185000.0,
            },
            taxes_paid_data={
                "tds_salary": 97500.0,
                "advance_tax_q1": 0.0,
                "advance_tax_q2": 0.0,
                "advance_tax_q3": 0.0,
                "advance_tax_q4": 0.0,
            },
            completeness_score=85,
        )
        db.add(profile)
        db.commit()
        print(f"Created demo user: {email} / Password123!")
    else:
        print(f"Demo user already exists: {email}")

    db.close()


def generate_all_samples():
    print("Generating synthetic tax documents in:", SAMPLES_DIR)
    create_salary_slip_pdf(SAMPLES_DIR / "sample_salary_slip.pdf")
    create_form16_pdf(SAMPLES_DIR / "sample_form_16.pdf")
    create_insurance_receipt_pdf(SAMPLES_DIR / "sample_insurance_receipt.pdf")
    create_home_loan_pdf(SAMPLES_DIR / "sample_home_loan_statement.pdf")
    create_rent_receipt_pdf(SAMPLES_DIR / "sample_rent_receipt.pdf")
    create_password_protected_pdf(SAMPLES_DIR / "sample_password_protected.pdf", password="TEST1234")
    create_bank_statement_csv(SAMPLES_DIR / "sample_bank_statement.csv")

    # Generate XLSX as well
    df = pd.read_csv(SAMPLES_DIR / "sample_bank_statement.csv")
    df.to_excel(SAMPLES_DIR / "sample_bank_statement.xlsx", index=False)

    print("Sample synthetic documents generated successfully!")
    seed_database_with_synthetic_user()


if __name__ == "__main__":
    generate_all_samples()
