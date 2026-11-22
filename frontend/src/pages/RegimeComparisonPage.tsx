import React, { useState } from 'react';
import { useTax } from '../context/TaxContext';
import { api } from '../api/client';
import { formatINR } from '../components/common/CurrencyDisplay';
import { StatutoryPill } from '../components/common/StatutoryPill';
import {
  Scale,
  Calculator,
  Home,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from 'recharts';

export const RegimeComparisonPage: React.FC = () => {
  const { financialYear, regime, setRegime, comparisonResult, showToast, refreshAll, isRecalculating } = useTax();

  // HRA calculator state
  const [basicSalary, setBasicSalary] = useState<number>(600000);
  const [daAmount, setDaAmount] = useState<number>(120000);
  const [hraReceived, setHraReceived] = useState<number>(240000);
  const [annualRent, setAnnualRent] = useState<number>(300000);
  const [isMetro, setIsMetro] = useState<boolean>(true);
  const [hraResult, setHraResult] = useState<any>(null);
  const [isCalculatingHra, setIsCalculatingHra] = useState<boolean>(false);

  const comp = comparisonResult;

  const handleComputeHra = async () => {
    setIsCalculatingHra(true);
    try {
      const res = await api.tax.calculateHra({
        basic_salary: basicSalary,
        da_amount: daAmount,
        hra_received: hraReceived,
        annual_rent_paid: annualRent,
        is_metro: isMetro,
        regime: 'old',
        financial_year: financialYear,
      });
      setHraResult(res);
      showToast('HRA Exemption calculated successfully!', 'success');
    } catch (err: any) {
      showToast('Failed to calculate HRA exemption', 'error');
    } finally {
      setIsCalculatingHra(false);
    }
  };

  if (!comp) {
    return (
      <div className="bg-white p-12 rounded-xl border border-slate-200 text-center space-y-3">
        <Scale className="w-10 h-10 text-indigo-600 mx-auto animate-pulse" />
        <h2 className="text-sm font-bold text-slate-800">Comparing Old vs New Regimes...</h2>
        <p className="text-xs text-slate-400 max-w-sm mx-auto">
          Running dual deterministic rules engine for FY {financialYear} to compute exact savings and break-even deductions.
        </p>
        <button
          onClick={refreshAll}
          disabled={isRecalculating}
          className="px-4 py-1.5 bg-indigo-600 text-white rounded-lg text-xs font-semibold hover:bg-indigo-700"
        >
          {isRecalculating ? 'Calculating...' : 'Recalculate Comparison Now'}
        </button>
      </div>
    );
  }

  const oldR = comp.old_regime || {};
  const newR = comp.new_regime || {};

  const oldGross = oldR.gross_total_income ?? 0;
  const newGross = newR.gross_total_income ?? 0;

  const oldDeductions = oldR.total_deductions_allowed ?? oldR.total_chapter_vi_a_deductions ?? 0;
  const newDeductions = newR.total_deductions_allowed ?? newR.total_chapter_vi_a_deductions ?? 0;

  const oldTaxable = oldR.taxable_income ?? oldR.taxable_total_income ?? 0;
  const newTaxable = newR.taxable_income ?? newR.taxable_total_income ?? 0;

  const oldTax = oldR.total_tax_liability ?? oldR.gross_tax_liability ?? 0;
  const newTax = newR.total_tax_liability ?? newR.gross_tax_liability ?? 0;

  const taxSavings = comp.tax_savings ?? comp.tax_difference ?? (comp as any).tax_diff ?? 0;
  const breakEven = comp.break_even_deduction ?? (comp as any).break_even_deductions ?? 0;
  const recRegime = comp.recommended_regime || 'new';
  const recReason = comp.reason || (comp as any).plain_language_explanation || '';

  const chartData = [
    {
      metric: 'Gross Income',
      'Old Regime': oldGross,
      'New Regime': newGross,
    },
    {
      metric: 'Deductions Allowed',
      'Old Regime': oldDeductions,
      'New Regime': newDeductions,
    },
    {
      metric: 'Taxable Income',
      'Old Regime': oldTaxable,
      'New Regime': newTaxable,
    },
    {
      metric: 'Tax Liability',
      'Old Regime': oldTax,
      'New Regime': newTax,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1 rounded bg-indigo-100 text-indigo-700">
              <Scale className="w-5 h-5" />
            </span>
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">
              Old vs New Regime Statutory Comparator
            </h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Section 115BAC concessional slabs vs Section 115 old slabs for FY {financialYear}.
          </p>
        </div>

        <StatutoryPill section1961="115BAC" section2025="115BAC" />
      </div>

      {/* Winning Regime Recommendation Card */}
      <div className="bg-gradient-to-r from-emerald-500/10 via-teal-500/10 to-indigo-500/10 border-2 border-emerald-400 rounded-xl p-5 shadow-2xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="w-12 h-12 rounded-xl bg-emerald-600 text-white flex items-center justify-center font-bold text-lg shadow-sm">
            ✓
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-emerald-800">
                Official Recommendation
              </span>
              <span className="px-2.5 py-0.5 rounded-full bg-emerald-600 text-white text-xs font-bold uppercase">
                {recRegime} Regime Wins
              </span>
            </div>
            <h3 className="text-base font-bold text-slate-900 mt-1">{recReason}</h3>
            <p className="text-xs text-slate-600 mt-0.5">
              Net Tax Difference:{' '}
              <strong className="text-emerald-700 font-bold">{formatINR(taxSavings)}</strong> •
              Break-Even Deductions Point:{' '}
              <strong className="text-indigo-800 font-bold">{formatINR(breakEven)}</strong>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {regime !== recRegime && (
            <button
              onClick={() => setRegime(recRegime as 'new' | 'old')}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors cursor-pointer"
            >
              Set {recRegime.toUpperCase()} as Active
            </button>
          )}
        </div>
      </div>

      {/* Break-even Explainer Box */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs flex items-center gap-3 text-xs text-slate-600">
        <div className="p-2 rounded-lg bg-indigo-50 text-indigo-700 shrink-0">
          <Calculator className="w-5 h-5" />
        </div>
        <div>
          <span className="font-bold text-slate-800">Break-Even Point Insight:</span> In order for the
          Old Regime to yield lower or equal tax than the New Regime at your income level, you need at
          least <strong>{formatINR(breakEven)}</strong> in total deductions (including
          standard deduction, 80C, 80D, HRA, and home loan interest). Currently, your eligible
          deductions are <strong>{formatINR(oldDeductions)}</strong>.
        </div>
      </div>

      {/* Side-by-Side Detailed Comparison Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-2xs overflow-hidden">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50">
          <h2 className="text-sm font-bold text-slate-800">
            Line-by-Line Statutory Comparison (FY {financialYear})
          </h2>
          <span className="text-xs text-slate-500 font-medium">All figures in INR (₹)</span>
        </div>

        <table className="w-full text-left text-xs">
          <thead className="bg-slate-100/70 border-b border-slate-200 text-slate-600 font-bold text-xs uppercase">
            <tr>
              <th className="py-3 px-4 w-1/2">Statutory Component</th>
              <th className="py-3 px-4 text-right w-1/4">Old Regime</th>
              <th className="py-3 px-4 text-right w-1/4 bg-indigo-50/50 text-indigo-900">
                New Regime (Default)
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 font-mono text-xs">
            <tr className="hover:bg-slate-50/50">
              <td className="py-2.5 px-4 font-sans font-medium text-slate-800">Gross Total Income</td>
              <td className="py-2.5 px-4 text-right">{formatINR(oldGross)}</td>
              <td className="py-2.5 px-4 text-right bg-indigo-50/30 font-semibold">
                {formatINR(newGross)}
              </td>
            </tr>

            <tr className="hover:bg-slate-50/50 text-emerald-700">
              <td className="py-2.5 px-4 font-sans font-medium">Standard Deduction (Salaried)</td>
              <td className="py-2.5 px-4 text-right">
                {formatINR(oldR.standard_deduction || 50000)}
              </td>
              <td className="py-2.5 px-4 text-right bg-indigo-50/30 font-semibold">
                {formatINR(newR.standard_deduction || 75000)}
              </td>
            </tr>

            <tr className="hover:bg-slate-50/50">
              <td className="py-2.5 px-4 font-sans font-medium text-slate-800">
                Chapter VI-A Deductions (80C, 80D, 80CCD(1B))
              </td>
              <td className="py-2.5 px-4 text-right text-emerald-700 font-semibold">
                {formatINR(oldDeductions)}
              </td>
              <td className="py-2.5 px-4 text-right bg-indigo-50/30 text-slate-400">
                Not Allowed
              </td>
            </tr>

            <tr className="hover:bg-slate-50/50">
              <td className="py-2.5 px-4 font-sans font-medium text-slate-800">
                Employer NPS Contribution (Sec 80CCD(2))
              </td>
              <td className="py-2.5 px-4 text-right">Allowed (Up to 14%)</td>
              <td className="py-2.5 px-4 text-right bg-indigo-50/30 font-semibold text-emerald-700">
                Allowed (Up to 14%)
              </td>
            </tr>

            <tr className="hover:bg-slate-50/50 bg-slate-50/40 font-bold">
              <td className="py-2.5 px-4 font-sans text-slate-900">
                Taxable Income (Sec 288A rounded)
              </td>
              <td className="py-2.5 px-4 text-right text-slate-900">
                {formatINR(oldTaxable)}
              </td>
              <td className="py-2.5 px-4 text-right bg-indigo-50/50 text-indigo-900">
                {formatINR(newTaxable)}
              </td>
            </tr>

            <tr className="hover:bg-slate-50/50">
              <td className="py-2.5 px-4 font-sans font-medium text-slate-800">
                Base Tax before Rebate & Surcharge
              </td>
              <td className="py-2.5 px-4 text-right">{formatINR(oldR.base_tax || oldR.slab_tax || 0)}</td>
              <td className="py-2.5 px-4 text-right bg-indigo-50/30 font-semibold">
                {formatINR(newR.base_tax || newR.slab_tax || 0)}
              </td>
            </tr>

            <tr className="hover:bg-slate-50/50 text-emerald-700">
              <td className="py-2.5 px-4 font-sans font-medium">
                Section 87A Rebate & Marginal Relief
              </td>
              <td className="py-2.5 px-4 text-right">- {formatINR(oldR.rebate_87a || 0)}</td>
              <td className="py-2.5 px-4 text-right bg-indigo-50/30 font-semibold">
                - {formatINR(newR.rebate_87a || 0)}
              </td>
            </tr>

            <tr className="hover:bg-slate-50/50">
              <td className="py-2.5 px-4 font-sans font-medium text-slate-800">
                Health & Education Cess (4%)
              </td>
              <td className="py-2.5 px-4 text-right">{formatINR(oldR.cess || oldR.health_and_education_cess || 0)}</td>
              <td className="py-2.5 px-4 text-right bg-indigo-50/30 font-semibold">
                {formatINR(newR.cess || newR.health_and_education_cess || 0)}
              </td>
            </tr>

            <tr className="bg-slate-100 font-bold text-sm">
              <td className="py-3 px-4 font-sans text-slate-900">Net Tax Payable (Sec 288B)</td>
              <td
                className={`py-3 px-4 text-right ${
                  recRegime === 'old' ? 'text-emerald-700 font-extrabold' : 'text-slate-800'
                }`}
              >
                {formatINR(oldTax)}
              </td>
              <td
                className={`py-3 px-4 text-right bg-indigo-100/60 ${
                  recRegime === 'new' ? 'text-indigo-900 font-extrabold' : 'text-slate-800'
                }`}
              >
                {formatINR(newTax)}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* Visual Comparison Bar Chart */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs">
        <h2 className="text-sm font-bold text-slate-800 mb-4">
          Statutory Metric Comparison (Old vs New)
        </h2>
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
              <XAxis dataKey="metric" tick={{ fontSize: 11, fill: '#64748b' }} />
              <YAxis
                tick={{ fontSize: 10, fill: '#64748b' }}
                tickFormatter={(val) => `₹${val / 1000}k`}
              />
              <Tooltip formatter={(val: any) => [formatINR(val), '']} />
              <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
              <Bar dataKey="Old Regime" fill="#94a3b8" radius={[4, 4, 0, 0]} />
              <Bar dataKey="New Regime" fill="#4f46e5" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Built-in Interactive HRA Exemption Calculator */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-2xs space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-2">
          <div className="flex items-center gap-2">
            <Home className="w-5 h-5 text-indigo-600" />
            <div>
              <h2 className="text-sm font-bold text-slate-800">
                Built-in Section 10(13A) HRA Exemption Calculator
              </h2>
              <p className="text-[11px] text-slate-400">
                Computes the least of the 3 statutory criteria (Old Regime only).
              </p>
            </div>
          </div>
          <StatutoryPill section1961="10(13A)" section2025="10(13A)" />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 text-xs">
          <div>
            <label className="font-semibold text-slate-700">Basic Salary</label>
            <input
              type="number"
              value={basicSalary}
              onChange={(e) => setBasicSalary(Number(e.target.value))}
              className="w-full p-2 border border-slate-300 rounded-lg mt-1 font-mono"
            />
          </div>
          <div>
            <label className="font-semibold text-slate-700">Dearness Allowance (DA)</label>
            <input
              type="number"
              value={daAmount}
              onChange={(e) => setDaAmount(Number(e.target.value))}
              className="w-full p-2 border border-slate-300 rounded-lg mt-1 font-mono"
            />
          </div>
          <div>
            <label className="font-semibold text-slate-700">Actual HRA Received</label>
            <input
              type="number"
              value={hraReceived}
              onChange={(e) => setHraReceived(Number(e.target.value))}
              className="w-full p-2 border border-slate-300 rounded-lg mt-1 font-mono"
            />
          </div>
          <div>
            <label className="font-semibold text-slate-700">Annual Rent Paid</label>
            <input
              type="number"
              value={annualRent}
              onChange={(e) => setAnnualRent(Number(e.target.value))}
              className="w-full p-2 border border-slate-300 rounded-lg mt-1 font-mono"
            />
          </div>
        </div>

        <div className="flex items-center justify-between">
          <label className="flex items-center gap-2 text-xs font-semibold text-slate-700 cursor-pointer">
            <input
              type="checkbox"
              checked={isMetro}
              onChange={(e) => setIsMetro(e.target.checked)}
              className="w-4 h-4 text-indigo-600 rounded"
            />
            <span>Metro City (Delhi, Mumbai, Kolkata, Chennai: 50% Basic+DA)</span>
          </label>

          <button
            onClick={handleComputeHra}
            disabled={isCalculatingHra}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg shadow-2xs transition-colors cursor-pointer"
          >
            {isCalculatingHra ? 'Calculating...' : 'Compute HRA Exemption'}
          </button>
        </div>

        {hraResult && (
          <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg space-y-2 text-xs">
            <div className="flex items-center justify-between text-indigo-900 font-bold text-sm">
              <span>Section 10(13A) Exempt HRA:</span>
              <span className="font-mono text-emerald-700 font-extrabold text-base">
                {formatINR(hraResult.exempt_hra)}
              </span>
            </div>
            <div className="flex items-center justify-between text-slate-600 text-xs">
              <span>Taxable HRA Component:</span>
              <span className="font-mono">{formatINR(hraResult.taxable_hra)}</span>
            </div>
            <div className="text-[11px] text-slate-500 pt-1 border-t border-slate-200">
              <strong>Calculation Basis:</strong> Least of (1) Actual HRA: {formatINR(hraReceived)}, (2)
              Rent - 10% Salary: {formatINR(Math.max(0, annualRent - 0.1 * (basicSalary + daAmount)))}, (3){' '}
              {isMetro ? '50%' : '40%'} of Salary: {formatINR((isMetro ? 0.5 : 0.4) * (basicSalary + daAmount))}.
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
