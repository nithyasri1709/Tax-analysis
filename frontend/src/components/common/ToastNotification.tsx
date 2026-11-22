import React from 'react';
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react';

interface ToastProps {
  message: string;
  type: 'success' | 'error' | 'info';
  onClose: () => void;
}

export const ToastNotification: React.FC<ToastProps> = ({ message, type, onClose }) => {
  const styles = {
    success: 'bg-emerald-50 text-emerald-900 border-emerald-300',
    error: 'bg-rose-50 text-rose-900 border-rose-300',
    info: 'bg-indigo-50 text-indigo-900 border-indigo-300',
  };

  const icons = {
    success: <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />,
    error: <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />,
    info: <Info className="w-5 h-5 text-indigo-600 shrink-0" />,
  };

  return (
    <div className={`fixed bottom-5 right-5 z-50 flex items-center gap-3 px-4 py-3 rounded-lg border shadow-lg transition-all animate-bounce-in max-w-md ${styles[type]}`}>
      {icons[type]}
      <p className="text-sm font-medium flex-1">{message}</p>
      <button
        onClick={onClose}
        className="text-slate-400 hover:text-slate-600 transition-colors p-1"
        aria-label="Close notification"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
};
