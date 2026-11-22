import React, { useState, useEffect } from 'react';
import { useTax } from '../context/TaxContext';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/client';
import { formatINR } from '../components/common/CurrencyDisplay';
import { useNavigate } from 'react-router-dom';
import {
  Check,
  ChevronRight,
  ChevronLeft,
  Save,
  Sparkles,
  Calculator,
  Compass,
  User,
  Briefcase,
  Wallet,
  Home,
  PiggyBank,
  HeartPulse,
  Award,
  Gift,
  Building,
  CreditCard,
  FileCheck,
  CheckCircle,
} from 'lucide-react';

export const OnboardingWizardPage: React.FC = () => {
  const { financialYear, profile, updateProfileData, showToast, refreshAll } = useTax();
  const { user, refreshUser } = useAuth();
  const navigate = useNavigate();

  const [currentStep, setCurrentStep] = useState<number>(1);
  const [isSaving, setIsSaving] = useState<boolean>(false);

  // Wizard state mapped to financial profile
  const [formData, setFormData] = useState({
    // Step 1: Demographics
    full_name: user?.full_name || '',
    dob: user?.dob || '',
    age_bracket: user?.age_bracket || 'regular',
    residential_status: user?.residential_status || 'resident',
    is_metro: user?.is_metro || false,
    pan: user?.pan_masked || '',

    // Step 2: Employment
    employment_type: user?.employment_type || 'salaried',
    employer_name: 'Acme Technologies Ltd',

    // Step 3: Salary Components
    gross_salary: 1500000,
    basic_salary: 600000,
    da_amount: 120000,
    hra_received: 240000,
    special_allowance: 400000,
    professional_tax: 2400,
    annual_rent_paid: 300000,

    // Step 4: House Property
    rental_income: 0,
    municipal_taxes: 0,
    home_loan_interest_sop: 180000,
    home_loan_interest_letout: 0,

    // Step 5: Other Sources
    savings_interest: 18000,
    fd_interest: 45000,
    dividend_income: 12000,
    other_income: 0,

    // Step 6: 80C Investments
    epf: 72000,
    ppf: 50000,
    elss: 40000,
    life_insurance: 25000,
    home_loan_principal: 60000,
    tuition_fees: 0,

    // Step 7: 80D Health Insurance
    health_insurance_self: 22000,
    health_insurance_parents: 30000,
    parents_senior: true,
    preventive_health_checkup: 5000,

    // Step 8: 80CCD NPS
    nps_80ccd_1b: 50000,
    nps_80ccd_2: 60000,

    // Step 9: 80G Donations
    donations_100_pm: 10000,
    donations_50_qualifying: 0,

    // Step 10: Loans (Education Loan Interest 80E)
    education_loan_interest_80e: 0,

    // Step 11: TDS & Taxes Paid
    tds_salary: 120000,
    tds_other: 6300,
    advance_tax_paid: 0,
    self_assessment_tax_paid: 0,
  });

  useEffect(() => {
    if (profile) {
      const sal = profile.salary_data || {};
      const hp = profile.house_prop_data || {};
      const os = profile.other_sources_data || {};
      const ded = profile.deductions_data || {};
      const tp = profile.taxes_paid_data || {};

      setFormData((prev) => ({
        ...prev,
        gross_salary: sal.gross_salary ?? prev.gross_salary,
        basic_salary: sal.basic_salary ?? prev.basic_salary,
        da_amount: sal.da_amount ?? prev.da_amount,
        hra_received: sal.hra_received ?? prev.hra_received,
        special_allowance: sal.special_allowance ?? prev.special_allowance,
        professional_tax: sal.professional_tax ?? prev.professional_tax,
        annual_rent_paid: sal.annual_rent_paid ?? prev.annual_rent_paid,

        rental_income: hp.annual_rent_received ?? prev.rental_income,
        municipal_taxes: hp.municipal_taxes_paid ?? prev.municipal_taxes,
        home_loan_interest_sop: hp.interest_self_occupied ?? prev.home_loan_interest_sop,
        home_loan_interest_letout: hp.interest_let_out ?? prev.home_loan_interest_letout,

        savings_interest: os.savings_interest ?? prev.savings_interest,
        fd_interest: os.fd_interest ?? prev.fd_interest,
        dividend_income: os.dividend_income ?? prev.dividend_income,
        other_income: os.other_income ?? prev.other_income,

        epf: ded.epf ?? prev.epf,
        ppf: ded.ppf ?? prev.ppf,
        elss: ded.elss ?? prev.elss,
        life_insurance: ded.life_insurance ?? prev.life_insurance,
        home_loan_principal: ded.home_loan_principal ?? prev.home_loan_principal,
        tuition_fees: ded.tuition_fees ?? prev.tuition_fees,

        health_insurance_self: ded.health_insurance_self ?? prev.health_insurance_self,
        health_insurance_parents: ded.health_insurance_parents ?? prev.health_insurance_parents,
        parents_senior: ded.parents_senior ?? prev.parents_senior,
        preventive_health_checkup: ded.preventive_health_checkup ?? prev.preventive_health_checkup,

        nps_80ccd_1b: ded["80ccd_1b"] ?? prev.nps_80ccd_1b,
        nps_80ccd_2: ded["80ccd_2"] ?? prev.nps_80ccd_2,
        donations_100_pm: ded["80g_100_pm"] ?? prev.donations_100_pm,
        education_loan_interest_80e: ded["80e_education_interest"] ?? prev.education_loan_interest_80e,

        tds_salary: tp.tds_salary ?? prev.tds_salary,
        tds_other: tp.tds_other ?? prev.tds_other,
        advance_tax_paid: tp.advance_tax ?? prev.advance_tax_paid,
      }));
    }
  }, [profile]);

  const steps = [
    { id: 1, title: 'Demographics', icon: User },
    { id: 2, title: 'Employment', icon: Briefcase },
    { id: 3, title: 'Salary & HRA', icon: Wallet },
    { id: 4, title: 'House Property', icon: Home },
    { id: 5, title: 'Other Income', icon: PiggyBank },
    { id: 6, title: '80C Investments', icon: Award },
    { id: 7, title: 'Health 80D', icon: HeartPulse },
    { id: 8, title: 'NPS 80CCD', icon: Sparkles },
    { id: 9, title: 'Donations 80G', icon: Gift },
    { id: 10, title: 'Loan Interest', icon: Building },
    { id: 11, title: 'TDS & Taxes', icon: CreditCard },
    { id: 12, title: 'AIS / Form 16 Check', icon: FileCheck },
    { id: 13, title: 'Review & Compute', icon: Calculator },
  ];

  const handleFieldChange = (key: string, value: any) => {
    setFormData((prev) => ({ ...prev, [key]: value }));
  };

  const handleSaveProgress = async () => {
    setIsSaving(true);
    try {
      await updateProfileData({
        salary_data: {
          gross_salary: Number(formData.gross_salary),
          basic_salary: Number(formData.basic_salary),
          da_amount: Number(formData.da_amount),
          hra_received: Number(formData.hra_received),
          special_allowance: Number(formData.special_allowance),
          professional_tax: Number(formData.professional_tax),
          annual_rent_paid: Number(formData.annual_rent_paid),
        },
        house_prop_data: {
          annual_rent_received: Number(formData.rental_income),
          municipal_taxes_paid: Number(formData.municipal_taxes),
          interest_self_occupied: Number(formData.home_loan_interest_sop),
          interest_let_out: Number(formData.home_loan_interest_letout),
        },
        other_sources_data: {
          savings_interest: Number(formData.savings_interest),
          fd_interest: Number(formData.fd_interest),
          dividend_income: Number(formData.dividend_income),
          other_income: Number(formData.other_income),
        },
        deductions_data: {
          epf: Number(formData.epf),
          ppf: Number(formData.ppf),
          elss: Number(formData.elss),
          life_insurance: Number(formData.life_insurance),
          home_loan_principal: Number(formData.home_loan_principal),
          tuition_fees: Number(formData.tuition_fees),
          health_insurance_self: Number(formData.health_insurance_self),
          health_insurance_parents: Number(formData.health_insurance_parents),
          parents_senior: Boolean(formData.parents_senior),
          preventive_health_checkup: Number(formData.preventive_health_checkup),
          "80ccd_1b": Number(formData.nps_80ccd_1b),
          "80ccd_2": Number(formData.nps_80ccd_2),
          "80g_100_pm": Number(formData.donations_100_pm),
          "80e_education_interest": Number(formData.education_loan_interest_80e),
        },
        taxes_paid_data: {
          tds_salary: Number(formData.tds_salary),
          tds_other: Number(formData.tds_other),
          advance_tax: Number(formData.advance_tax_paid),
        },
      });

      // Update user demographics if in Step 1
      if (currentStep === 1) {
        await api.users.updateMe({
          full_name: formData.full_name,
          dob: formData.dob || undefined,
          age_bracket: formData.age_bracket as any,
          is_metro: formData.is_metro,
        });
        await refreshUser();
      }

      showToast('Wizard progress saved successfully!', 'success');
    } catch (err: any) {
      showToast(err.message || 'Failed to save progress.', 'error');
    } finally {
      setIsSaving(false);
    }
  };

  const handleNext = async () => {
    await handleSaveProgress();
    if (currentStep < 13) {
      setCurrentStep((prev) => prev + 1);
    } else {
      navigate('/calculation');
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep((prev) => prev - 1);
    }
  };

  return (
    <div className="space-y-6">
      {/* Wizard Header */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1 rounded bg-indigo-100 text-indigo-700">
              <Compass className="w-5 h-5" />
            </span>
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">
              Guided 13-Step Tax Onboarding Wizard
            </h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Step {currentStep} of 13: <strong>{steps[currentStep - 1].title}</strong> • Financial Year {financialYear}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleSaveProgress}
            disabled={isSaving}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg transition-colors cursor-pointer"
          >
            <Save className="w-3.5 h-3.5" />
            <span>{isSaving ? 'Saving...' : 'Save & Resume Later'}</span>
          </button>
        </div>
      </div>

      {/* Stepper Pills / Progress */}
      <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-2xs overflow-x-auto">
        <div className="flex items-center justify-between min-w-[800px] gap-1">
          {steps.map((s) => {
            const isCompleted = s.id < currentStep;
            const isCurrent = s.id === currentStep;
            const StepIcon = s.icon;

            return (
              <button
                key={s.id}
                onClick={() => setCurrentStep(s.id)}
                className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                  isCurrent
                    ? 'bg-indigo-600 text-white shadow-xs'
                    : isCompleted
                    ? 'bg-emerald-50 text-emerald-700 border border-emerald-200 hover:bg-emerald-100'
                    : 'text-slate-400 hover:text-slate-700 hover:bg-slate-100'
                }`}
              >
                {isCompleted ? (
                  <Check className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                ) : (
                  <StepIcon className="w-3.5 h-3.5 shrink-0" />
                )}
                <span className="whitespace-nowrap">{s.id}. {s.title}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Step Form Container */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-2xs">
        {/* Step 1: Demographics */}
        {currentStep === 1 && (
          <div className="space-y-4 max-w-2xl">
            <h2 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-2">
              Taxpayer Demographics & Tax Residency
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Full Legal Name</label>
                <input
                  type="text"
                  value={formData.full_name}
                  onChange={(e) => handleFieldChange('full_name', e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Date of Birth</label>
                <input
                  type="date"
                  value={formData.dob}
                  onChange={(e) => handleFieldChange('dob', e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Age Bracket</label>
                <select
                  value={formData.age_bracket}
                  onChange={(e) => handleFieldChange('age_bracket', e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="regular">Below 60 Years (General Taxpayer)</option>
                  <option value="senior">60 to 79 Years (Senior Citizen - ₹3L Exemption)</option>
                  <option value="super_senior">80 Years & Above (Super Senior - ₹5L Exemption)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Residential Status</label>
                <select
                  value={formData.residential_status}
                  onChange={(e) => handleFieldChange('residential_status', e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="resident">Resident Indian</option>
                  <option value="nri">Non-Resident Indian (NRI)</option>
                </select>
              </div>
            </div>

            <div className="flex items-center justify-between p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs">
              <div>
                <p className="font-semibold text-slate-800">Metro City Residence</p>
                <p className="text-[11px] text-slate-500">
                  Residing in Delhi, Mumbai, Kolkata, or Chennai entitles you to 50% basic salary cap for Section 10(13A) HRA exemption (instead of 40%).
                </p>
              </div>
              <input
                type="checkbox"
                checked={formData.is_metro}
                onChange={(e) => handleFieldChange('is_metro', e.target.checked)}
                className="w-5 h-5 text-indigo-600 rounded"
              />
            </div>
          </div>
        )}

        {/* Step 2: Employment */}
        {currentStep === 2 && (
          <div className="space-y-4 max-w-2xl">
            <h2 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-2">
              Employment Details & Standard Deduction
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Employment Type</label>
                <select
                  value={formData.employment_type}
                  onChange={(e) => handleFieldChange('employment_type', e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="salaried">Salaried Individual</option>
                  <option value="pensioner">Pensioner</option>
                  <option value="self_employed_basic">Self-Employed / Freelancer</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Employer Name</label>
                <input
                  type="text"
                  value={formData.employer_name}
                  onChange={(e) => handleFieldChange('employer_name', e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>

            <div className="p-3 bg-indigo-50 border border-indigo-200 rounded-lg text-xs text-indigo-800">
              <strong>Statutory Benefit:</strong> Salaried individuals automatically receive the statutory standard deduction (₹75,000 under the New Regime for FY 2025-26 & FY 2026-27, and ₹50,000 under the Old Regime).
            </div>
          </div>
        )}

        {/* Step 3: Salary Components & HRA */}
        {currentStep === 3 && (
          <div className="space-y-4 max-w-2xl">
            <h2 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-2">
              Salary Breakup & Rent Paid for HRA (Section 10(13A))
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Gross Salary (Per Annum)</label>
                <input
                  type="number"
                  value={formData.gross_salary}
                  onChange={(e) => handleFieldChange('gross_salary', e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Basic Salary (Annual)</label>
                <input
                  type="number"
                  value={formData.basic_salary}
                  onChange={(e) => handleFieldChange('basic_salary', e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Dearness Allowance (DA)</label>
                <input
                  type="number"
                  value={formData.da_amount}
                  onChange={(e) => handleFieldChange('da_amount', e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">HRA Received from Employer</label>
                <input
                  type="number"
                  value={formData.hra_received}
                  onChange={(e) => handleFieldChange('hra_received', e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Total Annual Rent Paid</label>
                <input
                  type="number"
                  value={formData.annual_rent_paid}
                  onChange={(e) => handleFieldChange('annual_rent_paid', e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Professional Tax Paid</label>
                <input
                  type="number"
                  value={formData.professional_tax}
                  onChange={(e) => handleFieldChange('professional_tax', e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 font-mono"
                />
              </div>
            </div>
          </div>
        )}

        {/* Step 4: House Property */}
        {currentStep === 4 && (
          <div className="space-y-4 max-w-2xl">
            <h2 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-2">
              Income / Loss from House Property (Section 24(b))
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Home Loan Interest (Self Occupied)</label>
                <input
                  type="number"
                  value={formData.home_loan_interest_sop}
                  onChange={(e) => handleFieldChange('home_loan_interest_sop', e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 font-mono"
                />
                <span className="text-[10px] text-slate-400">Capped at ₹2,00,000 under Old Regime</span>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Rental Income Received (Let Out)</label>
                <input
                  type="number"
                  value={formData.rental_income}
                  onChange={(e) => handleFieldChange('rental_income', e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Municipal Taxes Paid</label>
                <input
                  type="number"
                  value={formData.municipal_taxes}
                  onChange={(e) => handleFieldChange('municipal_taxes', e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Home Loan Interest (Let Out)</label>
                <input
                  type="number"
                  value={formData.home_loan_interest_letout}
                  onChange={(e) => handleFieldChange('home_loan_interest_letout', e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 font-mono"
                />
              </div>
            </div>
          </div>
        )}

        {/* Step 5: Other Sources */}
        {currentStep === 5 && (
          <div className="space-y-4 max-w-2xl">
            <h2 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-2">
              Income from Other Sources (Interest & Dividends)
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Savings Account Interest (80TTA/TTB)</label>
                <input
                  type="number"
                  value={formData.savings_interest}
                  onChange={(e) => handleFieldChange('savings_interest', e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Fixed Deposit (FD) Interest</label>
                <input
                  type="number"
                  value={formData.fd_interest}
                  onChange={(e) => handleFieldChange('fd_interest', e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Dividend Income</label>
                <input
                  type="number"
                  value={formData.dividend_income}
                  onChange={(e) => handleFieldChange('dividend_income', e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Other Taxable Income</label>
                <input
                  type="number"
                  value={formData.other_income}
                  onChange={(e) => handleFieldChange('other_income', e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 font-mono"
                />
              </div>
            </div>
          </div>
        )}

        {/* Step 6: 80C Investments */}
        {currentStep === 6 && (
          <div className="space-y-4 max-w-2xl">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <h2 className="text-sm font-bold text-slate-900">
                Section 80C Investments (Combined ₹1,50,000 Cap)
              </h2>
              <span className="text-xs font-semibold text-indigo-700">
                Sum: {formatINR(
                  Number(formData.epf) +
                    Number(formData.ppf) +
                    Number(formData.elss) +
                    Number(formData.life_insurance) +
                    Number(formData.home_loan_principal) +
                    Number(formData.tuition_fees)
                )}
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Employee PF (EPF)</label>
                <input
                  type="number"
                  value={formData.epf}
                  onChange={(e) => handleFieldChange('epf', e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Public Provident Fund (PPF)</label>
                <input
                  type="number"
                  value={formData.ppf}
                  onChange={(e) => handleFieldChange('ppf', e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">ELSS Mutual Funds</label>
                <input
                  type="number"
                  value={formData.elss}
                  onChange={(e) => handleFieldChange('elss', e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Life Insurance Premium</label>
                <input
                  type="number"
                  value={formData.life_insurance}
                  onChange={(e) => handleFieldChange('life_insurance', e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Home Loan Principal Repayment</label>
                <input
                  type="number"
                  value={formData.home_loan_principal}
                  onChange={(e) => handleFieldChange('home_loan_principal', e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Children Tuition Fees</label>
                <input
                  type="number"
                  value={formData.tuition_fees}
                  onChange={(e) => handleFieldChange('tuition_fees', e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 font-mono"
                />
              </div>
            </div>
          </div>
        )}

        {/* Step 7: 80D Health Insurance */}
        {currentStep === 7 && (
          <div className="space-y-4 max-w-2xl">
            <h2 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-2">
              Section 80D Health Insurance Premiums
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Self & Family Premium</label>
                <input
                  type="number"
                  value={formData.health_insurance_self}
                  onChange={(e) => handleFieldChange('health_insurance_self', e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 font-mono"
                />
                <span className="text-[10px] text-slate-400">Limit: ₹25,000 (₹50k if senior)</span>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Parents Health Insurance Premium</label>
                <input
                  type="number"
                  value={formData.health_insurance_parents}
                  onChange={(e) => handleFieldChange('health_insurance_parents', e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 font-mono"
                />
                <span className="text-[10px] text-slate-400">Limit: ₹25,000 (₹50k if parents senior)</span>
              </div>

              <div className="sm:col-span-2 flex items-center justify-between p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs">
                <div>
                  <p className="font-semibold text-slate-800">Parents are Senior Citizens (60+ years)</p>
                  <p className="text-[11px] text-slate-500">Increases parents deduction cap from ₹25,000 to ₹50,000.</p>
                </div>
                <input
                  type="checkbox"
                  checked={formData.parents_senior}
                  onChange={(e) => handleFieldChange('parents_senior', e.target.checked)}
                  className="w-5 h-5 text-indigo-600 rounded"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Preventive Health Checkup</label>
                <input
                  type="number"
                  value={formData.preventive_health_checkup}
                  onChange={(e) => handleFieldChange('preventive_health_checkup', e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 font-mono"
                />
                <span className="text-[10px] text-slate-400">Sub-limit ₹5,000 within total 80D limit</span>
              </div>
            </div>
          </div>
        )}

        {/* Step 8: 80CCD NPS */}
        {currentStep === 8 && (
          <div className="space-y-4 max-w-2xl">
            <h2 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-2">
              National Pension System (NPS) Contributions
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Self Contribution (80CCD(1B))</label>
                <input
                  type="number"
                  value={formData.nps_80ccd_1b}
                  onChange={(e) => handleFieldChange('nps_80ccd_1b', e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 font-mono"
                />
                <span className="text-[10px] text-slate-400">Additional ₹50,000 over Section 80C</span>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Employer Contribution (80CCD(2))</label>
                <input
                  type="number"
                  value={formData.nps_80ccd_2}
                  onChange={(e) => handleFieldChange('nps_80ccd_2', e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 font-mono"
                />
                <span className="text-[10px] text-emerald-600 font-medium">Allowed in BOTH Old and New Regimes!</span>
              </div>
            </div>
          </div>
        )}

        {/* Step 9: 80G Donations */}
        {currentStep === 9 && (
          <div className="space-y-4 max-w-2xl">
            <h2 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-2">
              Charitable Donations (Section 80G)
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">100% Deduction (PM Relief, National Def.)</label>
                <input
                  type="number"
                  value={formData.donations_100_pm}
                  onChange={(e) => handleFieldChange('donations_100_pm', e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">50% Deduction (Approved Trusts)</label>
                <input
                  type="number"
                  value={formData.donations_50_qualifying}
                  onChange={(e) => handleFieldChange('donations_50_qualifying', e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 font-mono"
                />
              </div>
            </div>
          </div>
        )}

        {/* Step 10: Loan Interest */}
        {currentStep === 10 && (
          <div className="space-y-4 max-w-2xl">
            <h2 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-2">
              Higher Education Loan Interest (Section 80E)
            </h2>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Education Loan Interest Paid</label>
              <input
                type="number"
                value={formData.education_loan_interest_80e}
                onChange={(e) => handleFieldChange('education_loan_interest_80e', e.target.value)}
                className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 font-mono"
              />
              <span className="text-[10px] text-slate-400">100% deduction with no upper limit for up to 8 assessment years.</span>
            </div>
          </div>
        )}

        {/* Step 11: TDS & Taxes Paid */}
        {currentStep === 11 && (
          <div className="space-y-4 max-w-2xl">
            <h2 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-2">
              Taxes Deducted (TDS) & Advance Tax Paid
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">TDS on Salary (Form 16 Part A)</label>
                <input
                  type="number"
                  value={formData.tds_salary}
                  onChange={(e) => handleFieldChange('tds_salary', e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">TDS on Interest & Others (Form 26AS)</label>
                <input
                  type="number"
                  value={formData.tds_other}
                  onChange={(e) => handleFieldChange('tds_other', e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Advance Tax Paid Directly</label>
                <input
                  type="number"
                  value={formData.advance_tax_paid}
                  onChange={(e) => handleFieldChange('advance_tax_paid', e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 font-mono"
                />
              </div>
            </div>
          </div>
        )}

        {/* Step 12: AIS / Form 16 Check */}
        {currentStep === 12 && (
          <div className="space-y-4 max-w-2xl">
            <h2 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-2">
              Cross-Verify Against Uploaded Documents
            </h2>
            <p className="text-xs text-slate-600">
              We recommend cross-verifying your manual entries against your uploaded Form 16, AIS, and Form 26AS to prevent income-tax notices.
            </p>
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg space-y-2 text-xs">
              <div className="flex justify-between items-center">
                <span className="text-slate-600">Form 16 Salary TDS:</span>
                <span className="font-mono font-semibold">{formatINR(formData.tds_salary)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-600">Form 26AS Total TDS:</span>
                <span className="font-mono font-semibold">{formatINR(Number(formData.tds_salary) + Number(formData.tds_other))}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-600">Declared Gross Salary:</span>
                <span className="font-mono font-semibold">{formatINR(formData.gross_salary)}</span>
              </div>
            </div>
          </div>
        )}

        {/* Step 13: Review & Compute */}
        {currentStep === 13 && (
          <div className="space-y-4 max-w-2xl">
            <h2 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-2">
              Review Final Data & Trigger Deterministic Computation
            </h2>
            <div className="grid grid-cols-2 gap-4 text-xs">
              <div className="p-3 bg-slate-50 rounded-lg">
                <span className="text-slate-500">Gross Salary</span>
                <p className="text-base font-bold text-slate-800 mt-1">{formatINR(formData.gross_salary)}</p>
              </div>
              <div className="p-3 bg-slate-50 rounded-lg">
                <span className="text-slate-500">Total 80C Invested</span>
                <p className="text-base font-bold text-indigo-700 mt-1">
                  {formatINR(
                    Number(formData.epf) +
                      Number(formData.ppf) +
                      Number(formData.elss) +
                      Number(formData.life_insurance) +
                      Number(formData.home_loan_principal)
                  )}
                </p>
              </div>
              <div className="p-3 bg-slate-50 rounded-lg">
                <span className="text-slate-500">Health 80D</span>
                <p className="text-base font-bold text-indigo-700 mt-1">
                  {formatINR(Number(formData.health_insurance_self) + Number(formData.health_insurance_parents))}
                </p>
              </div>
              <div className="p-3 bg-slate-50 rounded-lg">
                <span className="text-slate-500">NPS Tier 1</span>
                <p className="text-base font-bold text-indigo-700 mt-1">{formatINR(formData.nps_80ccd_1b)}</p>
              </div>
            </div>

            <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg flex items-center gap-3">
              <CheckCircle className="w-5 h-5 text-emerald-600 shrink-0" />
              <p className="text-xs text-emerald-900">
                All 13 steps completed! Click <strong>"Compute Final Tax"</strong> to run the pure Python deterministic rules engine and view your side-by-side Old vs New comparison.
              </p>
            </div>
          </div>
        )}

        {/* Navigation Buttons */}
        <div className="mt-8 pt-4 border-t border-slate-100 flex items-center justify-between">
          <button
            onClick={handleBack}
            disabled={currentStep === 1}
            className={`flex items-center gap-1 px-4 py-2 text-xs font-semibold rounded-lg transition-colors cursor-pointer ${
              currentStep === 1
                ? 'text-slate-300 cursor-not-allowed'
                : 'text-slate-700 bg-slate-100 hover:bg-slate-200'
            }`}
          >
            <ChevronLeft className="w-4 h-4" />
            <span>Previous Step</span>
          </button>

          <button
            onClick={handleNext}
            disabled={isSaving}
            className="flex items-center gap-1 px-5 py-2 text-xs font-semibold rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs transition-all cursor-pointer"
          >
            <span>{currentStep === 13 ? 'Compute Final Tax' : 'Save & Continue'}</span>
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
