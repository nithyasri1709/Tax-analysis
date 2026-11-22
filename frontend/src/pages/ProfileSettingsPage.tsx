import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useTax } from '../context/TaxContext';
import { api } from '../api/client';
import { AuditLogItem } from '../types';
import {
  UserCheck,
  Shield,
  KeyRound,
  Download,
  Trash2,
  Lock,
  MapPin,
  Calendar,
  AlertTriangle,
  History,
  CheckCircle,
} from 'lucide-react';

export const ProfileSettingsPage: React.FC = () => {
  const { user, refreshUser, logout } = useAuth();
  const { showToast } = useTax();

  // Demographics form
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [dob, setDob] = useState(user?.dob || '');
  const [ageBracket, setAgeBracket] = useState(user?.age_bracket || 'regular');
  const [employmentType, setEmploymentType] = useState(user?.employment_type || 'salaried');
  const [isMetro, setIsMetro] = useState(user?.is_metro || false);
  const [pan, setPan] = useState('');
  const [isUpdatingProfile, setIsUpdatingProfile] = useState(false);

  // Security form
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [isChangingPass, setIsChangingPass] = useState(false);

  // Delete account confirmation
  const [deletePass, setDeletePass] = useState('');
  const [deleteConfirmText, setDeleteConfirmText] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);

  // Audit logs
  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>([]);

  useEffect(() => {
    if (user) {
      setFullName(user.full_name || '');
      setDob(user.dob || '');
      setAgeBracket(user.age_bracket || 'regular');
      setEmploymentType(user.employment_type || 'salaried');
      setIsMetro(user.is_metro || false);
    }

    const loadAuditLogs = async () => {
      try {
        const logs = await api.admin.getAuditLogs(20);
        setAuditLogs(logs);
      } catch (e) {
        console.warn('Failed to load audit logs', e);
      }
    };
    loadAuditLogs();
  }, [user]);

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsUpdatingProfile(true);
    try {
      await api.users.updateMe({
        full_name: fullName,
        dob: dob || undefined,
        age_bracket: ageBracket as any,
        employment_type: employmentType as any,
        is_metro: isMetro,
      });

      if (pan.trim()) {
        await api.users.updatePan(pan.trim());
      }

      await refreshUser();
      showToast('Profile and encrypted PAN updated successfully!', 'success');
      setPan('');
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Failed to update profile', 'error');
    } finally {
      setIsUpdatingProfile(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsChangingPass(true);
    try {
      await api.users.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });
      showToast('Password changed successfully!', 'success');
      setCurrentPassword('');
      setNewPassword('');
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Failed to change password', 'error');
    } finally {
      setIsChangingPass(false);
    }
  };

  const handleExportData = async () => {
    try {
      const data = await api.users.exportData();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `tax_data_export_${user?.id?.slice(0, 8)}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      showToast('DPDP Data Export downloaded successfully!', 'success');
    } catch (err: any) {
      showToast('Failed to export data', 'error');
    }
  };

  const handleDeleteAccount = async () => {
    if (deleteConfirmText !== 'DELETE') {
      showToast('Please type DELETE in capital letters to confirm', 'error');
      return;
    }
    setIsDeleting(true);
    try {
      await api.users.deleteAccount({
        password_confirmation: deletePass,
        confirm_text: deleteConfirmText,
      });
      showToast('Account and all associated encrypted files permanently purged.', 'info');
      await logout();
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Account deletion failed', 'error');
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1 rounded bg-indigo-100 text-indigo-700">
              <UserCheck className="w-5 h-5" />
            </span>
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">
              Profile, Security & DPDP Compliance
            </h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Manage taxpayer demographics, encrypted PAN, password security, audit logs, and privacy rights.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleExportData}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-200 text-xs font-semibold rounded-lg shadow-2xs transition-colors cursor-pointer"
          >
            <Download className="w-4 h-4" />
            <span>DPDP Data Export (JSON)</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Demographics & PAN */}
        <div className="lg:col-span-7 bg-white p-6 rounded-xl border border-slate-200 shadow-2xs space-y-4">
          <h2 className="text-sm font-bold text-slate-800 border-b pb-2 flex items-center gap-2">
            <UserCheck className="w-4 h-4 text-indigo-600" />
            <span>Taxpayer Demographics & Identity</span>
          </h2>

          <form onSubmit={handleUpdateProfile} className="space-y-4 text-xs">
            <div>
              <label className="font-semibold text-slate-700 block mb-1">Full Legal Name</label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full p-2.5 border border-slate-300 rounded-lg"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="font-semibold text-slate-700 block mb-1">Date of Birth</label>
                <input
                  type="date"
                  value={dob}
                  onChange={(e) => setDob(e.target.value)}
                  className="w-full p-2.5 border border-slate-300 rounded-lg"
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Age Bracket</label>
                <select
                  value={ageBracket}
                  onChange={(e) => setAgeBracket(e.target.value as any)}
                  className="w-full p-2.5 border border-slate-300 rounded-lg"
                >
                  <option value="regular">Regular Taxpayer (&lt; 60)</option>
                  <option value="senior">Senior Citizen (60 - 79)</option>
                  <option value="super_senior">Super Senior Citizen (80+)</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="font-semibold text-slate-700 block mb-1">Employment Type</label>
                <select
                  value={employmentType}
                  onChange={(e) => setEmploymentType(e.target.value as any)}
                  className="w-full p-2.5 border border-slate-300 rounded-lg"
                >
                  <option value="salaried">Salaried Individual</option>
                  <option value="pensioner">Pensioner</option>
                  <option value="self_employed_basic">Self-Employed / Freelancer</option>
                </select>
              </div>

              <div className="flex items-center justify-between p-2.5 bg-slate-50 border border-slate-200 rounded-lg">
                <span className="font-semibold text-slate-700">Metro City (50% HRA)</span>
                <input
                  type="checkbox"
                  checked={isMetro}
                  onChange={(e) => setIsMetro(e.target.checked)}
                  className="w-4 h-4 text-indigo-600 rounded"
                />
              </div>
            </div>

            <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-slate-700 flex items-center gap-1.5">
                  <Shield className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Permanent Account Number (PAN)</span>
                </span>
                <span className="font-mono text-slate-600 font-bold">
                  {user?.pan_masked || 'None Linked'}
                </span>
              </div>
              <input
                type="text"
                placeholder="Update PAN (e.g. ABCDE1234F)..."
                value={pan}
                onChange={(e) => setPan(e.target.value.toUpperCase())}
                maxLength={10}
                className="w-full p-2 border border-slate-300 rounded-lg font-mono uppercase text-xs"
              />
              <span className="text-[10px] text-slate-400 block">
                PAN is encrypted at rest using AES-128 Fernet and masked in UI.
              </span>
            </div>

            <button
              type="submit"
              disabled={isUpdatingProfile}
              className="w-full py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-lg shadow-xs transition-colors cursor-pointer"
            >
              {isUpdatingProfile ? 'Saving...' : 'Save Profile Changes'}
            </button>
          </form>
        </div>

        {/* Right Column: Security, Audit Log & Account Purge */}
        <div className="lg:col-span-5 space-y-6">
          {/* Security / Password Change */}
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-2xs space-y-4 text-xs">
            <h2 className="text-sm font-bold text-slate-800 border-b pb-2 flex items-center gap-2">
              <KeyRound className="w-4 h-4 text-indigo-600" />
              <span>Change Password</span>
            </h2>

            <form onSubmit={handleChangePassword} className="space-y-3">
              <div>
                <label className="font-semibold text-slate-700 block mb-1">Current Password</label>
                <input
                  type="password"
                  required
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  className="w-full p-2 border border-slate-300 rounded-lg"
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">New Password</label>
                <input
                  type="password"
                  required
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full p-2 border border-slate-300 rounded-lg"
                />
              </div>

              <button
                type="submit"
                disabled={isChangingPass}
                className="w-full py-2 bg-slate-800 hover:bg-slate-900 text-white font-semibold rounded-lg shadow-xs transition-colors cursor-pointer"
              >
                {isChangingPass ? 'Updating...' : 'Update Password'}
              </button>
            </form>
          </div>

          {/* User Audit Log Snippet */}
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs space-y-3 text-xs">
            <div className="flex items-center justify-between border-b pb-2">
              <div className="flex items-center gap-1.5 font-bold text-slate-800">
                <History className="w-4 h-4 text-indigo-600" />
                <span>Security Audit Log</span>
              </div>
              <span className="text-[10px] text-slate-400">Last 20 events</span>
            </div>

            <div className="max-h-40 overflow-y-auto divide-y divide-slate-100 text-[11px]">
              {auditLogs.map((log) => (
                <div key={log.id} className="py-1.5 flex items-center justify-between">
                  <span className="font-mono text-slate-700">{log.action}</span>
                  <span className="text-slate-400 font-mono">
                    {new Date(log.created_at).toLocaleTimeString()}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* DPDP Account Purge */}
          <div className="bg-rose-50 border border-rose-200 p-5 rounded-xl shadow-2xs space-y-3 text-xs">
            <div className="flex items-center gap-2 text-rose-800 font-bold">
              <Trash2 className="w-4 h-4 text-rose-600" />
              <span>Delete Account & Purge All Data</span>
            </div>
            <p className="text-rose-700 text-[11px] leading-relaxed">
              In compliance with the Digital Personal Data Protection Act (DPDP), you can permanently delete your account, documents, and calculation records. This action is irreversible.
            </p>

            <button
              onClick={() => setDeleteModalOpen(true)}
              className="w-full py-2 bg-rose-600 hover:bg-rose-700 text-white font-semibold rounded-lg transition-colors cursor-pointer"
            >
              Request Account Deletion
            </button>
          </div>
        </div>
      </div>

      {/* Delete Account Modal */}
      {deleteModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-sm w-full p-5 space-y-4 border border-rose-200 text-xs">
            <div className="flex items-center gap-2 text-rose-800 font-bold text-sm">
              <AlertTriangle className="w-5 h-5 text-rose-600" />
              <span>Confirm Permanent Account Purge</span>
            </div>

            <p className="text-slate-600">
              Type <strong>DELETE</strong> below and enter your password to purge all personal data.
            </p>

            <div>
              <label className="font-semibold text-slate-700 block mb-1">Type DELETE</label>
              <input
                type="text"
                value={deleteConfirmText}
                onChange={(e) => setDeleteConfirmText(e.target.value)}
                placeholder="DELETE"
                className="w-full p-2 border border-slate-300 rounded font-mono uppercase"
              />
            </div>

            <div>
              <label className="font-semibold text-slate-700 block mb-1">Current Password</label>
              <input
                type="password"
                value={deletePass}
                onChange={(e) => setDeletePass(e.target.value)}
                placeholder="Enter password..."
                className="w-full p-2 border border-slate-300 rounded"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setDeleteModalOpen(false)}
                className="px-3 py-1.5 text-slate-600 hover:bg-slate-100 rounded"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteAccount}
                disabled={isDeleting || deleteConfirmText !== 'DELETE' || !deletePass}
                className="px-4 py-1.5 bg-rose-600 hover:bg-rose-700 text-white font-semibold rounded shadow-xs disabled:opacity-40"
              >
                {isDeleting ? 'Purging...' : 'Permanently Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
