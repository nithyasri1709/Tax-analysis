import React, { ReactNode } from 'react';
import { Navbar } from './Navbar';
import { Sidebar } from './Sidebar';
import { DisclaimerBanner } from '../common/DisclaimerBanner';
import { ToastNotification } from '../common/ToastNotification';
import { ErrorBoundary } from '../common/ErrorBoundary';
import { useTax } from '../../context/TaxContext';

interface LayoutProps {
  children: ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { toast, clearToast } = useTax();

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col antialiased text-slate-800">
      <Navbar />

      <div className="flex flex-1">
        <Sidebar />

        <main className="flex-1 flex flex-col min-w-0 overflow-y-auto max-h-[calc(100vh-53px)]">
          <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-7xl w-full mx-auto">
            <DisclaimerBanner />
            <ErrorBoundary>{children}</ErrorBoundary>
          </div>
        </main>
      </div>

      {toast && (
        <ToastNotification
          message={toast.message}
          type={toast.type}
          onClose={clearToast}
        />
      )}
    </div>
  );
};
