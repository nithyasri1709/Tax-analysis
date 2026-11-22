# INTELLIGENT TAX ASSISTANT – Smart Tax Planning and Deduction Detection System
## System Architecture Specification

### 1. High-Level Architecture Overview
The Intelligent Tax Assistant is a production-grade, fintech-compliant web platform designed to streamline tax calculation, deduction optimization, and document-backed tax planning for Indian individual taxpayers under both the Income-tax Act, 1961 and the newly enacted Income-tax Act, 2025 (effective 1 April 2026).

```
+-----------------------------------------------------------------------------------+
|                            REACT 18 + TYPESCRIPT SPA                              |
|  - 13-Step Guided Onboarding Wizard              - Side-by-Side Verification UI   |
|  - Dashboard (Income, Deductions, Completeness)  - What-If Tax Simulator          |
|  - Multi-File Drag & Drop Encrypted Uploader     - Old vs New Regime Comparator   |
|  - Expense Categorizer & 80C Meter               - Grounded Q&A Assistant Chat    |
+-----------------------------------------+-----------------------------------------+
                                          | JSON over HTTPS (JWT Bearer Token)
                                          v
+-----------------------------------------------------------------------------------+
|                               FASTAPI BACKEND API                                 |
|  /api/v1/auth          /api/v1/documents       /api/v1/tax          /api/v1/chat  |
|  /api/v1/users         /api/v1/extraction      /api/v1/deductions   /api/v1/admin |
|  /api/v1/transactions  /api/v1/investments     /api/v1/reports      /api/v1/reconc|
+----+--------------------+-----------------------+---------------------+-----------+
     |                    |                       |                     |
     v                    v                       v                     v
+-----------+    +-------------------+    +---------------+    +--------------------+
| SQLALCHEMY|    | DOCUMENT PIPELINE |    | TAX ENGINE    |    | REPORTLAB ENGINE   |
| 2.0 ORM   |    | - PDF/PyMuPDF     |    | Pure Python   |    | - 16-Section PDF   |
| Postgre/  |    | - OCR (Tesseract) |    | Deterministic |    | - Paginated        |
| SQLite    |    | - Hybrid LLM/Regex|    | Slabs/Rebate  |    | - Branded Visuals  |
| Encrypted |    | - Deduplication   |    | Rules JSONs   |    | - Snapshot audit   |
+-----------+    +-------------------+    +---------------+    +--------------------+
```

### 2. Core Architectural Guarantees & Golden Rules
1. **Deterministic Tax Maths**: Zero LLM involvement in computation. Pure Python using Python `Decimal` arithmetic rounded to nearest ₹10 per Section 288A/288B of Income-tax Act.
2. **Configurable Statutory Values**: Slabs, rebates, caps, and section crosswalks loaded from versioned JSON files (`fy2024_25.json`, `fy2025_26.json`, `fy2026_27.json`, `section_mapping.json`).
3. **Dual Tax Regime & Dual Statute Support**:
   - Supports FY 2024-25, FY 2025-26 (AY 2026-27 under Income-tax Act, 1961), and FY 2026-27 (Tax Year 2026-27 under Income-tax Act, 2025).
   - Maps legacy sections (80C, 80D, 80CCD(1B), 24(b), 10(13A)) to new 2025 Act sections.
4. **Explainable Derivations**: Every computed line item yields a trace showing label, formula string, inputs, and final value.
5. **Privacy by Design**:
   - PII (such as PAN) stored with Fernet AES-128-CBC encryption and masked in UI (`ABCDE****F`).
   - Files stored with random UUID names, encrypted at rest.
   - Complete data export and account purge (DPDP compliant).
   - Strict `user_id` scoping across all DB queries with IDOR tests.
6. **Statutory Disclaimer**: Enforced on every response and view: *"Estimate only; not professional tax advice."*
