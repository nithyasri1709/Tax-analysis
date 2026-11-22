import React, { useEffect, useState } from 'react';
import { useTax } from '../context/TaxContext';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/client';
import { CurrencyDisplay, formatINR } from '../components/common/CurrencyDisplay';
import { StatutoryPill } from '../components/common/StatutoryPill';
import { Link } from 'react-router-dom';
import {
  ArrowRight,
  UploadCloud,
  FileCheck2,
  Sliders,
  Sparkles,
  Scale,
  FileText,
  CheckCircle2,
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

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const { financialYear, regime, setRegime, profile, comparisonResult } = useTax();

  const [missedSummary, setMissedSummary] = useState<any>(null);

  useEffect(() => {
    const fetchMissed = async () => {
      try {
        const res = await api.deductions.getMissed(financialYear, regime);
        setMissedSummary(res);
      } catch (err) {
        console.warn('Could not load missed deductions summary', err);
      }
    };
    fetchMissed();
  }, [financialYear, regime]);

  const activeTaxResult =
    regime === 'new' ? comparisonResult?.new_regime : comparisonResult?.old_regime;

  const grossTotal = activeTaxResult?.gross_total_income ?? 0;
  const deductionsTotal =
    activeTaxResult?.total_deductions_allowed ??
    (activeTaxResult as any)?.total_chapter_vi_a_deductions ??
    0;
  const netTaxLiability =
    activeTaxResult?.total_tax_liability ??
    (activeTaxResult as any)?.gross_tax_liability ??
    0;

  const regimeSavings =
    comparisonResult?.tax_savings ??
    comparisonResult?.tax_difference ??
    (comparisonResult as any)?.tax_diff ??
    0;

  const missedSavings =
    missedSummary?.total_potential_tax_savings ??
    missedSummary?.total_potential_savings ??
    0;

  const missedCount =
    missedSummary?.missed_deductions?.length ??
    missedSummary?.opportunities?.length ??
    0;

  const breakEven =
    comparisonResult?.break_even_deduction ??
    (comparisonResult as any)?.break_even_deductions ??
    0;

  const recRegime = comparisonResult?.recommended_regime || 'new';
  const recReason =
    comparisonResult?.reason ||
    (comparisonResult as any)?.plain_language_explanation ||
    'Comparing Old vs New Regime based on statutory calculations.';

  const oldR = comparisonResult?.old_regime;
  const newR = comparisonResult?.new_regime;

  const chartData = [
    {
      name: 'Gross Income',
      'Old Regime': oldR?.gross_total_income ?? 0,
      'New Regime': newR?.gross_total_income ?? 0,
    },
    {
      name: 'Deductions',
      'Old Regime': oldR?.total_deductions_allowed ?? (oldR as any)?.total_chapter_vi_a_deductions ?? 0,
      'New Regime': newR?.total_deductions_allowed ?? (newR as any)?.total_chapter_vi_a_deductions ?? 0,
    },
    {
      name: 'Taxable Income',
      'Old Regime': oldR?.taxable_income ?? (oldR as any)?.taxable_total_income ?? 0,
      'New Regime': newR?.taxable_income ?? (newR as any)?.taxable_total_income ?? 0,
    },
    {
      name: 'Tax Payable',
      'Old Regime': oldR?.total_tax_liability ?? (oldR as any)?.gross_tax_liability ?? 0,
      'New Regime': newR?.total_tax_liability ?? (newR as any)?.gross_tax_liability ?? 0,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Top Welcome & Summary Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-5 rounded-xl border border-slate-200 shadow-2xs">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">
              Welcome back, {user?.full_name || 'Taxpayer'}
            </h1>
            <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200">
              {user?.employment_type?.toUpperCase()}
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Indian Income Tax Planning Overview for <strong>FY {financialYear}</strong> ({financialYear === '2026-27' ? 'Tax Year 2026-27 under Income-tax Act 2025' : 'AY 2026-27 under 1961 Act'})
          </p>
        </div>

        {/* Profile Completeness Bar */}
        <div className="flex flex-col sm:items-end min-w-[220px]">
          <div className="flex items-center justify-between w-full text-xs mb-1">
            <span className="text-slate-500 font-medium">Profile Completeness</span>
            <span className="font-bold text-indigo-700">{profile?.completeness_score || 35}%</span>
          </div>
          <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden border border-slate-200">
            <div
              className="bg-indigo-600 h-2 rounded-full transition-all duration-500"
              style={{ width: `${profile?.completeness_score || 35}%` }}
            />
          </div>
          <Link
            to="/wizard"
            className="text-[11px] text-indigo-600 hover:text-indigo-800 font-semibold mt-1 flex items-center gap-1"
          >
            <span>Complete 13-step wizard</span>
            <ArrowRight className="w-3 h-3" />
          </Link>
        </div>
      </div>

      {/* 4 Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Gross Total Income */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
          <span className="text-xs font-medium text-slate-500">Gross Total Income</span>
          <div className="text-2xl font-bold text-slate-900 mt-1">
            <CurrencyDisplay amount={grossTotal} />
          </div>
          <div className="flex items-center justify-between mt-3 pt-2 border-t border-slate-100 text-[11px]">
            <span className="text-slate-400">Salary + Property + Other</span>
            <Link to="/income" className="text-indigo-600 font-semibold hover:underline">
              Inspect
            </Link>
          </div>
        </div>

        {/* Deductions Claimed */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
          <span className="text-xs font-medium text-slate-500">Deductions Allowed</span>
          <div className="text-2xl font-bold text-emerald-600 mt-1">
            <CurrencyDisplay amount={deductionsTotal} />
          </div>
          <div className="flex items-center justify-between mt-3 pt-2 border-t border-slate-100 text-[11px]">
            <span className="text-slate-400">
              {regime === 'new' ? 'Std Ded (₹75k) + NPS' : '80C, 80D, 24(b), etc.'}
            </span>
            <Link to="/investments" className="text-indigo-600 font-semibold hover:underline">
              80C Meter
            </Link>
          </div>
        </div>

        {/* Estimated Tax Liability */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">Net Tax Liability</span>
            <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-slate-100 text-slate-700 uppercase">
              {regime} regime
            </span>
          </div>
          <div className="text-2xl font-bold text-slate-900 mt-1">
            <CurrencyDisplay amount={netTaxLiability} />
          </div>
          <div className="flex items-center justify-between mt-3 pt-2 border-t border-slate-100 text-[11px]">
            <span className="text-slate-400">Incl. Cess & Relief</span>
            <Link to="/calculation" className="text-indigo-600 font-semibold hover:underline">
              View Steps
            </Link>
          </div>
        </div>

        {/* Potential Tax Savings */}
        <div className="bg-gradient-to-br from-indigo-50 to-purple-50 p-4 rounded-xl border border-indigo-200 shadow-2xs">
          <div className="flex items-center gap-1.5">
            <Sparkles className="w-4 h-4 text-indigo-600" />
            <span className="text-xs font-semibold text-indigo-900">Potential Tax Savings</span>
          </div>
          <div className="text-2xl font-bold text-indigo-700 mt-1">
            <CurrencyDisplay amount={regimeSavings + missedSavings} />
          </div>
          <div className="flex items-center justify-between mt-3 pt-2 border-t border-indigo-100 text-[11px]">
            <span className="text-indigo-700 font-medium">Regime diff + Missed</span>
            <Link to="/missed-deductions" className="text-indigo-800 font-bold hover:underline">
              Claim Now
            </Link>
          </div>
        </div>
      </div>

      {/* Winning Regime Recommendation Card */}
      {comparisonResult && (
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-2xs flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0">
              <Scale className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider text-emerald-700">
                  Recommendation Engine Result
                </span>
                <span className="text-[11px] px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-semibold">
                  {recRegime.toUpperCase()} REGIME WINS
                </span>
              </div>
              <h3 className="text-base font-bold text-slate-900 mt-0.5">
                {recReason}
              </h3>
              <p className="text-xs text-slate-500 mt-1">
                Tax Difference: <strong className="text-slate-800">{formatINR(regimeSavings)}</strong> • Break-even deductions point: <strong className="text-slate-800">{formatINR(breakEven)}</strong>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {regime !== recRegime && (
              <button
                onClick={() => setRegime(recRegime as 'new' | 'old')}
                className="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-lg shadow-2xs transition-colors cursor-pointer"
              >
                Switch to {recRegime.toUpperCase()} Regime
              </button>
            )}
            <Link
              to="/regimes"
              className="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg transition-colors"
            >
              Side-by-Side Comparison
            </Link>
          </div>
        </div>
      )}

      {/* Missed Deductions Banner */}
      {missedSavings > 0 && (
        <div className="bg-gradient-to-r from-amber-500/10 via-orange-500/10 to-amber-500/5 border border-amber-300 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-amber-500 text-white flex items-center justify-center font-bold">
              !
            </div>
            <div>
              <p className="text-xs font-bold text-amber-900">
                You could save up to <CurrencyDisplay amount={missedSavings} /> in missed deductions!
              </p>
              <p className="text-[11px] text-amber-800 mt-0.5">
                Our advisor found {missedCount} unutilized opportunities (e.g. NPS, Health Insurance, Rent). Answer 2 quick questions to claim them.
              </p>
            </div>
          </div>
          <Link
            to="/missed-deductions"
            className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white text-xs font-semibold rounded-lg shrink-0 shadow-xs text-center"
          >
            Review Missed Deductions
          </Link>
        </div>
      )}

      {/* Comparison Chart & Quick Actions Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Recharts Bar Chart */}
        <div className="lg:col-span-8 bg-white p-5 rounded-xl border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-bold text-slate-800">Old vs New Regime Statutory Comparison</h2>
              <p className="text-xs text-slate-400">Breakdown of Income, Deductions, and Final Tax Liability</p>
            </div>
            <StatutoryPill section1961="115BAC" section2025="115BAC" />
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#64748b' }} />
                <YAxis
                  tick={{ fontSize: 10, fill: '#64748b' }}
                  tickFormatter={(val) => `₹${val / 1000}k`}
                />
                <Tooltip
                  formatter={(val: any) => [formatINR(val), '']}
                  contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', borderRadius: '8px', fontSize: '12px' }}
                />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                <Bar dataKey="Old Regime" fill="#94a3b8" radius={[4, 4, 0, 0]} />
                <Bar dataKey="New Regime" fill="#4f46e5" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Right: Quick Launchpad */}
        <div className="lg:col-span-4 bg-white p-5 rounded-xl border border-slate-200 shadow-2xs flex flex-col justify-between">
          <div>
            <h2 className="text-sm font-bold text-slate-800">Quick Tax Launchpad</h2>
            <p className="text-xs text-slate-400 mt-0.5">Jump directly to your active workflows</p>

            <div className="mt-4 space-y-2.5">
              <Link
                to="/upload"
                className="flex items-center gap-3 p-2.5 rounded-lg border border-slate-100 hover:border-indigo-200 hover:bg-indigo-50/50 transition-all text-xs"
              >
                <div className="p-2 rounded bg-indigo-100 text-indigo-700">
                  <UploadCloud className="w-4 h-4" />
                </div>
                <div>
                  <p className="font-semibold text-slate-800">Upload Documents</p>
                  <p className="text-[11px] text-slate-500">PDFs, Salary Slips, AIS, Form 16</p>
                </div>
              </Link>

              <Link
                to="/extraction"
                className="flex items-center gap-3 p-2.5 rounded-lg border border-slate-100 hover:border-indigo-200 hover:bg-indigo-50/50 transition-all text-xs"
              >
                <div className="p-2 rounded bg-purple-100 text-purple-700">
                  <FileCheck2 className="w-4 h-4" />
                </div>
                <div>
                  <p className="font-semibold text-slate-800">Verification Workbench</p>
                  <p className="text-[11px] text-slate-500">Review OCR confidence & edit fields</p>
                </div>
              </Link>

              <Link
                to="/what-if"
                className="flex items-center gap-3 p-2.5 rounded-lg border border-slate-100 hover:border-indigo-200 hover:bg-indigo-50/50 transition-all text-xs"
              >
                <div className="p-2 rounded bg-emerald-100 text-emerald-700">
                  <Sliders className="w-4 h-4" />
                </div>
                <div>
                  <p className="font-semibold text-slate-800">What-If Simulator</p>
                  <p className="text-[11px] text-slate-500">Interactive live investment sliders</p>
                </div>
              </Link>

              <Link
                to="/reports"
                className="flex items-center gap-3 p-2.5 rounded-lg border border-slate-100 hover:border-indigo-200 hover:bg-indigo-50/50 transition-all text-xs"
              >
                <div className="p-2 rounded bg-amber-100 text-amber-700">
                  <FileText className="w-4 h-4" />
                </div>
                <div>
                  <p className="font-semibold text-slate-800">16-Section Tax PDF</p>
                  <p className="text-[11px] text-slate-500">Generate & download audit-proof report</p>
                </div>
              </Link>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
            <span>Deterministic engine</span>
            <span className="text-emerald-600 font-semibold flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" /> Ready for FY {financialYear}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
