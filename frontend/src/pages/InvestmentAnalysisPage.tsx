import React, { useState, useEffect, useCallback } from 'react';
import { useTax } from '../context/TaxContext';
import { api } from '../api/client';
import { InvestmentAnalysisResponse } from '../types';
import { formatINR } from '../components/common/CurrencyDisplay';
import { StatutoryPill } from '../components/common/StatutoryPill';
import {
  PiggyBank,
  AlertCircle,
  Sparkles,
  ArrowRight,
} from 'lucide-react';
import { Link } from 'react-router-dom';

export const InvestmentAnalysisPage: React.FC = () => {
  const { financialYear, regime, showToast } = useTax();
  const [data, setData] = useState<InvestmentAnalysisResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchAnalysis = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.investments.getAnalysis(financialYear, regime);
      setData(res);
    } catch (err: any) {
      showToast('Could not load investment analysis', 'error');
    } finally {
      setLoading(false);
    }
  }, [financialYear, regime, showToast]);

  useEffect(() => {
    fetchAnalysis();
  }, [fetchAnalysis]);

  if (loading || !data) {
    return (
      <div className="p-8 text-center text-xs text-slate-400">
        Analyzing investment instruments and section utilization...
      </div>
    );
  }

  const meter80C = data.section_80c_meter || {
    total_invested: 0,
    cap: 150000,
    allowed: 0,
    remaining_headroom: 150000,
    utilization_pct: 0,
    components: {},
  };
  const meterNPS = data.section_80ccd_1b_nps || {
    invested: 0,
    cap: 50000,
    allowed: 0,
    remaining_headroom: 50000,
  };
  const meter80D = data.section_80d_health || {
    self_family: 0,
    parents: 0,
    preventive_checkup: 0,
    cap: 50000,
    allowed: 0,
    remaining_headroom: 50000,
  };
  const meter24B = data.section_24b_home_loan_interest || {
    interest_paid: 0,
    cap: 200000,
    allowed: 0,
    remaining_headroom: 200000,
  };

  const cap80C = meter80C.cap || (meter80C as any).statutory_cap || 150000;
  const rem80C = meter80C.remaining_headroom ?? (meter80C as any).remaining_limit ?? 0;
  const util80C = meter80C.utilization_pct ?? (meter80C as any).percentage_utilized ?? 0;
  const components80C = meter80C.components || {};

  const capNPS = meterNPS.cap || (meterNPS as any).limit || 50000;
  const invNPS = meterNPS.invested ?? (meterNPS as any).utilized ?? 0;
  const remNPS = meterNPS.remaining_headroom ?? (meterNPS as any).remaining ?? 0;

  const cap80D = meter80D.cap || 50000;
  const claim80D = (meter80D.self_family || 0) + (meter80D.parents || 0);
  const rem80D = meter80D.remaining_headroom ?? 0;

  const cap24B = meter24B.cap || 200000;
  const int24B = meter24B.interest_paid || 0;
  const rem24B = meter24B.remaining_headroom ?? 0;

  const recommendations = Array.isArray(data.recommendations) ? data.recommendations : [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1 rounded bg-indigo-100 text-indigo-700">
              <PiggyBank className="w-5 h-5" />
            </span>
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">
              Investment Analysis & 80C Headroom Meter
            </h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Track utilization against statutory caps for FY {financialYear} under <strong>{regime.toUpperCase()} Regime</strong>.
          </p>
        </div>

        {regime === 'new' && (
          <div className="bg-amber-50 border border-amber-300 rounded-lg p-2.5 text-xs text-amber-800 max-w-sm flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-amber-600 mt-0.5 shrink-0" />
            <span>
              <strong>New Regime Note:</strong> Chapter VI-A deductions (80C, 80D, 80CCD(1B)) are not available in the New Regime. Employer NPS (80CCD(2)) is allowed.
            </span>
          </div>
        )}
      </div>

      {/* Main 80C Combined Meter Card */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-2xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-slate-900">
                Section 80C Combined Utilization Meter
              </h2>
              <StatutoryPill section1961="80C" section2025="80C" />
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Includes EPF, PPF, ELSS, Life Insurance, Home Loan Principal, Tuition Fees, NSC, 5-Yr FD.
            </p>
          </div>

          <div className="text-right">
            <span className="text-xs text-slate-400">Total Invested vs Cap:</span>
            <div className="text-lg font-mono font-bold text-slate-800">
              {formatINR(meter80C.total_invested || 0)} / {formatINR(cap80C)}
            </div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs font-semibold text-slate-700">
            <span>Utilization: {util80C}%</span>
            <span>
              Remaining Headroom:{' '}
              <strong className="text-indigo-600">{formatINR(rem80C)}</strong>
            </span>
          </div>

          <div className="w-full bg-slate-100 rounded-full h-4 overflow-hidden border border-slate-200 p-0.5">
            <div
              className={`h-full rounded-full transition-all duration-700 ${
                util80C >= 100
                  ? 'bg-emerald-500'
                  : util80C > 50
                  ? 'bg-indigo-600'
                  : 'bg-amber-500'
              }`}
              style={{ width: `${Math.min(100, util80C)}%` }}
            />
          </div>
        </div>

        {/* Sub-components breakdown */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
          {Object.entries(components80C).map(([key, amount]) => (
            <div key={key} className="p-3 bg-slate-50 rounded-lg border border-slate-200/60 text-xs">
              <span className="text-slate-500 capitalize">{key.replace(/_/g, ' ')}</span>
              <div className="font-mono font-bold text-slate-800 mt-1">{formatINR(amount as number)}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Other Section Meters Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Section 80CCD(1B) NPS */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs space-y-3">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <div>
              <h3 className="text-sm font-bold text-slate-800">Section 80CCD(1B) NPS</h3>
              <p className="text-[11px] text-slate-400">Additional Tier 1 Contribution</p>
            </div>
            <StatutoryPill section1961="80CCD(1B)" section2025="80CCD(1B)" />
          </div>

          <div className="flex justify-between items-baseline text-xs">
            <span className="text-slate-500">Invested:</span>
            <span className="font-mono font-bold text-slate-800">{formatINR(invNPS)}</span>
          </div>

          <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden border border-slate-200">
            <div
              className="bg-indigo-600 h-full rounded-full"
              style={{ width: `${Math.min(100, (invNPS / (capNPS || 1)) * 100)}%` }}
            />
          </div>

          <div className="flex justify-between items-center text-[11px] pt-1">
            <span className="text-slate-400">Cap: {formatINR(capNPS)}</span>
            <span className="text-indigo-600 font-semibold">
              Remaining: {formatINR(remNPS)}
            </span>
          </div>
        </div>

        {/* Section 80D Health Insurance */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs space-y-3">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <div>
              <h3 className="text-sm font-bold text-slate-800">Section 80D Health Insurance</h3>
              <p className="text-[11px] text-slate-400">Self, Family & Parents</p>
            </div>
            <StatutoryPill section1961="80D" section2025="80D" />
          </div>

          <div className="flex justify-between items-baseline text-xs">
            <span className="text-slate-500">Claimed:</span>
            <span className="font-mono font-bold text-slate-800">
              {formatINR(claim80D)}
            </span>
          </div>

          <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden border border-slate-200">
            <div
              className="bg-emerald-600 h-full rounded-full"
              style={{
                width: `${Math.min(100, (claim80D / (cap80D || 1)) * 100)}%`,
              }}
            />
          </div>

          <div className="flex justify-between items-center text-[11px] pt-1">
            <span className="text-slate-400">Cap: {formatINR(cap80D)}</span>
            <span className="text-emerald-600 font-semibold">
              Remaining: {formatINR(rem80D)}
            </span>
          </div>
        </div>

        {/* Section 24(b) Home Loan Interest */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs space-y-3">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <div>
              <h3 className="text-sm font-bold text-slate-800">Section 24(b) Home Loan</h3>
              <p className="text-[11px] text-slate-400">Self-Occupied Interest Cap</p>
            </div>
            <StatutoryPill section1961="24(b)" section2025="24(b)" />
          </div>

          <div className="flex justify-between items-baseline text-xs">
            <span className="text-slate-500">Interest Paid:</span>
            <span className="font-mono font-bold text-slate-800">{formatINR(int24B)}</span>
          </div>

          <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden border border-slate-200">
            <div
              className="bg-purple-600 h-full rounded-full"
              style={{ width: `${Math.min(100, (int24B / (cap24B || 1)) * 100)}%` }}
            />
          </div>

          <div className="flex justify-between items-center text-[11px] pt-1">
            <span className="text-slate-400">Cap: {formatINR(cap24B)}</span>
            <span className="text-purple-600 font-semibold">
              Remaining: {formatINR(rem24B)}
            </span>
          </div>
        </div>
      </div>

      {/* Actionable Recommendations */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-2xs space-y-4">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-indigo-600" />
          <h2 className="text-sm font-bold text-slate-800">
            Actionable Optimization Recommendations Before Year-End
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {recommendations.map((rec, i) => (
            <div
              key={i}
              className="p-4 rounded-xl border border-indigo-100 bg-indigo-50/40 flex flex-col justify-between text-xs space-y-2"
            >
              <div>
                <div className="flex items-center justify-between">
                  <span className="font-bold text-indigo-900">Section {rec.section}</span>
                  <span className="text-indigo-700 font-semibold">
                    Headroom: {formatINR(rec.headroom)}
                  </span>
                </div>
                <p className="text-slate-600 mt-1 text-[11px] leading-relaxed">{rec.suggestion}</p>
              </div>

              <Link
                to="/what-if"
                className="inline-flex items-center gap-1 text-[11px] font-semibold text-indigo-700 hover:text-indigo-900 mt-2"
              >
                <span>Simulate tax impact in What-If Simulator</span>
                <ArrowRight className="w-3 h-3" />
              </Link>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
