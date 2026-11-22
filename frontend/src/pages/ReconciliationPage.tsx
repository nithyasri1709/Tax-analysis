import React, { useState, useEffect, useCallback } from 'react';
import { useTax } from '../context/TaxContext';
import { api } from '../api/client';
import { ReconciliationResponse } from '../types';
import { CurrencyDisplay, formatINR } from '../components/common/CurrencyDisplay';
import { StatutoryPill } from '../components/common/StatutoryPill';
import {
  GitCompare,
  CheckCircle,
  AlertTriangle,
  AlertCircle,
  ShieldCheck,
  Info,
  ExternalLink,
} from 'lucide-react';

export const ReconciliationPage: React.FC = () => {
  const { financialYear, showToast } = useTax();

  const [data, setData] = useState<ReconciliationResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchRecon = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.reconciliation.getSummary(financialYear);
      setData(res);
    } catch (err: any) {
      showToast('Could not load reconciliation data', 'error');
    } finally {
      setLoading(false);
    }
  }, [financialYear, showToast]);

  useEffect(() => {
    fetchRecon();
  }, [fetchRecon]);

  if (loading || !data) {
    return (
      <div className="p-8 text-center text-xs text-slate-400">
        Cross-checking Form 16, Form 26AS, and AIS/TIS figures...
      </div>
    );
  }

  const summary = (data as any)?.summary || {
    tds_salary_form16: 0,
    tds_total_26as: 0,
    gross_income_ais: 0,
    tds_credit_status: 'MATCHED',
  };
  const sources_matched = (data as any)?.sources_matched || {
    form_16: false,
    form_26as: false,
    ais_tis: false,
  };
  const discrepancies: any[] = Array.isArray((data as any)?.discrepancies) ? (data as any).discrepancies : [];
  const notes: string[] = Array.isArray((data as any)?.notes) ? (data as any).notes : [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1 rounded bg-indigo-100 text-indigo-700">
              <GitCompare className="w-5 h-5" />
            </span>
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">
              Form 16 / 26AS / AIS Cross-Reconciliation
            </h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Automated multi-way cross-verification to prevent defective return notices under Section 139(9).
          </p>
        </div>

        <StatutoryPill section1961="139(9)" section2025="139(9)" />
      </div>

      {/* Verification Health Status Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs flex items-center justify-between">
          <div>
            <span className="text-xs font-medium text-slate-500">TDS on Salary (Form 16)</span>
            <div className="text-lg font-bold font-mono text-slate-800 mt-0.5">
              {formatINR(summary.tds_salary_form16)}
            </div>
            <span className="text-[10px] text-slate-400">Employer Part A credit</span>
          </div>
          <div
            className={`p-2 rounded-full ${
              sources_matched.form_16 ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-400'
            }`}
          >
            <CheckCircle className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs flex items-center justify-between">
          <div>
            <span className="text-xs font-medium text-slate-500">Total TDS Deposited (26AS)</span>
            <div className="text-lg font-bold font-mono text-slate-800 mt-0.5">
              {formatINR(summary.tds_total_26as)}
            </div>
            <span className="text-[10px] text-slate-400">ITD portal ledger</span>
          </div>
          <div
            className={`p-2 rounded-full ${
              sources_matched.form_26as ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-400'
            }`}
          >
            <CheckCircle className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs flex items-center justify-between">
          <div>
            <span className="text-xs font-medium text-slate-500">Annual Gross Income (AIS)</span>
            <div className="text-lg font-bold font-mono text-slate-800 mt-0.5">
              {formatINR(summary.gross_income_ais)}
            </div>
            <span className="text-[10px] text-slate-400">Comprehensive TIS statement</span>
          </div>
          <div
            className={`p-2 rounded-full ${
              sources_matched.ais_tis ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-400'
            }`}
          >
            <CheckCircle className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Discrepancies Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-2xs overflow-hidden">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50">
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-bold text-slate-800">
              Cross-Source Discrepancies & Variances ({discrepancies.length})
            </h2>
          </div>
          <span className="text-xs font-semibold text-emerald-700 bg-emerald-100 px-2.5 py-0.5 rounded">
            {discrepancies.length === 0 ? 'All Sources Reconciled' : 'Review Required'}
          </span>
        </div>

        {discrepancies.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-400 flex flex-col items-center gap-2">
            <ShieldCheck className="w-8 h-8 text-emerald-500" />
            <p className="font-semibold text-slate-700">Perfect Match across all official documents!</p>
            <p className="text-slate-400 max-w-sm">
              No TDS shortfalls or unreported interest income found between Form 16, Form 26AS, and AIS.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-b border-slate-100 text-slate-500 uppercase text-[10px]">
                <tr>
                  <th className="py-2.5 px-4 font-semibold">Field Name</th>
                  <th className="py-2.5 px-4 font-semibold">Source 1</th>
                  <th className="py-2.5 px-4 font-semibold">Source 2</th>
                  <th className="py-2.5 px-4 font-semibold text-right">Variance</th>
                  <th className="py-2.5 px-4 font-semibold text-center">Severity</th>
                  <th className="py-2.5 px-4 font-semibold">Suggested Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-mono">
                {discrepancies.map((d, idx) => (
                  <tr key={idx} className="hover:bg-slate-50/50">
                    <td className="py-3 px-4 font-sans font-medium text-slate-800">{d.field}</td>
                    <td className="py-3 px-4 text-slate-700">
                      <span className="font-sans text-[11px] text-slate-400 block">{d.source_1}:</span>
                      {formatINR(d.val_1)}
                    </td>
                    <td className="py-3 px-4 text-slate-700">
                      <span className="font-sans text-[11px] text-slate-400 block">{d.source_2}:</span>
                      {formatINR(d.val_2)}
                    </td>
                    <td className="py-3 px-4 text-right font-bold text-amber-800">
                      {formatINR(d.difference)}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span
                        className={`text-[10px] font-sans font-bold px-2 py-0.5 rounded-full ${
                          d.severity === 'CRITICAL'
                            ? 'bg-rose-100 text-rose-800'
                            : d.severity === 'WARNING'
                            ? 'bg-amber-100 text-amber-800'
                            : 'bg-indigo-100 text-indigo-800'
                        }`}
                      >
                        {d.severity}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-sans text-slate-600 max-w-xs">{d.recommendation || d.message || 'Verify document values.'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Statutory Guidance Notes */}
      <div className="bg-slate-100/60 p-4 rounded-xl border border-slate-200 text-xs text-slate-600 space-y-2">
        <div className="flex items-center gap-1.5 font-bold text-slate-800">
          <Info className="w-4 h-4 text-indigo-600" />
          <span>Statutory Compliance Guidance</span>
        </div>
        <ul className="list-disc list-inside space-y-1 text-[11px] text-slate-500">
          <li>
            Always ensure that the TDS claimed in your ITR exactly matches the amount appearing in
            <strong> Form 26AS</strong> under the employer's TAN.
          </li>
          <li>
            Income Tax Department algorithms cross-check AIS information automatically against filed
            ITRs. Any discrepancies in interest income or dividends can trigger automated notice under
            Section 143(1)(a).
          </li>
        </ul>
      </div>
    </div>
  );
};
