/**
 * INTELLIGENT TAX ASSISTANT - API Client
 * Axios HTTP client with JWT interceptor, refresh rotation, and typed service endpoints.
 */

import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import {
  User,
  DocumentItem,
  ExtractedField,
  Transaction,
  CategoryTotalItem,
  FinancialProfile,
  TaxCalculationResult,
  RegimeComparisonResult,
  MissedDeductionsResponse,
  WhatIfResponse,
  InvestmentAnalysisResponse,
  ReportItem,
  ReconciliationResponse,
  AuditLogItem,
  StatutoryRulesResponse,
} from '../types';

const API_BASE = '/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor: Attach JWT Token
apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('access_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response Interceptor: Handle Token Refresh on 401
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value?: unknown) => void;
  reject: (reason?: unknown) => void;
}> = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && !originalRequest._retry && !originalRequest.url?.includes('/auth/')) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            return apiClient(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        isRefreshing = false;
        localStorage.clear();
        window.location.href = '/login';
        return Promise.reject(error);
      }

      try {
        const res = await axios.post(`${API_BASE}/auth/refresh`, {
          refresh_token: refreshToken,
        });

        const { access_token, refresh_token: newRefreshToken } = res.data;
        localStorage.setItem('access_token', access_token);
        localStorage.setItem('refresh_token', newRefreshToken);

        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
        }
        processQueue(null, access_token);
        return apiClient(originalRequest);
      } catch (refreshErr) {
        processQueue(refreshErr, null);
        localStorage.clear();
        window.location.href = '/login';
        return Promise.reject(refreshErr);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export const api = {
  // Auth
  auth: {
    register: async (data: any) => (await apiClient.post('/auth/register', data)).data,
    login: async (data: any) => (await apiClient.post('/auth/login', data)).data,
    refresh: async (refreshToken: string) =>
      (await apiClient.post('/auth/refresh', { refresh_token: refreshToken })).data,
    logout: async () => (await apiClient.post('/auth/logout')).data,
  },

  // Users
  users: {
    getMe: async (): Promise<User> => (await apiClient.get('/users/me')).data,
    updateMe: async (data: Partial<User>): Promise<User> => (await apiClient.patch('/users/me', data)).data,
    updatePan: async (pan: string): Promise<User> => (await apiClient.post('/users/me/pan', { pan })).data,
    changePassword: async (data: any) => (await apiClient.post('/users/me/change-password', data)).data,
    exportData: async () => (await apiClient.get('/users/me/export')).data,
    deleteAccount: async (data: { password_confirmation: string; confirm_text: string }) =>
      (await apiClient.post('/users/me/delete-account', data)).data,
  },

  // Documents
  documents: {
    upload: async (formData: FormData): Promise<DocumentItem> => {
      const res = await apiClient.post('/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return res.data;
    },
    list: async (financialYear?: string): Promise<DocumentItem[]> => {
      const params = financialYear ? { financial_year: financialYear } : {};
      return (await apiClient.get('/documents', { params })).data;
    },
    getById: async (id: string): Promise<DocumentItem> => (await apiClient.get(`/documents/${id}`)).data,
    delete: async (id: string) => (await apiClient.delete(`/documents/${id}`)).data,
    getViewUrl: (id: string) => {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token');
      return `${API_BASE}/documents/${id}/view${token ? `?token=${encodeURIComponent(token)}` : ''}`;
    },
  },

  // Extraction
  extraction: {
    processDoc: async (docId: string, password?: string) =>
      (await apiClient.post(`/extraction/process/${docId}`, null, { params: { password } })).data,
    getFields: async (docId?: string, financialYear?: string): Promise<ExtractedField[]> => {
      const params: any = {};
      if (docId) params.document_id = docId;
      if (financialYear) params.financial_year = financialYear;
      return (await apiClient.get('/extraction/fields', { params })).data;
    },
    updateField: async (fieldId: string, data: { field_value: string; normalized_value?: number }) =>
      (await apiClient.patch(`/extraction/fields/${fieldId}`, data)).data,
    confirmField: async (fieldId: string) =>
      (await apiClient.post(`/extraction/fields/${fieldId}/confirm`)).data,
    resolveConflict: async (key: string, data: { chosen_field_id: string; custom_value?: number }) =>
      (await apiClient.post(`/extraction/conflicts/${key}/resolve`, data)).data,
  },

  // Transactions
  transactions: {
    list: async (params?: {
      financial_year?: string;
      category?: string;
      only_tax_eligible?: boolean;
      skip?: number;
      limit?: number;
    }): Promise<Transaction[]> => (await apiClient.get('/transactions', { params })).data,
    getTotals: async (financialYear?: string): Promise<CategoryTotalItem[]> =>
      (await apiClient.get('/transactions/category-totals', { params: { financial_year: financialYear } })).data,
    update: async (
      id: string,
      data: { category?: string; deduction_status?: string; apply_to_similar?: boolean }
    ) => (await apiClient.patch(`/transactions/${id}`, data)).data,
    bulkCategorise: async (data: { description_pattern: string; new_category: string }) =>
      (await apiClient.post('/transactions/bulk-categorise', data)).data,
    split: async (id: string, splits: Array<{ category: string; amount: number; description?: string }>) =>
      (await apiClient.post(`/transactions/${id}/split`, { splits })).data,
  },

  // Investments
  investments: {
    getAnalysis: async (financialYear = '2025-26', regime = 'new'): Promise<InvestmentAnalysisResponse> =>
      (await apiClient.get('/investments', { params: { financial_year: financialYear, regime } })).data,
  },

  // Tax Engine
  tax: {
    calculate: async (payload: any): Promise<TaxCalculationResult> =>
      (await apiClient.post('/tax/calculate', payload)).data,
    compareRegimes: async (payload: any): Promise<RegimeComparisonResult> =>
      (await apiClient.post('/tax/compare', payload)).data,
    calculateHra: async (payload: any) => (await apiClient.post('/tax/hra-calculator', payload)).data,
    getStatutoryRules: async (financialYear = '2025-26'): Promise<StatutoryRulesResponse> =>
      (await apiClient.get(`/tax/rules/${financialYear}`)).data,
  },

  // Deductions Advisor & What-If
  deductions: {
    getMissed: async (financialYear = '2025-26', regime = 'new'): Promise<MissedDeductionsResponse> =>
      (await apiClient.get('/deductions/missed', { params: { financial_year: financialYear, regime } })).data,
    answerQuestion: async (payload: {
      financial_year: string;
      question_id: string;
      field_target: string;
      answer_value: any;
    }) => (await apiClient.post('/deductions/answer-question', payload)).data,
    whatIf: async (payload: {
      financial_year?: string;
      regime?: string;
      additional_80c?: number;
      additional_nps_tier1?: number;
      additional_80d_health?: number;
      additional_employer_nps?: number;
    }): Promise<WhatIfResponse> => (await apiClient.post('/deductions/what-if', payload)).data,
  },

  // Reports
  reports: {
    generate: async (financialYear = '2025-26', calculationId?: string): Promise<ReportItem> =>
      (await apiClient.post('/reports/generate', { financial_year: financialYear, calculation_id: calculationId })).data,
    list: async (financialYear?: string): Promise<ReportItem[]> =>
      (await apiClient.get('/reports', { params: { financial_year: financialYear } })).data,
    getDownloadUrl: (id: string) => {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token');
      return `${API_BASE}/reports/${id}/download${token ? `?token=${encodeURIComponent(token)}` : ''}`;
    },
    compare: async (reportId1: string, reportId2: string) =>
      (await apiClient.get(`/reports/compare/${reportId1}/${reportId2}`)).data,
  },

  // Reconciliation
  reconciliation: {
    getSummary: async (financialYear = '2025-26'): Promise<ReconciliationResponse> =>
      (await apiClient.get('/reconciliation', { params: { financial_year: financialYear } })).data,
  },

  // Financial Profile & Manual Entry
  profile: {
    getSummary: async (financialYear = '2025-26'): Promise<FinancialProfile> =>
      (await apiClient.get('/profile/summary', { params: { financial_year: financialYear } })).data,
    updateManualEntry: async (payload: any): Promise<FinancialProfile> =>
      (await apiClient.post('/profile/manual-entry', payload)).data,
    copyLastYear: async (targetFy = '2025-26', sourceFy = '2024-25') =>
      (await apiClient.post('/profile/copy-last-year', null, { params: { target_fy: targetFy, source_fy: sourceFy } })).data,
  },

  // Chat
  chat: {
    ask: async (message: string, financialYear = '2025-26', regime = 'new') =>
      (await apiClient.post('/chat/ask', { message, financial_year: financialYear, regime })).data,
  },

  // Admin & Audit
  admin: {
    getHealth: async () => (await apiClient.get('/admin/health')).data,
    getAuditLogs: async (limit = 50): Promise<AuditLogItem[]> =>
      (await apiClient.get('/admin/audit-logs', { params: { limit } })).data,
  },
};
