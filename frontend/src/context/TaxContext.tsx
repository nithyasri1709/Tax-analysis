/**
 * INTELLIGENT TAX ASSISTANT - Tax Calculation & Global State Context
 */

import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';
import { FinancialProfile, RegimeComparisonResult, StatutoryRulesResponse } from '../types';
import { api } from '../api/client';
import { useAuth } from './AuthContext';

interface ToastState {
  message: string;
  type: 'success' | 'error' | 'info';
}

interface TaxContextType {
  financialYear: string;
  setFinancialYear: (fy: string) => void;
  regime: 'new' | 'old';
  setRegime: (reg: 'new' | 'old') => void;
  profile: FinancialProfile | null;
  comparisonResult: RegimeComparisonResult | null;
  statutoryRules: StatutoryRulesResponse | null;
  isRecalculating: boolean;
  toast: ToastState | null;
  showToast: (message: string, type?: 'success' | 'error' | 'info') => void;
  clearToast: () => void;
  refreshAll: () => Promise<void>;
  updateProfileData: (data: any) => Promise<void>;
}

const TaxContext = createContext<TaxContextType | undefined>(undefined);

export const TaxProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuth();
  const [financialYear, setFinancialYear] = useState<string>('2025-26');
  const [regime, setRegime] = useState<'new' | 'old'>('new');
  const [profile, setProfile] = useState<FinancialProfile | null>(null);
  const [comparisonResult, setComparisonResult] = useState<RegimeComparisonResult | null>(null);
  const [statutoryRules, setStatutoryRules] = useState<StatutoryRulesResponse | null>(null);
  const [isRecalculating, setIsRecalculating] = useState<boolean>(false);
  const [toast, setToast] = useState<ToastState | null>(null);

  const showToast = (message: string, type: 'success' | 'error' | 'info' = 'info') => {
    setToast({ message, type });
    setTimeout(() => {
      setToast(null);
    }, 4500);
  };

  const clearToast = () => setToast(null);

  const refreshAll = useCallback(async () => {
    if (!isAuthenticated) return;
    setIsRecalculating(true);
    try {
      // 1. Fetch statutory rules
      try {
        const rules = await api.tax.getStatutoryRules(financialYear);
        setStatutoryRules(rules);
      } catch (e) {
        console.warn('Could not load statutory rules:', e);
      }

      // 2. Fetch financial profile
      const prof = await api.profile.getSummary(financialYear);
      setProfile(prof);
      if (prof.selected_regime) {
        setRegime(prof.selected_regime as 'new' | 'old');
      }

      // 3. Compute regime comparison
      const comp = await api.tax.compareRegimes({
        financial_year: financialYear,
        salary_data: prof.salary_data,
        house_prop_data: prof.house_prop_data,
        other_sources_data: prof.other_sources_data,
        capital_gains_data: prof.capital_gains_data,
        deductions_data: prof.deductions_data,
        taxes_paid_data: prof.taxes_paid_data,
        age_bracket: prof.user_demographics?.age_bracket || 'regular',
        employment_type: prof.user_demographics?.employment_type || 'salaried',
        is_metro: prof.user_demographics?.is_metro || false,
      });
      setComparisonResult(comp);
    } catch (err: any) {
      console.error('Error refreshing tax profile:', err);
    } finally {
      setIsRecalculating(false);
    }
  }, [financialYear, isAuthenticated]);

  useEffect(() => {
    if (isAuthenticated) {
      refreshAll();
    }
  }, [isAuthenticated, financialYear, refreshAll]);

  const updateProfileData = async (payload: any) => {
    setIsRecalculating(true);
    try {
      const updated = await api.profile.updateManualEntry({
        financial_year: financialYear,
        selected_regime: regime,
        ...payload,
      });
      setProfile(updated);
      showToast('Profile updated and tax recalculated.', 'success');
      await refreshAll();
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Failed to update profile.', 'error');
      throw err;
    } finally {
      setIsRecalculating(false);
    }
  };

  return (
    <TaxContext.Provider
      value={{
        financialYear,
        setFinancialYear,
        regime,
        setRegime,
        profile,
        comparisonResult,
        statutoryRules,
        isRecalculating,
        toast,
        showToast,
        clearToast,
        refreshAll,
        updateProfileData,
      }}
    >
      {children}
    </TaxContext.Provider>
  );
};

export const useTax = () => {
  const context = useContext(TaxContext);
  if (!context) {
    throw new Error('useTax must be used within a TaxProvider');
  }
  return context;
};
