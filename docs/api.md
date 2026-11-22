# API Contract and Database Schema Specification

## 1. Database Schema (SQLAlchemy 2.0 / PostgreSQL & SQLite)

### Table: `users`
- `id`: UUID (Primary Key, default uuid4)
- `email`: VARCHAR(255) (Unique, Index, Not Null)
- `hashed_password`: VARCHAR(255) (Not Null, bcrypt/argon2)
- `full_name`: VARCHAR(255) (Not Null)
- `dob`: DATE (Nullable, used to calculate exact age for senior brackets)
- `age_bracket`: VARCHAR(32) (regular, senior_60_plus, super_senior_80_plus)
- `residential_status`: VARCHAR(32) (resident, nri, rnor)
- `state`: VARCHAR(100) (Nullable)
- `city`: VARCHAR(100) (Nullable)
- `is_metro`: BOOLEAN (Default False, controls 50% vs 40% HRA limit)
- `employment_type`: VARCHAR(32) (salaried, pensioner, self_employed)
- `encrypted_pan`: TEXT (Nullable, Fernet encrypted)
- `pan_masked`: VARCHAR(16) (Nullable, e.g. ABCDE****F)
- `is_active`: BOOLEAN (Default True)
- `created_at`: TIMESTAMP WITH TIME ZONE
- `updated_at`: TIMESTAMP WITH TIME ZONE

### Table: `refresh_tokens`
- `id`: UUID (Primary Key)
- `user_id`: UUID (Foreign Key -> users.id, ondelete CASCADE)
- `token_hash`: VARCHAR(255) (Unique, Index)
- `expires_at`: TIMESTAMP WITH TIME ZONE
- `is_revoked`: BOOLEAN (Default False)
- `created_at`: TIMESTAMP WITH TIME ZONE

### Table: `financial_profiles`
- `id`: UUID (Primary Key)
- `user_id`: UUID (Foreign Key -> users.id, ondelete CASCADE)
- `financial_year`: VARCHAR(16) (e.g., '2025-26')
- `selected_regime`: VARCHAR(16) (new / old)
- `salary_income`: JSONB (gross, basic, da, hra_received, special_allowance, perquisites, prof_tax, pf_deducted)
- `house_property_income`: JSONB (rent_received, municipal_taxes, home_loan_interest, is_self_occupied)
- `other_sources_income`: JSONB (savings_interest, fd_interest, dividend, other)
- `capital_gains`: JSONB (stcg_equity, ltcg_equity, other)
- `exemptions`: JSONB (hra_claimed, lta_claimed, etc.)
- `deductions`: JSONB (80C, 80CCD1B, 80CCD2, 80D_self, 80D_parents, 80E, 80G, 80TTA, etc.)
- `taxes_paid`: JSONB (tds_salary, tds_other, tcs, advance_tax_q1..q4, self_assessment)
- `completeness_score`: INTEGER (0-100)
- `created_at`, `updated_at`: TIMESTAMP WITH TIME ZONE

### Table: `documents`
- `id`: UUID (Primary Key)
- `user_id`: UUID (Foreign Key -> users.id, ondelete CASCADE)
- `financial_year`: VARCHAR(16)
- `file_name`: VARCHAR(255)
- `file_type`: VARCHAR(64) (MIME type)
- `file_size`: INTEGER
- `storage_path`: VARCHAR(512) (Encrypted storage location)
- `file_hash`: VARCHAR(64) (SHA-256 for duplicate detection)
- `doc_type`: VARCHAR(64) (salary_slip, form_16, bank_statement, investment_proof, etc.)
- `status`: VARCHAR(32) (uploaded, processing, needs_review, confirmed, failed)
- `is_password_protected`: BOOLEAN (Default False)
- `error_message`: TEXT (Nullable)
- `created_at`, `updated_at`: TIMESTAMP WITH TIME ZONE

### Table: `extracted_fields`
- `id`: UUID (Primary Key)
- `document_id`: UUID (Foreign Key -> documents.id, ondelete CASCADE)
- `user_id`: UUID (Foreign Key -> users.id, ondelete CASCADE)
- `field_key`: VARCHAR(64) (e.g. gross_salary, basic_salary, employee_pf)
- `field_label`: VARCHAR(128)
- `field_value`: TEXT
- `normalized_value`: NUMERIC(14, 2)
- `confidence`: NUMERIC(3, 2) (0.00 to 1.00)
- `source_page`: INTEGER (Nullable)
- `source_snippet`: TEXT (Nullable)
- `status`: VARCHAR(32) (auto, user_edited, confirmed)
- `conflict_flag`: BOOLEAN (Default False)
- `conflict_details`: JSONB (Nullable)
- `created_at`, `updated_at`: TIMESTAMP WITH TIME ZONE

### Table: `transactions`
- `id`: UUID (Primary Key)
- `user_id`: UUID (Foreign Key -> users.id, ondelete CASCADE)
- `document_id`: UUID (Foreign Key -> documents.id, Nullable)
- `financial_year`: VARCHAR(16)
- `date`: DATE
- `description`: TEXT
- `amount`: NUMERIC(14, 2)
- `transaction_type`: VARCHAR(16) (debit, credit)
- `category`: VARCHAR(64) (House Rent, Health Insurance, ELSS, PPF, etc.)
- `confidence`: NUMERIC(3, 2)
- `classification_source`: VARCHAR(16) (rule, ml, llm, user)
- `is_potentially_tax_eligible`: BOOLEAN
- `applicable_section`: VARCHAR(32) (Nullable)
- `deduction_status`: VARCHAR(32) (claimed, needs_proof, ineligible, ignored)
- `proof_document_id`: UUID (Nullable)
- `is_duplicate`: BOOLEAN (Default False)
- `parent_transaction_id`: UUID (Nullable, for split transactions)
- `created_at`: TIMESTAMP WITH TIME ZONE

### Table: `tax_calculations`
- `id`: UUID (Primary Key)
- `user_id`: UUID (Foreign Key -> users.id, ondelete CASCADE)
- `financial_year`: VARCHAR(16)
- `rule_config_version`: VARCHAR(64)
- `inputs_snapshot`: JSONB
- `old_regime_result`: JSONB
- `new_regime_result`: JSONB
- `recommended_regime`: VARCHAR(16) (old / new)
- `tax_difference`: NUMERIC(14, 2)
- `break_even_deductions`: NUMERIC(14, 2)
- `created_at`: TIMESTAMP WITH TIME ZONE

### Table: `reports`
- `id`: UUID (Primary Key)
- `user_id`: UUID (Foreign Key -> users.id, ondelete CASCADE)
- `financial_year`: VARCHAR(16)
- `calculation_id`: UUID (Foreign Key -> tax_calculations.id)
- `file_name`: VARCHAR(255)
- `storage_path`: VARCHAR(512)
- `report_summary`: JSONB
- `created_at`: TIMESTAMP WITH TIME ZONE

### Table: `audit_logs`
- `id`: UUID (Primary Key)
- `user_id`: UUID (Foreign Key -> users.id, ondelete CASCADE)
- `action`: VARCHAR(64) (DOCUMENT_UPLOAD, FIELD_EDIT, TAX_CALCULATE, REPORT_GENERATE, DATA_PURGE)
- `details`: JSONB
- `ip_address`: VARCHAR(45)
- `created_at`: TIMESTAMP WITH TIME ZONE

---

## 2. API Contract Endpoints

### Auth & User (`/api/v1/auth`, `/api/v1/users`)
- `POST /api/v1/auth/register` -> `{ email, password, full_name, age_bracket, residential_status, is_metro, employment_type }` -> Returns `{ access_token, refresh_token, user }`
- `POST /api/v1/auth/login` -> `{ email, password }` -> Returns `{ access_token, refresh_token, user }`
- `POST /api/v1/auth/refresh` -> `{ refresh_token }` -> Returns `{ access_token, refresh_token }`
- `POST /api/v1/auth/logout` -> `{ refresh_token }` -> Revokes token
- `GET /api/v1/users/me` -> Current user profile
- `PUT /api/v1/users/me` -> Update user profile
- `PUT /api/v1/users/me/pan` -> `{ pan }` -> Encrypts & returns masked PAN
- `DELETE /api/v1/users/me` -> Purges user, all documents, extractions, transactions, reports
- `GET /api/v1/users/me/export` -> Complete JSON export of all personal data

### Documents & Extraction (`/api/v1/documents`, `/api/v1/extraction`)
- `POST /api/v1/documents/upload` -> Multipart form (files, financial_year, doc_type, password) -> Returns list of document records
- `GET /api/v1/documents` -> Query `?financial_year=2025-26` -> Returns list of documents
- `GET /api/v1/documents/{id}/file` -> Streaming decrypted file bytes
- `DELETE /api/v1/documents/{id}` -> Deletes document, file, extracted fields
- `POST /api/v1/extraction/{id}/process` -> Runs async OCR/parser/classifier
- `GET /api/v1/extraction/{id}/fields` -> Returns extracted fields with confidence & source snippets
- `PUT /api/v1/extraction/fields/{field_id}` -> Edit field value
- `POST /api/v1/extraction/{id}/confirm` -> Mark all fields as confirmed and sync to profile

### Transactions & Categorisation (`/api/v1/transactions`)
- `GET /api/v1/transactions` -> Filter by FY, category, search, deduction_status
- `PUT /api/v1/transactions/{id}` -> Update category, notes, deduction status
- `POST /api/v1/transactions/bulk-categorise` -> Update category for description pattern
- `POST /api/v1/transactions/{id}/split` -> Split transaction into multiple lines
- `GET /api/v1/transactions/category-totals` -> Aggregated totals by category and tax section

### Tax Engine & Comparison (`/api/v1/tax`)
- `POST /api/v1/tax/calculate` -> `{ financial_year, regime, income_data, deductions_data, taxes_paid }` -> Pure Python deterministic computation with step-by-step breakdown
- `GET /api/v1/tax/compare` -> Side-by-side Old vs New comparison, break-even deduction threshold
- `POST /api/v1/tax/hra-calculator` -> `{ basic, da, hra_received, rent_paid, is_metro }` -> Step-by-step least-of-three derivation
- `GET /api/v1/tax/rules/{fy}` -> Slabs, standard deduction, rebate threshold, section crosswalk

### Missed Deductions Advisor & What-If Simulator (`/api/v1/deductions`)
- `GET /api/v1/deductions/missed` -> Detected gaps (80C, 80CCD, 80D, 24b, HRA) with tax savings at marginal rate
- `POST /api/v1/deductions/answer-question` -> Submit answers to clarify potential deductions
- `POST /api/v1/deductions/what-if` -> Live recalculation slider endpoint

### Reports (`/api/v1/reports`)
- `POST /api/v1/reports/generate` -> Generates 16-section ReportLab PDF
- `GET /api/v1/reports` -> List user's reports
- `GET /api/v1/reports/{id}/download` -> Download generated PDF

### Chat & Reconciliation (`/api/v1/chat`, `/api/v1/reconciliation`)
- `POST /api/v1/chat/ask` -> Tax-grounded Q&A assistant explaining numbers with citations
- `GET /api/v1/reconciliation` -> Cross-verification of TDS & income between Form 16, 26AS, and AIS
