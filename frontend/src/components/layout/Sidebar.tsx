import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Compass,
  UploadCloud,
  FileCheck2,
  Wallet,
  Receipt,
  PiggyBank,
  Calculator,
  Scale,
  Sparkles,
  Sliders,
  FileText,
  GitCompare,
  MessageSquare,
  UserCheck,
} from 'lucide-react';

interface SidebarProps {
  collapsed?: boolean;
}

export const Sidebar: React.FC<SidebarProps> = () => {
  const navItems = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/wizard', label: 'Guided Wizard', icon: Compass, badge: '13-Step' },
    { to: '/upload', label: 'Upload Documents', icon: UploadCloud },
    { to: '/extraction', label: 'Verification Workbench', icon: FileCheck2 },
    { to: '/income', label: 'Income Overview', icon: Wallet },
    { to: '/transactions', label: 'Bank Transactions', icon: Receipt },
    { to: '/investments', label: '80C & Investments', icon: PiggyBank },
    { to: '/calculation', label: 'Tax Calculation', icon: Calculator },
    { to: '/regimes', label: 'Regime Comparator', icon: Scale },
    { to: '/missed-deductions', label: 'Missed Deductions', icon: Sparkles, highlight: true },
    { to: '/what-if', label: 'What-If Simulator', icon: Sliders },
    { to: '/reports', label: 'Tax Reports (PDF)', icon: FileText },
    { to: '/reconciliation', label: 'AIS / 26AS Reconcile', icon: GitCompare },
    { to: '/chat', label: 'Tax Assistant Chat', icon: MessageSquare },
    { to: '/profile', label: 'Profile & Settings', icon: UserCheck },
  ];

  return (
    <aside className="w-64 shrink-0 bg-white border-r border-slate-200 flex flex-col h-[calc(100vh-53px)] sticky top-[53px]">
      <div className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
        <div className="px-3 pb-2 text-[10px] font-bold uppercase tracking-wider text-slate-400">
          Core Workflows
        </div>
        {navItems.slice(0, 4).map((item) => (
          <SidebarLink key={item.to} {...item} />
        ))}

        <div className="pt-4 px-3 pb-2 text-[10px] font-bold uppercase tracking-wider text-slate-400">
          Financials & Analysis
        </div>
        {navItems.slice(4, 7).map((item) => (
          <SidebarLink key={item.to} {...item} />
        ))}

        <div className="pt-4 px-3 pb-2 text-[10px] font-bold uppercase tracking-wider text-slate-400">
          Tax Engine & Optimisation
        </div>
        {navItems.slice(7, 11).map((item) => (
          <SidebarLink key={item.to} {...item} />
        ))}

        <div className="pt-4 px-3 pb-2 text-[10px] font-bold uppercase tracking-wider text-slate-400">
          Verification & Compliance
        </div>
        {navItems.slice(11).map((item) => (
          <SidebarLink key={item.to} {...item} />
        ))}
      </div>

      <div className="p-3 border-t border-slate-100 bg-slate-50/70 text-[11px] text-slate-500 flex flex-col gap-1">
        <div className="flex items-center justify-between font-medium text-slate-700">
          <span>Engine Status</span>
          <span className="flex items-center gap-1 text-emerald-600">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            Deterministic
          </span>
        </div>
        <p className="text-[10px] text-slate-400">
          Pure-Python rules engine • Sec 288A/B rounding
        </p>
      </div>
    </aside>
  );
};

const SidebarLink: React.FC<{
  to: string;
  label: string;
  icon: any;
  badge?: string;
  highlight?: boolean;
}> = ({ to, label, icon: Icon, badge, highlight }) => {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-all ${
          isActive
            ? 'bg-indigo-50 text-indigo-700 font-semibold shadow-2xs'
            : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/70'
        } ${highlight ? 'text-amber-800 bg-amber-50/60' : ''}`
      }
    >
      <div className="flex items-center gap-2.5">
        <Icon className="w-4 h-4 shrink-0" />
        <span className="truncate">{label}</span>
      </div>
      {badge && (
        <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-200 text-slate-700 font-semibold">
          {badge}
        </span>
      )}
    </NavLink>
  );
};
