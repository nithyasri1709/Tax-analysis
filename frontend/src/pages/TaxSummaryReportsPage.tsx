import React, { useState, useEffect, useCallback } from 'react';
import { useTax } from '../context/TaxContext';
import { api } from '../api/client';
import { ReportItem } from '../types';
import { CurrencyDisplay, formatINR } from '../components/common/CurrencyDisplay';
import {
  FileText,
  Download,
  Plus,
  GitCompare,
  Clock,
  Sparkles,
  CheckCircle,
  FileCheck,
  Eye,
  X,
} from 'lucide-react';

export const TaxSummaryReportsPage: React.FC = () => {
  const { financialYear, regime, showToast } = useTax();

  const [reports, setReports] = useState<ReportItem[]>([]);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);

  // Compare reports state
  const [compareModalOpen, setCompareModalOpen] = useState<boolean>(false);
  const [selectedRep1, setSelectedRep1] = useState<string>('');
  const [selectedRep2, setSelectedRep2] = useState<string>('');
  const [compareResult, setCompareResult] = useState<any>(null);
  const [isComparing, setIsComparing] = useState<boolean>(false);

  const fetchReports = useCallback(async () => {
    try {
      const data = await api.reports.list(financialYear);
      setReports(data);
      if (data.length >= 2) {
        setSelectedRep1(data[0].id);
        setSelectedRep2(data[1].id);
      }
    } catch (err: any) {
      showToast('Could not load generated reports list', 'error');
    }
  }, [financialYear, showToast]);

  useEffect(() => {
    fetchReports();
  }, [fetchReports]);

  const handleGenerateReport = async () => {
    setIsGenerating(true);
    try {
      const rep = await api.reports.generate(financialYear);
      showToast(`Generated 16-section report: ${rep.file_name}`, 'success');
      await fetchReports();
    } catch (err: any) {
      showToast('Failed to generate tax report', 'error');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleCompare = async () => {
    if (!selectedRep1 || !selectedRep2) return;
    setIsComparing(true);
    try {
      const res = await api.reports.compare(selectedRep1, selectedRep2);
      setCompareResult(res);
    } catch (err: any) {
      showToast('Failed to compare reports', 'error');
    } finally {
      setIsComparing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1 rounded bg-indigo-100 text-indigo-700">
              <FileText className="w-5 h-5" />
            </span>
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">
              16-Section Statutory Tax Summary Reports
            </h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Audit-proof ReportLab PDF reports complete with calculation traces, document logs, and statutory citations.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {reports.length >= 2 && (
            <button
              onClick={() => setCompareModalOpen(true)}
              className="flex items-center gap-1.5 px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg transition-colors cursor-pointer"
            >
              <GitCompare className="w-4 h-4" />
              <span>Compare Reports</span>
            </button>
          )}

          <button
            onClick={handleGenerateReport}
            disabled={isGenerating}
            className="flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg shadow-2xs transition-colors cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>{isGenerating ? 'Generating 16 Sections...' : 'Generate New PDF Report'}</span>
          </button>
        </div>
      </div>

      {/* Reports Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-2xs overflow-hidden">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50 text-xs text-slate-500">
          <span className="font-semibold text-slate-700">Generated Reports ({reports.length})</span>
          <span>Financial Year: {financialYear}</span>
        </div>

        {reports.length === 0 ? (
          <div className="p-12 text-center text-xs text-slate-400 space-y-3">
            <FileText className="w-10 h-10 mx-auto text-slate-300" />
            <p>No reports generated yet for FY {financialYear}.</p>
            <button
              onClick={handleGenerateReport}
              disabled={isGenerating}
              className="px-4 py-2 bg-indigo-600 text-white font-semibold rounded-lg shadow-xs hover:bg-indigo-700"
            >
              Generate First Tax Report
            </button>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {reports.map((rep) => {
              const summary = rep.report_summary || {};
              return (
                <div
                  key={rep.id}
                  className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-slate-50/70 transition-colors"
                >
                  <div className="flex items-start gap-3">
                    <div className="p-2.5 rounded-lg bg-indigo-50 text-indigo-700 mt-0.5">
                      <FileCheck className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-slate-800">{rep.file_name}</span>
                        <span className="text-[10px] px-2 py-0.5 rounded-full font-semibold bg-emerald-100 text-emerald-800 uppercase">
                          {summary.recommended_regime || regime} Regime
                        </span>
                      </div>

                      <div className="flex items-center gap-3 mt-1 text-[11px] text-slate-500">
                        <span>Generated: {new Date(rep.created_at).toLocaleString()}</span>
                        <span>•</span>
                        <span>
                          Taxable Income:{' '}
                          <strong className="text-slate-700">
                            {formatINR(summary.taxable_income || 0)}
                          </strong>
                        </span>
                        <span>•</span>
                        <span>
                          Tax Liability:{' '}
                          <strong className="text-indigo-700 font-mono">
                            {formatINR(summary.tax_liability || 0)}
                          </strong>
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 self-end sm:self-center">
                    <a
                      href={api.reports.getDownloadUrl(rep.id)}
                      target="_blank"
                      rel="noreferrer"
                      className="flex items-center gap-1.5 px-3.5 py-1.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-xs font-semibold rounded-md border border-indigo-200 transition-colors"
                    >
                      <Download className="w-3.5 h-3.5" />
                      <span>Download PDF</span>
                    </a>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Compare Reports Modal */}
      {compareModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full p-6 space-y-4 border border-slate-200">
            <div className="flex items-center justify-between border-b pb-2">
              <div className="flex items-center gap-2">
                <GitCompare className="w-5 h-5 text-indigo-600" />
                <h3 className="text-sm font-bold text-slate-800">Compare Two Tax Reports</h3>
              </div>
              <button
                onClick={() => setCompareModalOpen(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-4 text-xs">
              <div>
                <label className="font-semibold text-slate-700 mb-1 block">Baseline Report</label>
                <select
                  value={selectedRep1}
                  onChange={(e) => setSelectedRep1(e.target.value)}
                  className="w-full p-2 border border-slate-300 rounded-lg text-xs"
                >
                  {reports.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.file_name} ({new Date(r.created_at).toLocaleDateString()})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="font-semibold text-slate-700 mb-1 block">Comparison Report</label>
                <select
                  value={selectedRep2}
                  onChange={(e) => setSelectedRep2(e.target.value)}
                  className="w-full p-2 border border-slate-300 rounded-lg text-xs"
                >
                  {reports.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.file_name} ({new Date(r.created_at).toLocaleDateString()})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex justify-end">
              <button
                onClick={handleCompare}
                disabled={isComparing || selectedRep1 === selectedRep2}
                className="px-4 py-1.5 bg-indigo-600 text-white font-semibold rounded-lg text-xs shadow-xs hover:bg-indigo-700"
              >
                {isComparing ? 'Comparing...' : 'Run Side-by-Side Comparison'}
              </button>
            </div>

            {compareResult && (
              <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg space-y-3 text-xs">
                <div className="flex justify-between items-center text-sm font-bold text-slate-900 border-b pb-2">
                  <span>Net Tax Variance:</span>
                  <span
                    className={`font-mono ${
                      compareResult.tax_diff <= 0 ? 'text-emerald-700' : 'text-rose-700'
                    }`}
                  >
                    {formatINR(compareResult.tax_diff)}
                  </span>
                </div>
                <p className="text-slate-600 leading-relaxed">{compareResult.analysis}</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
