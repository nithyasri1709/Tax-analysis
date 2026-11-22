import React, { useState, useEffect } from 'react';
import { useTax } from '../context/TaxContext';
import { CurrencyDisplay, formatINR } from '../components/common/CurrencyDisplay';
import { StatutoryPill } from '../components/common/StatutoryPill';
import {
  Wallet,
  Building,
  PiggyBank,
  TrendingUp,
  Save,
  CheckCircle,
  HelpCircle,
} from 'lucide-react';

export const IncomeOverviewPage: React.FC = () => {
  const { financialYear, regime, profile, updateProfileData, showToast } = useTax();

  const [salary, setSalary] = useState({
    gross_salary: 1500000,
    basic_salary: 600000,
    da_amount: 120000,
    hra_received: 240000,
    special_allowance: 400000,
    professional_tax: 2400,
    annual_rent_paid: 300000,
  });

  const [houseProp, setHouseProp] = useState({
    annual_rent_received: 0,
    municipal_taxes_paid: 0,
    interest_self_occupied: 180000,
    interest_let_out: 0,
  });

  const [otherSources, setOtherSources] = useState({
    savings_interest: 18000,
    fd_interest: 45000,
    dividend_income: 12000,
    other_income: 0,
  });

  const [capitalGains, setCapitalGains] = useState({
    stcg_equity: 0,
    ltcg_equity: 0,
  });

  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (profile) {
      if (profile.salary_data) setSalary((prev) => ({ ...prev, ...profile.salary_data }));
      if (profile.house_prop_data) setHouseProp((prev) => ({ ...prev, ...profile.house_prop_data }));
      if (profile.other_sources_data) setOtherSources((prev) => ({ ...prev, ...profile.other_sources_data }));
      if (profile.capital_gains_data) setCapitalGains((prev) => ({ ...prev, ...profile.capital_gains_data }));
    }
  }, [profile]);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await updateProfileData({
        salary_data: salary,
        house_prop_data: houseProp,
        other_sources_data: otherSources,
        capital_gains_data: capitalGains,
      });
      showToast('Income details saved and tax recomputed!', 'success');
    } catch (err: any) {
      showToast('Failed to save income data', 'error');
    } finally {
      setIsSaving(false);
    }
  };

  // Calculations for display
  const standardDeduction = regime === 'new' ? 75000 : 50000;
  const netSalary = Math.max(0, salary.gross_salary - standardDeduction - salary.professional_tax);
  const housePropertyNet = -Math.min(200000, houseProp.interest_self_occupied);
  const otherSourcesNet =
    Number(otherSources.savings_interest) +
    Number(otherSources.fd_interest) +
    Number(otherSources.dividend_income) +
    Number(otherSources.other_income);
  const grossTotalIncome = netSalary + (regime === 'old' ? housePropertyNet : 0) + otherSourcesNet;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1 rounded bg-indigo-100 text-indigo-700">
              <Wallet className="w-5 h-5" />
            </span>
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">
              Income Overview & Heads of Income
            </h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Configure income across Salary, House Property, Capital Gains, and Other Sources for FY {financialYear}.
          </p>
        </div>

        <button
          onClick={handleSave}
          disabled={isSaving}
          className="flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg shadow-2xs transition-colors cursor-pointer"
        >
          <Save className="w-4 h-4" />
          <span>{isSaving ? 'Recalculating...' : 'Save & Recalculate'}</span>
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
          <span className="text-xs font-medium text-slate-500">Net Salary Income</span>
          <div className="text-xl font-bold text-slate-900 mt-1">{formatINR(netSalary)}</div>
          <span className="text-[10px] text-slate-400">After Std Ded {formatINR(standardDeduction)}</span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
          <span className="text-xs font-medium text-slate-500">House Property Loss</span>
          <div className="text-xl font-bold text-rose-600 mt-1">
            {regime === 'old' ? formatINR(housePropertyNet) : '₹ 0 (New Regime)'}
          </div>
          <span className="text-[10px] text-slate-400">Section 24(b) set-off</span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
          <span className="text-xs font-medium text-slate-500">Other Sources</span>
          <div className="text-xl font-bold text-slate-900 mt-1">{formatINR(otherSourcesNet)}</div>
          <span className="text-[10px] text-slate-400">Savings & FD interest</span>
        </div>

        <div className="bg-indigo-50 border border-indigo-200 p-4 rounded-xl shadow-2xs">
          <span className="text-xs font-semibold text-indigo-900">Gross Total Income (GTI)</span>
          <div className="text-2xl font-bold text-indigo-700 mt-1">{formatINR(grossTotalIncome)}</div>
          <span className="text-[10px] text-indigo-600 font-medium">Under {regime.toUpperCase()} Regime</span>
        </div>
      </div>

      {/* Accordion / Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Head 1: Salary Income */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <div className="flex items-center gap-2">
              <Wallet className="w-4 h-4 text-indigo-600" />
              <h2 className="text-sm font-bold text-slate-800">1. Income from Salary (Section 17)</h2>
            </div>
            <StatutoryPill section1961="16(ia)" section2025="16(ia)" />
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <label className="font-semibold text-slate-700">Gross Annual Salary</label>
              <input
                type="number"
                value={salary.gross_salary}
                onChange={(e) => setSalary({ ...salary, gross_salary: Number(e.target.value) })}
                className="w-full p-2 border border-slate-300 rounded-lg mt-1 font-mono"
              />
            </div>
            <div>
              <label className="font-semibold text-slate-700">Basic Salary</label>
              <input
                type="number"
                value={salary.basic_salary}
                onChange={(e) => setSalary({ ...salary, basic_salary: Number(e.target.value) })}
                className="w-full p-2 border border-slate-300 rounded-lg mt-1 font-mono"
              />
            </div>
            <div>
              <label className="font-semibold text-slate-700">Dearness Allowance (DA)</label>
              <input
                type="number"
                value={salary.da_amount}
                onChange={(e) => setSalary({ ...salary, da_amount: Number(e.target.value) })}
                className="w-full p-2 border border-slate-300 rounded-lg mt-1 font-mono"
              />
            </div>
            <div>
              <label className="font-semibold text-slate-700">HRA Received</label>
              <input
                type="number"
                value={salary.hra_received}
                onChange={(e) => setSalary({ ...salary, hra_received: Number(e.target.value) })}
                className="w-full p-2 border border-slate-300 rounded-lg mt-1 font-mono"
              />
            </div>
            <div>
              <label className="font-semibold text-slate-700">Annual Rent Paid</label>
              <input
                type="number"
                value={salary.annual_rent_paid}
                onChange={(e) => setSalary({ ...salary, annual_rent_paid: Number(e.target.value) })}
                className="w-full p-2 border border-slate-300 rounded-lg mt-1 font-mono"
              />
            </div>
            <div>
              <label className="font-semibold text-slate-700">Professional Tax</label>
              <input
                type="number"
                value={salary.professional_tax}
                onChange={(e) => setSalary({ ...salary, professional_tax: Number(e.target.value) })}
                className="w-full p-2 border border-slate-300 rounded-lg mt-1 font-mono"
              />
            </div>
          </div>
        </div>

        {/* Head 2: House Property */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <div className="flex items-center gap-2">
              <Building className="w-4 h-4 text-indigo-600" />
              <h2 className="text-sm font-bold text-slate-800">2. Income from House Property (Section 24)</h2>
            </div>
            <StatutoryPill section1961="24(b)" section2025="24(b)" />
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <label className="font-semibold text-slate-700">Self-Occupied Home Loan Interest</label>
              <input
                type="number"
                value={houseProp.interest_self_occupied}
                onChange={(e) => setHouseProp({ ...houseProp, interest_self_occupied: Number(e.target.value) })}
                className="w-full p-2 border border-slate-300 rounded-lg mt-1 font-mono"
              />
              <span className="text-[10px] text-slate-400">Cap: ₹2,00,000 (Old Regime only)</span>
            </div>
            <div>
              <label className="font-semibold text-slate-700">Rental Income (Let Out Property)</label>
              <input
                type="number"
                value={houseProp.annual_rent_received}
                onChange={(e) => setHouseProp({ ...houseProp, annual_rent_received: Number(e.target.value) })}
                className="w-full p-2 border border-slate-300 rounded-lg mt-1 font-mono"
              />
            </div>
            <div>
              <label className="font-semibold text-slate-700">Municipal Taxes Paid</label>
              <input
                type="number"
                value={houseProp.municipal_taxes_paid}
                onChange={(e) => setHouseProp({ ...houseProp, municipal_taxes_paid: Number(e.target.value) })}
                className="w-full p-2 border border-slate-300 rounded-lg mt-1 font-mono"
              />
            </div>
            <div>
              <label className="font-semibold text-slate-700">Let-Out Home Loan Interest</label>
              <input
                type="number"
                value={houseProp.interest_let_out}
                onChange={(e) => setHouseProp({ ...houseProp, interest_let_out: Number(e.target.value) })}
                className="w-full p-2 border border-slate-300 rounded-lg mt-1 font-mono"
              />
            </div>
          </div>
        </div>

        {/* Head 3: Other Sources */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <div className="flex items-center gap-2">
              <PiggyBank className="w-4 h-4 text-indigo-600" />
              <h2 className="text-sm font-bold text-slate-800">3. Income from Other Sources (Section 56)</h2>
            </div>
            <StatutoryPill section1961="56(2)" section2025="56(2)" />
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <label className="font-semibold text-slate-700">Savings Bank Interest</label>
              <input
                type="number"
                value={otherSources.savings_interest}
                onChange={(e) => setOtherSources({ ...otherSources, savings_interest: Number(e.target.value) })}
                className="w-full p-2 border border-slate-300 rounded-lg mt-1 font-mono"
              />
            </div>
            <div>
              <label className="font-semibold text-slate-700">FD / Term Deposit Interest</label>
              <input
                type="number"
                value={otherSources.fd_interest}
                onChange={(e) => setOtherSources({ ...otherSources, fd_interest: Number(e.target.value) })}
                className="w-full p-2 border border-slate-300 rounded-lg mt-1 font-mono"
              />
            </div>
            <div>
              <label className="font-semibold text-slate-700">Dividend Income</label>
              <input
                type="number"
                value={otherSources.dividend_income}
                onChange={(e) => setOtherSources({ ...otherSources, dividend_income: Number(e.target.value) })}
                className="w-full p-2 border border-slate-300 rounded-lg mt-1 font-mono"
              />
            </div>
            <div>
              <label className="font-semibold text-slate-700">Other Miscellaneous Income</label>
              <input
                type="number"
                value={otherSources.other_income}
                onChange={(e) => setOtherSources({ ...otherSources, other_income: Number(e.target.value) })}
                className="w-full p-2 border border-slate-300 rounded-lg mt-1 font-mono"
              />
            </div>
          </div>
        </div>

        {/* Head 4: Capital Gains */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-indigo-600" />
              <h2 className="text-sm font-bold text-slate-800">4. Capital Gains (Section 45)</h2>
            </div>
            <StatutoryPill section1961="111A / 112A" section2025="111A / 112A" />
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <label className="font-semibold text-slate-700">STCG on Listed Equity (Sec 111A)</label>
              <input
                type="number"
                value={capitalGains.stcg_equity}
                onChange={(e) => setCapitalGains({ ...capitalGains, stcg_equity: Number(e.target.value) })}
                className="w-full p-2 border border-slate-300 rounded-lg mt-1 font-mono"
              />
              <span className="text-[10px] text-slate-400">Special rate 20% (Budget 2024+)</span>
            </div>
            <div>
              <label className="font-semibold text-slate-700">LTCG on Listed Equity (Sec 112A)</label>
              <input
                type="number"
                value={capitalGains.ltcg_equity}
                onChange={(e) => setCapitalGains({ ...capitalGains, ltcg_equity: Number(e.target.value) })}
                className="w-full p-2 border border-slate-300 rounded-lg mt-1 font-mono"
              />
              <span className="text-[10px] text-slate-400">Special rate 12.5% above ₹1.25L</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
