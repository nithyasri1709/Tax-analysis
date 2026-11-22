import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { TaxProvider } from './context/TaxContext';
import { Layout } from './components/layout/Layout';
import { LoadingSpinner } from './components/common/LoadingSpinner';

// Pages
import { AuthPage } from './pages/AuthPage';
import { DashboardPage } from './pages/DashboardPage';
import { OnboardingWizardPage } from './pages/OnboardingWizardPage';
import { UploadDocumentsPage } from './pages/UploadDocumentsPage';
import { DocumentAnalysisPage } from './pages/DocumentAnalysisPage';
import { IncomeOverviewPage } from './pages/IncomeOverviewPage';
import { ExpenseCategoriesPage } from './pages/ExpenseCategoriesPage';
import { InvestmentAnalysisPage } from './pages/InvestmentAnalysisPage';
import { TaxCalculationPage } from './pages/TaxCalculationPage';
import { RegimeComparisonPage } from './pages/RegimeComparisonPage';
import { MissedDeductionsPage } from './pages/MissedDeductionsPage';
import { WhatIfSimulatorPage } from './pages/WhatIfSimulatorPage';
import { TaxSummaryReportsPage } from './pages/TaxSummaryReportsPage';
import { ReconciliationPage } from './pages/ReconciliationPage';
import { TaxChatPage } from './pages/TaxChatPage';
import { ProfileSettingsPage } from './pages/ProfileSettingsPage';

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <LoadingSpinner size="lg" label="Restoring session..." />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Layout>{children}</Layout>;
};

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <TaxProvider>
          <Routes>
            <Route path="/login" element={<AuthPage />} />

            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <DashboardPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="/wizard"
              element={
                <ProtectedRoute>
                  <OnboardingWizardPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="/upload"
              element={
                <ProtectedRoute>
                  <UploadDocumentsPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="/extraction"
              element={
                <ProtectedRoute>
                  <DocumentAnalysisPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="/income"
              element={
                <ProtectedRoute>
                  <IncomeOverviewPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="/transactions"
              element={
                <ProtectedRoute>
                  <ExpenseCategoriesPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="/investments"
              element={
                <ProtectedRoute>
                  <InvestmentAnalysisPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="/calculation"
              element={
                <ProtectedRoute>
                  <TaxCalculationPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="/regimes"
              element={
                <ProtectedRoute>
                  <RegimeComparisonPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="/missed-deductions"
              element={
                <ProtectedRoute>
                  <MissedDeductionsPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="/what-if"
              element={
                <ProtectedRoute>
                  <WhatIfSimulatorPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="/reports"
              element={
                <ProtectedRoute>
                  <TaxSummaryReportsPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="/reconciliation"
              element={
                <ProtectedRoute>
                  <ReconciliationPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="/chat"
              element={
                <ProtectedRoute>
                  <TaxChatPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="/profile"
              element={
                <ProtectedRoute>
                  <ProfileSettingsPage />
                </ProtectedRoute>
              }
            />

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </TaxProvider>
      </AuthProvider>
    </BrowserRouter>
  );
};

export default App;
