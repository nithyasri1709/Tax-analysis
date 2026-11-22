import React from 'react';
import { useAuth } from '../../context/AuthContext';
import { useTax } from '../../context/TaxContext';
import { RefreshCw, User as UserIcon, LogOut, Shield, Calendar, Sparkles } from 'lucide-react';

export const Navbar: React.FC = () => {
  const { user, logout } = useAuth();
  const { financialYear, setFinancialYear, regime, setRegime, isRecalculating, refreshAll } = useTax();

  const is2025Act = financialYear === '2026-27';

  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur border-b border-slate-200 px-4 sm:px-6 py-2.5 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-bold shadow-md shadow-indigo-200">
            ₹
          </div>
          <div className="hidden sm:block">
            <span className="font-bold text-slate-900 tracking-tight text-base">TAX ASSISTANT</span>
            <span className="ml-1.5 text-[10px] font-semibold tracking-wider uppercase px-1.5 py-0.5 rounded bg-indigo-100 text-indigo-700">
              Smart Tax 2026
            </span>
          </div>
        </div>

        {/* Financial Year Selector */}
        <div className="flex items-center ml-2 sm:ml-6 gap-2 bg-slate-100/90 border border-slate-200 rounded-lg p-1">
          <Calendar className="w-3.5 h-3.5 text-slate-500 ml-1.5 hidden md:inline" />
          <select
            value={financialYear}
            onChange={(e) => setFinancialYear(e.target.value)}
            className="bg-transparent text-xs font-semibold text-slate-800 focus:outline-none cursor-pointer pr-1"
          >
            <option value="2024-25">FY 2024-25 (AY 2025-26)</option>
            <option value="2025-26">FY 2025-26 (AY 2026-27)</option>
            <option value="2026-27">FY 2026-27 (Tax Year 2026-27)</option>
          </select>
          <span
            className={`text-[10px] px-1.5 py-0.5 font-medium rounded ${
              is2025Act ? 'bg-amber-100 text-amber-800' : 'bg-blue-100 text-blue-800'
            }`}
          >
            {is2025Act ? 'Income-tax Act, 2025' : 'Income-tax Act, 1961'}
          </span>
        </div>
      </div>

      <div className="flex items-center gap-2 sm:gap-4">
        {/* Regime Toggle */}
        <div className="flex items-center bg-slate-100 p-0.5 rounded-lg border border-slate-200">
          <button
            onClick={() => setRegime('new')}
            className={`px-2.5 py-1 text-xs font-semibold rounded-md transition-all ${
              regime === 'new'
                ? 'bg-indigo-600 text-white shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            New Regime <span className="text-[10px] opacity-80">(Default)</span>
          </button>
          <button
            onClick={() => setRegime('old')}
            className={`px-2.5 py-1 text-xs font-semibold rounded-md transition-all ${
              regime === 'old'
                ? 'bg-indigo-600 text-white shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Old Regime
          </button>
        </div>

        {/* Recalculate Button */}
        <button
          onClick={refreshAll}
          disabled={isRecalculating}
          title="Recalculate Tax"
          className="flex items-center gap-1.5 text-xs font-medium text-slate-700 bg-white hover:bg-slate-50 border border-slate-200 px-2.5 py-1.5 rounded-md shadow-2xs transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-indigo-600 ${isRecalculating ? 'animate-spin' : ''}`} />
          <span className="hidden md:inline">{isRecalculating ? 'Calculating...' : 'Recalculate'}</span>
        </button>

        {/* User Info / PAN Badge */}
        {user && (
          <div className="flex items-center gap-2 pl-2 border-l border-slate-200">
            <div className="hidden lg:flex flex-col items-end">
              <span className="text-xs font-semibold text-slate-800 leading-tight">{user.full_name}</span>
              <div className="flex items-center gap-1 text-[11px] text-slate-500">
                <Shield className="w-3 h-3 text-emerald-600" />
                <span>{user.pan_masked || 'No PAN Linked'}</span>
              </div>
            </div>

            <button
              onClick={logout}
              title="Logout"
              className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-md transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
