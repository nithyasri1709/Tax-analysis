/**
 * INTELLIGENT TAX ASSISTANT - TypeScript Data Contracts
 * Fully aligned with Backend FastAPI and Pure-Python Tax Engine
 */

export interface User {
  id: string;
  email: string;
  full_name: string;
  dob?: string | null;
  age_bracket: 'regular' | 'senior' | 'super_senior';
  residential_status: string;
  state?: string | null;
  city?: string | null;
  is_metro: boolean;
  employment_type: 'salaried' | 'pensioner' | 'self_employed_basic';
  pan_masked?: string | null;
  is_active: boolean;
  created_at: string;
}

export interface ExtractedField {
  id: string;
  document_id: string;
  field_key: string;
  field_label: string;
  field_value: string;
  normalized_value?: number | null;
  confidence: number;
  source_page?: number | null;
  source_snippet?: string | null;
  status: 'auto' | 'user_edited' | 'confirmed';
  conflict_flag: boolean;
  conflict_details?: Record<string, any> | null;
  created_at: string;
}

export interface DocumentItem {
  id: string;
  financial_year: string;
  file_name: string;
  file_type: string;
  file_size: number;
  doc_type: string;
  status: 'PENDING' | 'PROCESSING' | 'PROCESSED' | 'ERROR';
  is_password_protected: boolean;
  error_message?: string | null;
  created_at: string;
  extracted_fields: ExtractedField[];
}

export interface Transaction {
  id: string;
  document_id?: string | null;
  financial_year: string;
  date: string;
  description: string;
  amount: number;
  transaction_type: 'debit' | 'credit';
  category: string;
  confidence: number;
  classification_source: string;
  is_potentially_tax_eligible: boolean;
  applicable_section?: string | null;
  deduction_status: 'unclaimed' | 'eligible' | 'claimed' | 'rejected';
  proof_document_id?: string | null;
  is_duplicate: boolean;
  parent_transaction_id?: string | null;
  created_at: string;
}

export interface CategoryTotalItem {
  category: string;
  total_amount: number;
  count: number;
  tax_eligible_amount: number;
  applicable_section?: string | null;
}

export interface FinancialProfile {
  id: string;
  financial_year: string;
  selected_regime: 'new' | 'old';
  salary_data: Record<string, any>;
  house_prop_data: Record<string, any>;
  other_sources_data: Record<string, any>;
  capital_gains_data: Record<string, any>;
  deductions_data: Record<string, any>;
  taxes_paid_data: Record<string, any>;
  completeness_score: number;
  user_demographics: {
    full_name: string;
    dob?: string | null;
    age_bracket: string;
    employment_type: string;
    is_metro: boolean;
    residential_status: string;
    pan_masked?: string | null;
  };
}

export interface SlabBreakdown {
  slab: string;
  taxable_in_slab: number;
  rate: string;
  tax: number;
}

export interface TaxCalculationResult {
  financial_year: string;
  regime: 'new' | 'old';
  statutory_basis?: string;
  statutory_act?: string;
  gross_total_income: number;
  total_deductions_allowed?: number;
  total_chapter_vi_a_deductions?: number;
  taxable_income?: number;
  taxable_total_income?: number;
  standard_deduction?: number;
  base_tax?: number;
  slab_tax?: number;
  rebate_87a: number;
  tax_after_rebate?: number;
  surcharge?: number;
  net_surcharge?: number;
  cess?: number;
  health_and_education_cess?: number;
  total_tax_liability?: number;
  gross_tax_liability?: number;
  net_tax_payable?: number;
  balance_payable_or_refund?: number;
  slab_breakdown: any[];
  calculation_breakdown?: any[];
  advance_tax_schedule?: Array<{
    due_date: string;
    percentage: number;
    cumulative_amount: number;
  }>;
  interest_234?: {
    interest_234a: number;
    interest_234b: number;
    interest_234c: number;
    total_interest: number;
  };
  statutory_interest_234abc?: number;
  audit_trace?: Array<{
    step: string;
    description: string;
    amount?: number | null;
    rule_applied?: string | null;
  }>;
  disclaimer: string;
}

export interface RegimeComparisonResult {
  financial_year: string;
  old_regime: TaxCalculationResult;
  new_regime: TaxCalculationResult;
  recommended_regime: 'new' | 'old';
  tax_difference: number;
  tax_savings: number;
  break_even_deduction: number;
  reason: string;
  statutory_basis: string;
  disclaimer: string;
}

export interface MissedDeductionItem {
  section_1961: string;
  section_2025?: string | null;
  name: string;
  category: string;
  max_limit: number;
  current_claimed: number;
  potential_additional: number;
  estimated_tax_savings: number;
  status: 'ELIGIBLE' | 'POTENTIAL' | 'CLAIMED' | 'NOT_ELIGIBLE';
  condition_description: string;
  action_needed: string;
  regime_availability: string;
}

export interface ClarifyingQuestion {
  id: string;
  question: string;
  field_target: string;
  section: string;
  input_type: 'boolean' | 'number' | 'select';
  options?: string[];
  help_text: string;
}

export interface MissedDeductionsResponse {
  financial_year: string;
  selected_regime: string;
  total_potential_tax_savings: number;
  missed_deductions: MissedDeductionItem[];
  clarifying_questions: ClarifyingQuestion[];
  disclaimer: string;
}

export interface WhatIfResponse {
  financial_year: string;
  regime: string;
  baseline_tax: number;
  simulated_tax: number;
  tax_saved: number;
  baseline_deductions: number;
  simulated_deductions: number;
  breakdown: Record<string, any>;
  disclaimer: string;
}

export interface InvestmentAnalysisResponse {
  financial_year: string;
  regime: string;
  regime_note: string;
  section_80c_meter: {
    total_invested: number;
    cap: number;
    allowed: number;
    remaining_headroom: number;
    utilization_pct: number;
    components: Record<string, number>;
  };
  section_80ccd_1b_nps: {
    invested: number;
    cap: number;
    allowed: number;
    remaining_headroom: number;
  };
  section_80d_health: {
    self_family: number;
    parents: number;
    preventive_checkup: number;
    cap: number;
    allowed: number;
    remaining_headroom: number;
  };
  section_24b_home_loan_interest: {
    interest_paid: number;
    cap: number;
    allowed: number;
    remaining_headroom: number;
  };
  recommendations: Array<{
    section: string;
    section_2025?: string;
    headroom: number;
    suggestion: string;
  }>;
  disclaimer: string;
}

export interface ReportItem {
  id: string;
  financial_year: string;
  calculation_id?: string | null;
  file_name: string;
  report_summary: Record<string, any>;
  created_at: string;
}

export interface ReconciliationResponse {
  financial_year: string;
  summary: {
    tds_salary_form16: number;
    tds_total_26as: number;
    gross_income_ais: number;
    tds_credit_status: string;
  };
  sources_matched: {
    form_16: boolean;
    form_26as: boolean;
    ais_tis: boolean;
  };
  discrepancies: Array<{
    field: string;
    source_1: string;
    val_1: number;
    source_2: string;
    val_2: number;
    difference: number;
    severity: 'INFO' | 'WARNING' | 'CRITICAL';
    recommendation: string;
  }>;
  notes: string[];
}

export interface AuditLogItem {
  id: string;
  action: string;
  details?: Record<string, any> | null;
  ip_address?: string | null;
  created_at: string;
}

export interface StatutoryRulesResponse {
  financial_year: string;
  metadata: {
    applicable_act: string;
    assessment_year: string;
    last_verified_date: string;
    source_url: string;
  };
  new_regime: Record<string, any>;
  old_regime: Record<string, any>;
  section_mapping?: Record<string, string>;
}
