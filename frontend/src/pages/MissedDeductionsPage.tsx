import React, { useState, useEffect, useCallback } from 'react';
import { useTax } from '../context/TaxContext';
import { api } from '../api/client';
import { MissedDeductionsResponse, MissedDeductionItem, ClarifyingQuestion } from '../types';
import { CurrencyDisplay, formatINR } from '../components/common/CurrencyDisplay';
import { StatutoryPill } from '../components/common/StatutoryPill';
import { Link } from 'react-router-dom';
import {
  Sparkles,
  HelpCircle,
  Sliders,
  Send,
} from 'lucide-react';

export const MissedDeductionsPage: React.FC = () => {
  const { financialYear, regime, showToast, refreshAll } = useTax();

  const [advisorData, setAdvisorData] = useState<MissedDeductionsResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [answerInput, setAnswerInput] = useState<{ [qId: string]: any }>({});
  const [submittingQ, setSubmittingQ] = useState<boolean>(false);

  // Manual claim modal
  const [claimingItem, setClaimingItem] = useState<MissedDeductionItem | null>(null);
  const [claimAmount, setClaimAmount] = useState<number>(0);

  const fetchAdvisor = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.deductions.getMissed(financialYear, regime);
      setAdvisorData(res);
    } catch (err: any) {
      showToast('Could not load missed deductions advisor', 'error');
    } finally {
      setLoading(false);
    }
  }, [financialYear, regime, showToast]);

  useEffect(() => {
    fetchAdvisor();
  }, [fetchAdvisor]);

  const handleAnswerQuestion = async (q: ClarifyingQuestion, val: any) => {
    setSubmittingQ(true);
    try {
      await api.deductions.answerQuestion({
        financial_year: financialYear,
        question_id: q.id,
        field_target: q.field_target,
        answer_value: val,
      });
      showToast('Profile updated with your response! Recalculating...', 'success');
      await fetchAdvisor();
      await refreshAll();
    } catch (err: any) {
      showToast('Failed to submit response', 'error');
    } finally {
      setSubmittingQ(false);
    }
  };

  const handleClaimSubmit = async () => {
    if (!claimingItem) return;
    try {
      await api.deductions.answerQuestion({
        financial_year: financialYear,
        question_id: `claim_${claimingItem.section_1961}`,
        field_target: claimingItem.section_1961.toLowerCase().replace(/[^a-z0-9]/g, '_'),
        answer_value: claimAmount,
      });
      showToast(`Claimed ${formatINR(claimAmount)} under Sec ${claimingItem.section_1961}!`, 'success');
      setClaimingItem(null);
      await fetchAdvisor();
      await refreshAll();
    } catch (err: any) {
      showToast('Failed to claim deduction', 'error');
    }
  };

  if (loading || !advisorData) {
    return (
      <div className="p-8 text-center text-xs text-slate-400">
        Scanning statutory rules and tax profile for missed deductions...
      </div>
    );
  }

  const missedList: MissedDeductionItem[] = Array.isArray(advisorData?.missed_deductions)
    ? advisorData.missed_deductions
    : Array.isArray((advisorData as any)?.opportunities)
    ? (advisorData as any).opportunities.map((o: any) => ({
        section_1961: o.section || '',
        section_2025: o.section || '',
        name: o.category || '',
        category: o.category || '',
        max_limit: o.statutory_limit || 0,
        current_claimed: o.claimed_amount || 0,
        potential_additional: o.remaining_eligible || 0,
        estimated_tax_savings: o.estimated_tax_savings || 0,
        status: (o.remaining_eligible || 0) <= 0 ? 'CLAIMED' : 'ELIGIBLE',
        condition_description: o.conditions || '',
        action_needed: o.required_documents || '',
        regime_availability: o.regime_relevance || '',
      }))
    : [];

  const questionsList: ClarifyingQuestion[] = Array.isArray(advisorData?.clarifying_questions)
    ? advisorData.clarifying_questions.map((q: any) => ({
        id: q.id || q.question_id || '',
        question: q.question || q.title || '',
        field_target: q.field_target || '',
        section: q.section || '80',
        input_type: q.input_type === 'currency' ? 'number' : q.input_type || 'number',
        help_text: q.help_text || q.description || '',
      }))
    : [];

  const totalSavings =
    advisorData?.total_potential_tax_savings ??
    (advisorData as any)?.total_potential_savings ??
    0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1 rounded bg-indigo-100 text-indigo-700">
              <Sparkles className="w-5 h-5" />
            </span>
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">
              Missed-Deductions Advisor (Flagship Feature)
            </h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Deterministic gap analysis matching your parsed records against statutory limits for FY {financialYear}.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link
            to="/what-if"
            className="flex items-center gap-1 px-3.5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg shadow-2xs transition-colors"
          >
            <Sliders className="w-4 h-4" />
            <span>Open What-If Simulator</span>
          </Link>
        </div>
      </div>

      {/* Total Potential Savings Highlight */}
      <div className="bg-gradient-to-r from-amber-500/15 via-orange-500/15 to-indigo-500/10 border-2 border-amber-300 rounded-xl p-5 shadow-2xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="w-12 h-12 rounded-xl bg-amber-500 text-white flex items-center justify-center font-bold text-xl shadow-xs shrink-0">
            ₹
          </div>
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-amber-900">
              Maximum Additional Tax Savings Available
            </span>
            <div className="text-2xl font-bold font-mono text-amber-900 mt-0.5">
              <CurrencyDisplay amount={totalSavings} />
            </div>
            <p className="text-xs text-amber-800 mt-1">
              {missedList.filter((d) => d.status !== 'CLAIMED').length} eligible opportunities detected under the statutory framework.
            </p>
          </div>
        </div>

        <div className="text-right text-xs text-amber-800">
          <p className="font-semibold">Statutory Basis:</p>
          <p className="text-[11px] text-amber-700">Rule-driven conditions check</p>
        </div>
      </div>

      {/* Interactive Clarifying Questionnaire (Ambiguity Resolver) */}
      {questionsList.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-2xs overflow-hidden">
          <div className="p-4 border-b border-slate-100 bg-indigo-50/50 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <HelpCircle className="w-4 h-4 text-indigo-700" />
              <h2 className="text-sm font-bold text-slate-800">
                Clarifying Eligibility Questionnaire ({questionsList.length} questions)
              </h2>
            </div>
            <span className="text-[10px] font-semibold bg-indigo-100 text-indigo-800 px-2 py-0.5 rounded">
              Answers Update Tax Live
            </span>
          </div>

          <div className="divide-y divide-slate-100">
            {questionsList.map((q) => (
              <div key={q.id} className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 text-xs">
                <div className="space-y-1 max-w-xl">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-slate-800">{q.question}</span>
                    <span className="text-[10px] px-1.5 py-0.2 bg-slate-100 text-slate-600 rounded font-mono">
                      Sec {q.section}
                    </span>
                  </div>
                  <p className="text-slate-500 text-[11px]">{q.help_text}</p>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  {q.input_type === 'boolean' ? (
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleAnswerQuestion(q, true)}
                        disabled={submittingQ}
                        className="px-3 py-1.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-semibold rounded-md border border-indigo-200 transition-colors"
                      >
                        Yes
                      </button>
                      <button
                        onClick={() => handleAnswerQuestion(q, false)}
                        disabled={submittingQ}
                        className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-md transition-colors"
                      >
                        No
                      </button>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2">
                      <input
                        type="number"
                        placeholder="Enter amount..."
                        value={answerInput[q.id] || ''}
                        onChange={(e) =>
                          setAnswerInput({ ...answerInput, [q.id]: Number(e.target.value) })
                        }
                        className="w-32 p-1.5 border border-slate-300 rounded font-mono text-xs"
                      />
                      <button
                        onClick={() => handleAnswerQuestion(q, answerInput[q.id])}
                        disabled={submittingQ || !answerInput[q.id]}
                        className="p-1.5 bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50"
                        title="Submit answer"
                      >
                        <Send className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Missed Deductions Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {missedList.map((item, idx) => {
          const isClaimed = item.status === 'CLAIMED';
          return (
            <div
              key={idx}
              className={`p-5 rounded-xl border transition-all flex flex-col justify-between text-xs space-y-3 ${
                isClaimed
                  ? 'bg-emerald-50/40 border-emerald-200'
                  : 'bg-white border-slate-200 shadow-2xs hover:border-indigo-300'
              }`}
            >
              <div>
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-bold text-slate-900">{item.name}</h3>
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                          isClaimed
                            ? 'bg-emerald-100 text-emerald-800'
                            : 'bg-amber-100 text-amber-800'
                        }`}
                      >
                        {item.status}
                      </span>
                    </div>

                    <div className="mt-1">
                      <StatutoryPill
                        section1961={item.section_1961}
                        section2025={item.section_2025}
                      />
                    </div>
                  </div>

                  <div className="text-right">
                    <span className="text-[10px] text-slate-400">Est. Tax Savings</span>
                    <div className="text-base font-bold font-mono text-emerald-600">
                      {formatINR(item.estimated_tax_savings)}
                    </div>
                  </div>
                </div>

                <p className="text-slate-600 text-[11px] mt-2 leading-relaxed">
                  {item.condition_description}
                </p>

                {/* Utilization meter inside card */}
                <div className="mt-3 p-2.5 bg-slate-50 rounded-lg border border-slate-100 space-y-1">
                  <div className="flex justify-between text-[11px] text-slate-500">
                    <span>
                      Claimed: <strong>{formatINR(item.current_claimed)}</strong>
                    </span>
                    <span>
                      Headroom: <strong className="text-indigo-600">{formatINR(item.potential_additional)}</strong>
                    </span>
                  </div>
                  <div className="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
                    <div
                      className={`h-full rounded-full ${isClaimed ? 'bg-emerald-500' : 'bg-indigo-600'}`}
                      style={{
                        width: `${Math.min(100, (item.current_claimed / (item.max_limit || 1)) * 100)}%`,
                      }}
                    />
                  </div>
                </div>
              </div>

              <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[11px]">
                <span className="text-slate-400 italic">{item.action_needed}</span>

                {!isClaimed && (
                  <button
                    onClick={() => {
                      setClaimingItem(item);
                      setClaimAmount(item.potential_additional);
                    }}
                    className="px-3 py-1 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-md shadow-2xs transition-colors cursor-pointer"
                  >
                    Claim This
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Claim Modal */}
      {claimingItem && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-sm w-full p-5 space-y-4 border border-slate-200">
            <div className="flex items-center gap-2">
              <div className="p-2 rounded-lg bg-indigo-100 text-indigo-700">
                <Sparkles className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-800">
                  Claim Section {claimingItem.section_1961}
                </h3>
                <p className="text-[11px] text-slate-500">{claimingItem.name}</p>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Amount to Claim (Max Headroom: {formatINR(claimingItem.potential_additional)})
              </label>
              <input
                type="number"
                value={claimAmount}
                onChange={(e) => setClaimAmount(Number(e.target.value))}
                max={claimingItem.potential_additional}
                className="w-full text-xs p-2.5 border border-slate-300 rounded-lg font-mono focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setClaimingItem(null)}
                className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-md"
              >
                Cancel
              </button>
              <button
                onClick={handleClaimSubmit}
                className="px-4 py-1.5 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-md"
              >
                Confirm & Recompute
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
