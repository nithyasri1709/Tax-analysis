import React, { useState, useEffect, useCallback } from 'react';
import { useTax } from '../context/TaxContext';
import { api } from '../api/client';
import { WhatIfResponse } from '../types';
import { formatINR } from '../components/common/CurrencyDisplay';
import {
  Sliders,
  TrendingDown,
  RefreshCw,
} from 'lucide-react';

export const WhatIfSimulatorPage: React.FC = () => {
  const { financialYear, regime } = useTax();

  // Slider states
  const [additional80C, setAdditional80C] = useState<number>(50000);
  const [additionalNPS, setAdditionalNPS] = useState<number>(50000);
  const [additional80D, setAdditional80D] = useState<number>(25000);
  const [additionalEmployerNPS, setAdditionalEmployerNPS] = useState<number>(0);

  const [simResult, setSimResult] = useState<WhatIfResponse | null>(null);
  const [isSimulating, setIsSimulating] = useState<boolean>(false);

  const runSimulation = useCallback(async () => {
    setIsSimulating(true);
    try {
      const res = await api.deductions.whatIf({
        financial_year: financialYear,
        regime: regime,
        additional_80c: additional80C,
        additional_nps_tier1: additionalNPS,
        additional_80d_health: additional80D,
        additional_employer_nps: additionalEmployerNPS,
      });
      setSimResult(res);
    } catch (err: any) {
      console.warn('Simulation error:', err);
    } finally {
      setIsSimulating(false);
    }
  }, [financialYear, regime, additional80C, additionalNPS, additional80D, additionalEmployerNPS]);

  useEffect(() => {
    runSimulation();
  }, [runSimulation]);

  const taxSaved = simResult ? (simResult.tax_saved ?? (simResult as any).tax_savings ?? 0) : 0;
  const baseTax = simResult?.baseline_tax ?? 0;
  const simTax = simResult?.simulated_tax ?? 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1 rounded bg-indigo-100 text-indigo-700">
              <Sliders className="w-5 h-5" />
            </span>
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">
              Interactive What-If Tax Simulator
            </h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Simulate real-time tax savings by adjusting investment sliders for FY {financialYear} under{' '}
            <strong>{regime.toUpperCase()} Regime</strong>.
          </p>
        </div>

        <button
          onClick={runSimulation}
          disabled={isSimulating}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg transition-colors cursor-pointer"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isSimulating ? 'animate-spin' : ''}`} />
          <span>{isSimulating ? 'Recalculating...' : 'Refresh Simulation'}</span>
        </button>
      </div>

      {/* Hero Savings Result Card */}
      {simResult && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs">
            <span className="text-xs font-medium text-slate-500">Baseline Tax Liability</span>
            <div className="text-2xl font-bold font-mono text-slate-800 mt-1">
              {formatINR(baseTax)}
            </div>
            <span className="text-[10px] text-slate-400">Current financial profile</span>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs">
            <span className="text-xs font-medium text-slate-500">Simulated Tax Liability</span>
            <div className="text-2xl font-bold font-mono text-indigo-700 mt-1">
              {formatINR(simTax)}
            </div>
            <span className="text-[10px] text-slate-400">With planned investments</span>
          </div>

          <div className="bg-gradient-to-br from-emerald-500/15 via-teal-500/15 to-emerald-500/5 border-2 border-emerald-400 p-5 rounded-xl shadow-2xs">
            <div className="flex items-center gap-1 text-emerald-800 text-xs font-bold uppercase tracking-wider">
              <TrendingDown className="w-4 h-4 text-emerald-600" />
              <span>Net Tax Saved in Cash</span>
            </div>
            <div className="text-3xl font-extrabold font-mono text-emerald-700 mt-1">
              {formatINR(taxSaved)}
            </div>
            <span className="text-[11px] text-emerald-800 font-semibold mt-1 block">
              Additional Planned Investments: +{formatINR(additional80C + additionalNPS + additional80D + additionalEmployerNPS)}
            </span>
          </div>
        </div>
      )}

      {/* Interactive Sliders Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Slider 1: 80C */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-xs font-bold text-slate-800">Additional Section 80C</span>
              <p className="text-[11px] text-slate-400">ELSS Mutual Funds, PPF, Life Insurance</p>
            </div>
            <span className="font-mono font-bold text-indigo-700 text-sm">
              {formatINR(additional80C)}
            </span>
          </div>

          <input
            type="range"
            min="0"
            max="150000"
            step="5000"
            value={additional80C}
            onChange={(e) => setAdditional80C(Number(e.target.value))}
            className="w-full accent-indigo-600 cursor-pointer"
          />

          <div className="flex justify-between text-[10px] text-slate-400 font-mono">
            <span>₹ 0</span>
            <span>₹ 75,000</span>
            <span>₹ 1,50,000 (Max Cap)</span>
          </div>
        </div>

        {/* Slider 2: NPS 80CCD(1B) */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-xs font-bold text-slate-800">Additional Section 80CCD(1B) NPS</span>
              <p className="text-[11px] text-slate-400">Exclusive Tier-1 National Pension System</p>
            </div>
            <span className="font-mono font-bold text-indigo-700 text-sm">
              {formatINR(additionalNPS)}
            </span>
          </div>

          <input
            type="range"
            min="0"
            max="50000"
            step="5000"
            value={additionalNPS}
            onChange={(e) => setAdditionalNPS(Number(e.target.value))}
            className="w-full accent-indigo-600 cursor-pointer"
          />

          <div className="flex justify-between text-[10px] text-slate-400 font-mono">
            <span>₹ 0</span>
            <span>₹ 25,000</span>
            <span>₹ 50,000 (Max Cap)</span>
          </div>
        </div>

        {/* Slider 3: Health Insurance 80D */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-xs font-bold text-slate-800">Additional Section 80D Health</span>
              <p className="text-[11px] text-slate-400">Mediclaim for Self, Family & Senior Parents</p>
            </div>
            <span className="font-mono font-bold text-indigo-700 text-sm">
              {formatINR(additional80D)}
            </span>
          </div>

          <input
            type="range"
            min="0"
            max="100000"
            step="5000"
            value={additional80D}
            onChange={(e) => setAdditional80D(Number(e.target.value))}
            className="w-full accent-indigo-600 cursor-pointer"
          />

          <div className="flex justify-between text-[10px] text-slate-400 font-mono">
            <span>₹ 0</span>
            <span>₹ 50,000</span>
            <span>₹ 1,00,000 (Self + Senior Parents)</span>
          </div>
        </div>

        {/* Slider 4: Employer NPS 80CCD(2) */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-1.5">
                <span className="text-xs font-bold text-slate-800">Employer NPS (Sec 80CCD(2))</span>
                <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-100 text-emerald-800 font-bold">
                  BOTH REGIMES
                </span>
              </div>
              <p className="text-[11px] text-slate-400">Up to 14% of Basic + DA from Employer</p>
            </div>
            <span className="font-mono font-bold text-indigo-700 text-sm">
              {formatINR(additionalEmployerNPS)}
            </span>
          </div>

          <input
            type="range"
            min="0"
            max="200000"
            step="10000"
            value={additionalEmployerNPS}
            onChange={(e) => setAdditionalEmployerNPS(Number(e.target.value))}
            className="w-full accent-indigo-600 cursor-pointer"
          />

          <div className="flex justify-between text-[10px] text-slate-400 font-mono">
            <span>₹ 0</span>
            <span>₹ 1,00,000</span>
            <span>₹ 2,00,000</span>
          </div>
        </div>
      </div>
    </div>
  );
};
