import React, { useState } from 'react';
import { useTax } from '../context/TaxContext';
import { formatINR } from '../components/common/CurrencyDisplay';
import { StatutoryPill } from '../components/common/StatutoryPill';
import {
  Calculator,
  Calendar,
} from 'lucide-react';

export const TaxCalculationPage: React.FC = () => {
  const { financialYear, regime, comparisonResult, refreshAll, isRecalculating } = useTax();

  const [activeTab, setActiveTab] = useState<'summary' | 'audit' | 'advance'>('summary');

  const taxResult =
    regime === 'new' ? comparisonResult?.new_regime : comparisonResult?.old_regime;

  if (!taxResult) {
    return (
      <div className="bg-white p-12 rounded-xl border border-slate-200 text-center space-y-3">
        <Calculator className="w-10 h-10 text-indigo-600 mx-auto animate-pulse" />
        <h2 className="text-sm font-bold text-slate-800">Computing Deterministic Tax Breakdown...</h2>
        <p className="text-xs text-slate-400 max-w-sm mx-auto">
          Running Section 115 / 115BAC rules engine with Section 288A/B rounding for FY {financialYear}.
        </p>
        <button
          onClick={refreshAll}
          disabled={isRecalculating}
          className="px-4 py-1.5 bg-indigo-600 text-white rounded-lg text-xs font-semibold hover:bg-indigo-700"
        >
          {isRecalculating ? 'Calculating...' : 'Recalculate Tax Now'}
        </button>
      </div>
    );
  }

  const grossTotalIncome = taxResult.gross_total_income ?? 0;
  const taxableIncome = taxResult.taxable_income ?? (taxResult as any).taxable_total_income ?? 0;
  const rebate87a = taxResult.rebate_87a ?? 0;
  const totalTaxLiability = taxResult.total_tax_liability ?? (taxResult as any).gross_tax_liability ?? 0;
  const baseTax = taxResult.base_tax ?? (taxResult as any).slab_tax ?? 0;
  const surcharge = taxResult.surcharge ?? (taxResult as any).net_surcharge ?? 0;
  const cess = taxResult.cess ?? (taxResult as any).health_and_education_cess ?? 0;

  const slabList = Array.isArray(taxResult.slab_breakdown) ? taxResult.slab_breakdown : [];

  const auditList = Array.isArray(taxResult.audit_trace)
    ? taxResult.audit_trace
    : Array.isArray((taxResult as any).calculation_breakdown)
    ? (taxResult as any).calculation_breakdown.map((s: any) => ({
        step: s.label || s.step_id || '',
        description: s.notes || s.formula_text || '',
        amount: s.output_amount,
        rule_applied: s.section_ref,
      }))
    : [];

  const advanceSchedule = Array.isArray(taxResult.advance_tax_schedule)
    ? taxResult.advance_tax_schedule
    : [];

  const int234 = taxResult.interest_234 || {
    interest_234a: 0,
    interest_234b: 0,
    interest_234c: (taxResult as any).statutory_interest_234abc || 0,
    total_interest: (taxResult as any).statutory_interest_234abc || 0,
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1 rounded bg-indigo-100 text-indigo-700">
              <Calculator className="w-5 h-5" />
            </span>
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">
              Deterministic Tax Calculation & Audit Inspector
            </h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Pure-Python statutory engine • Rounded under Section 288A & 288B • Active Regime:{' '}
            <strong>{regime.toUpperCase()}</strong>
          </p>
        </div>

        <div className="flex items-center gap-2 bg-slate-100 p-1 rounded-lg">
          <button
            onClick={() => setActiveTab('summary')}
            className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${
              activeTab === 'summary' ? 'bg-white text-indigo-700 shadow-xs' : 'text-slate-600'
            }`}
          >
            Slab Breakdown
          </button>
          <button
            onClick={() => setActiveTab('audit')}
            className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${
              activeTab === 'audit' ? 'bg-white text-indigo-700 shadow-xs' : 'text-slate-600'
            }`}
          >
            Step-by-Step Audit Trace ({auditList.length})
          </button>
          <button
            onClick={() => setActiveTab('advance')}
            className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${
              activeTab === 'advance' ? 'bg-white text-indigo-700 shadow-xs' : 'text-slate-600'
            }`}
          >
            Advance Tax & 234 Int.
          </button>
        </div>
      </div>

      {/* Top Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
          <span className="text-xs font-medium text-slate-500">Gross Total Income</span>
          <div className="text-xl font-bold text-slate-900 mt-1">
            {formatINR(grossTotalIncome)}
          </div>
          <span className="text-[10px] text-slate-400">Section 80B(5)</span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
          <span className="text-xs font-medium text-slate-500">Taxable Total Income</span>
          <div className="text-xl font-bold text-indigo-700 mt-1">
            {formatINR(taxableIncome)}
          </div>
          <span className="text-[10px] text-slate-400">Sec 288A nearest ₹10</span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
          <span className="text-xs font-medium text-slate-500">Sec 87A Tax Rebate</span>
          <div className="text-xl font-bold text-emerald-600 mt-1">
            {formatINR(rebate87a)}
          </div>
          <span className="text-[10px] text-slate-400">With marginal relief</span>
        </div>

        <div className="bg-indigo-50 border border-indigo-200 p-4 rounded-xl shadow-2xs">
          <span className="text-xs font-semibold text-indigo-900">Total Tax Liability</span>
          <div className="text-2xl font-bold text-indigo-700 mt-1">
            {formatINR(totalTaxLiability)}
          </div>
          <span className="text-[10px] text-indigo-600 font-medium">Sec 288B rounded</span>
        </div>
      </div>

      {/* Tab 1: Summary Slab Breakdown Table */}
      {activeTab === 'summary' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-2xs overflow-hidden">
          <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50">
            <div>
              <h2 className="text-sm font-bold text-slate-800">
                Slab-by-Slab Statutory Tax Computation
              </h2>
              <p className="text-xs text-slate-500">
                FY {financialYear} • Statutory basis: <strong>{taxResult.statutory_basis || (taxResult as any).statutory_act || 'Income-tax Act'}</strong>
              </p>
            </div>
            <StatutoryPill section1961="115BAC" section2025="115BAC" />
          </div>

          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-100 text-slate-500 uppercase text-[10px]">
              <tr>
                <th className="py-2.5 px-4 font-semibold">Income Slab</th>
                <th className="py-2.5 px-4 font-semibold text-right">Taxable in Slab</th>
                <th className="py-2.5 px-4 font-semibold text-center">Tax Rate</th>
                <th className="py-2.5 px-4 font-semibold text-right">Computed Tax</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono">
              {slabList.length === 0 ? (
                <tr>
                  <td colSpan={4} className="py-4 text-center text-slate-400 font-sans">
                    No taxable income in slabs.
                  </td>
                </tr>
              ) : (
                slabList.map((sb: any, idx: number) => {
                  const label = sb.slab || sb.range || `Slab ${idx + 1}`;
                  const taxableInSlab = sb.taxable_in_slab ?? sb.taxable_amount ?? 0;
                  const rateStr = sb.rate ?? (sb.rate_pct !== undefined ? `${sb.rate_pct}%` : '0%');
                  const taxVal = sb.tax ?? sb.tax_amount ?? 0;
                  return (
                    <tr key={idx} className="hover:bg-slate-50/50">
                      <td className="py-2.5 px-4 text-slate-700 font-sans font-medium">{label}</td>
                      <td className="py-2.5 px-4 text-right text-slate-700">{formatINR(taxableInSlab)}</td>
                      <td className="py-2.5 px-4 text-center font-bold text-indigo-700">{rateStr}</td>
                      <td className="py-2.5 px-4 text-right font-bold text-slate-800">{formatINR(taxVal)}</td>
                    </tr>
                  );
                })
              )}
            </tbody>
            <tfoot className="bg-slate-50/80 font-bold border-t border-slate-200 text-xs font-mono">
              <tr>
                <td colSpan={3} className="py-2.5 px-4 text-right font-sans">
                  Base Tax before Rebate:
                </td>
                <td className="py-2.5 px-4 text-right">{formatINR(baseTax)}</td>
              </tr>
              {rebate87a > 0 && (
                <tr className="text-emerald-700">
                  <td colSpan={3} className="py-2.5 px-4 text-right font-sans">
                    Less: Section 87A Tax Rebate:
                  </td>
                  <td className="py-2.5 px-4 text-right">- {formatINR(rebate87a)}</td>
                </tr>
              )}
              {surcharge > 0 && (
                <tr className="text-amber-800">
                  <td colSpan={3} className="py-2.5 px-4 text-right font-sans">
                    Add: Surcharge (with marginal relief):
                  </td>
                  <td className="py-2.5 px-4 text-right">+ {formatINR(surcharge)}</td>
                </tr>
              )}
              <tr>
                <td colSpan={3} className="py-2.5 px-4 text-right font-sans">
                  Add: Health & Education Cess (4%):
                </td>
                <td className="py-2.5 px-4 text-right">+ {formatINR(cess)}</td>
              </tr>
              <tr className="text-indigo-900 bg-indigo-50/50 text-sm">
                <td colSpan={3} className="py-3 px-4 text-right font-sans">
                  Net Tax Liability (Sec 288B nearest ₹10):
                </td>
                <td className="py-3 px-4 text-right font-bold">
                  {formatINR(totalTaxLiability)}
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      )}

      {/* Tab 2: Step-by-Step Audit Trace */}
      {activeTab === 'audit' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-2xs overflow-hidden">
          <div className="p-4 border-b border-slate-100 bg-slate-50 flex items-center justify-between">
            <h2 className="text-sm font-bold text-slate-800">
              Statutory Calculation Audit Log (Deterministic Formula Trace)
            </h2>
            <span className="text-[10px] font-mono bg-slate-200 px-2 py-0.5 rounded text-slate-700">
              Zero LLM Math
            </span>
          </div>

          <div className="divide-y divide-slate-100">
            {auditList.map((step: any, i: number) => (
              <div key={i} className="p-3.5 hover:bg-slate-50/70 transition-colors flex items-start gap-3 text-xs">
                <span className="w-6 h-6 rounded-full bg-indigo-50 text-indigo-700 font-bold flex items-center justify-center shrink-0 text-[10px]">
                  {i + 1}
                </span>

                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-800">{step.step}</span>
                    {step.rule_applied && (
                      <code className="text-[10px] bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded">
                        {step.rule_applied}
                      </code>
                    )}
                  </div>
                  <p className="text-slate-600 mt-0.5 text-[11px] leading-relaxed">{step.description}</p>
                </div>

                {step.amount !== null && step.amount !== undefined && (
                  <div className="font-mono font-bold text-slate-800 shrink-0 text-right">
                    {formatINR(step.amount)}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 3: Advance Tax Schedule & 234 Interest */}
      {activeTab === 'advance' && (
        <div className="space-y-6">
          <div className="bg-white rounded-xl border border-slate-200 shadow-2xs overflow-hidden">
            <div className="p-4 border-b border-slate-100 bg-slate-50 flex items-center justify-between">
              <div>
                <h2 className="text-sm font-bold text-slate-800">Advance Tax Installment Schedule</h2>
                <p className="text-xs text-slate-400">
                  Mandatory if estimated tax liability exceeds ₹10,000 in the financial year.
                </p>
              </div>
              <StatutoryPill section1961="208 / 211" section2025="208 / 211" />
            </div>

            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-b border-slate-100 text-slate-500 uppercase text-[10px]">
                <tr>
                  <th className="py-2.5 px-4 font-semibold">Installment Due Date</th>
                  <th className="py-2.5 px-4 font-semibold text-center">Statutory Cumulative %</th>
                  <th className="py-2.5 px-4 font-semibold text-right">Cumulative Tax Payable</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-mono">
                {advanceSchedule.map((item: any, idx: number) => (
                  <tr key={idx} className="hover:bg-slate-50/50">
                    <td className="py-2.5 px-4 text-slate-800 font-sans font-medium flex items-center gap-2">
                      <Calendar className="w-3.5 h-3.5 text-indigo-600" />
                      <span>{item.due_date || `Installment ${idx + 1}`}</span>
                    </td>
                    <td className="py-2.5 px-4 text-center font-bold text-indigo-700">
                      {item.percentage}%
                    </td>
                    <td className="py-2.5 px-4 text-right font-bold text-slate-800">
                      {formatINR(item.cumulative_amount)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs space-y-3">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <h3 className="text-sm font-bold text-slate-800">
                Interest Penalties under Section 234A, 234B, and 234C (Estimate)
              </h3>
              <StatutoryPill section1961="234A/B/C" section2025="234A/B/C" />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs">
              <div className="p-3 bg-slate-50 rounded-lg">
                <span className="text-slate-500">234A (Delay in Filing)</span>
                <div className="text-base font-bold font-mono text-slate-800 mt-1">
                  {formatINR(int234.interest_234a || 0)}
                </div>
                <span className="text-[10px] text-slate-400">1% per month</span>
              </div>

              <div className="p-3 bg-slate-50 rounded-lg">
                <span className="text-slate-500">234B (Default in Advance Tax)</span>
                <div className="text-base font-bold font-mono text-slate-800 mt-1">
                  {formatINR(int234.interest_234b || 0)}
                </div>
                <span className="text-[10px] text-slate-400">Paid &lt; 90% of assessed tax</span>
              </div>

              <div className="p-3 bg-slate-50 rounded-lg">
                <span className="text-slate-500">234C (Deferment of Installments)</span>
                <div className="text-base font-bold font-mono text-slate-800 mt-1">
                  {formatINR(int234.interest_234c || 0)}
                </div>
                <span className="text-[10px] text-slate-400">Quarterly shortfall</span>
              </div>

              <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg">
                <span className="text-rose-700 font-semibold">Total Estimated Interest</span>
                <div className="text-base font-bold font-mono text-rose-800 mt-1">
                  {formatINR(int234.total_interest || 0)}
                </div>
                <span className="text-[10px] text-rose-600">Statutory estimate</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
