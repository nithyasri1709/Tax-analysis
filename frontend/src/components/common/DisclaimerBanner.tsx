import React from 'react';
import { AlertTriangle, ShieldCheck } from 'lucide-react';

interface DisclaimerBannerProps {
  className?: string;
  compact?: boolean;
}

export const DisclaimerBanner: React.FC<DisclaimerBannerProps> = ({ className = '', compact = false }) => {
  if (compact) {
    return (
      <div className={`flex items-center gap-2 text-xs text-amber-700 bg-amber-50/80 border border-amber-200 px-3 py-1.5 rounded-md ${className}`}>
        <AlertTriangle className="w-3.5 h-3.5 shrink-0 text-amber-600" />
        <span>
          <strong>Statutory Notice:</strong> Estimate only; not professional tax advice. Cross-check against statutory rules and Form 26AS/AIS.
        </span>
      </div>
    );
  }

  return (
    <div className={`bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 rounded-lg p-3 text-xs text-amber-800 flex items-start gap-3 shadow-xs ${className}`}>
      <AlertTriangle className="w-4 h-4 text-amber-600 mt-0.5 shrink-0" />
      <div className="flex-1 leading-relaxed">
        <p className="font-semibold text-amber-900">
          Statutory Notice & Privacy Guarantee
        </p>
        <p className="mt-0.5 text-amber-700">
          <strong>Estimate only; not professional tax advice.</strong> All calculations are powered by a pure deterministic rules engine conforming to the Finance Act and Income-tax rules. Documents and PII are encrypted at rest with Fernet AES cryptography. Always verify figures against your official Form 16, AIS, and Form 26AS before filing on the Income Tax Portal.
        </p>
      </div>
      <div className="hidden sm:flex items-center gap-1 text-[11px] font-medium text-emerald-700 bg-emerald-100/60 border border-emerald-300 px-2 py-1 rounded">
        <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
        <span>AES-128 Encrypted</span>
      </div>
    </div>
  );
};
