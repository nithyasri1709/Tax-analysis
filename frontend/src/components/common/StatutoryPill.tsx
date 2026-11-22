import React from 'react';
import { BookOpen } from 'lucide-react';

interface StatutoryPillProps {
  section1961: string;
  section2025?: string | null;
  className?: string;
  isVerified?: boolean;
}

export const StatutoryPill: React.FC<StatutoryPillProps> = ({
  section1961,
  section2025,
  className = '',
  isVerified = true,
}) => {
  return (
    <div className={`inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-md bg-slate-100 text-slate-800 border border-slate-200 ${className}`}>
      <BookOpen className="w-3 h-3 text-slate-500" />
      <span>Sec {section1961} (1961 Act)</span>
      {section2025 && (
        <>
          <span className="text-slate-400">➔</span>
          <span className="text-indigo-700 font-semibold">
            Sec {section2025} (2025 Act{!isVerified ? ' [verify]' : ''})
          </span>
        </>
      )}
    </div>
  );
};
