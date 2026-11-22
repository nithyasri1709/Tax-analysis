import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Shield, Sparkles, CheckCircle, ArrowRight, Lock, Mail, User, Building, MapPin } from 'lucide-react';

export const AuthPage: React.FC = () => {
  const { login, register, quickDemoLogin, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [ageBracket, setAgeBracket] = useState('regular');
  const [employmentType, setEmploymentType] = useState('salaried');
  const [isMetro, setIsMetro] = useState(true);
  const [pan, setPan] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  React.useEffect(() => {
    if (isAuthenticated) {
      navigate('/');
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      if (mode === 'login') {
        await login(email, password);
      } else {
        await register({
          email,
          password,
          full_name: fullName,
          age_bracket: ageBracket,
          employment_type: employmentType,
          is_metro: isMetro,
          residential_status: 'resident',
          pan: pan.trim() || undefined,
        });
      }
      navigate('/');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Authentication failed. Please check your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDemoSignIn = async () => {
    setError(null);
    setIsLoading(true);
    try {
      await quickDemoLogin();
      navigate('/');
    } catch (err: any) {
      setError('Could not sign into demo account. Please try manual registration.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-indigo-950 flex items-center justify-center p-4">
      <div className="max-w-4xl w-full grid grid-cols-1 lg:grid-cols-12 bg-white rounded-2xl shadow-2xl overflow-hidden border border-slate-700/20">
        {/* Left hero side */}
        <div className="lg:col-span-5 bg-gradient-to-br from-indigo-700 via-indigo-800 to-slate-900 p-8 text-white flex flex-col justify-between">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/30 text-indigo-200 text-xs font-semibold mb-6">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Income-tax Act 1961 & 2025 Ready</span>
            </div>

            <h1 className="text-2xl font-bold tracking-tight">INTELLIGENT TAX ASSISTANT</h1>
            <p className="mt-2 text-indigo-100 text-sm leading-relaxed">
              Smart Tax Planning, Automated Document OCR & Parsing, and Explainable Deduction Detection.
            </p>

            <ul className="mt-8 space-y-3 text-xs text-indigo-200">
              <li className="flex items-center gap-2.5">
                <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>Deterministic pure-Python rules engine (no LLM math)</span>
              </li>
              <li className="flex items-center gap-2.5">
                <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>Multi-document OCR & Form 16 / AIS cross-checks</span>
              </li>
              <li className="flex items-center gap-2.5">
                <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>Old vs New Regime comparison & break-even analysis</span>
              </li>
              <li className="flex items-center gap-2.5">
                <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>Missed Deductions Advisor with live What-If sliders</span>
              </li>
            </ul>
          </div>

          <div className="mt-8 pt-6 border-t border-indigo-600/50 flex items-center gap-2 text-xs text-indigo-300">
            <Shield className="w-4 h-4 text-emerald-400" />
            <span>Fernet AES encrypted • Privacy first</span>
          </div>
        </div>

        {/* Right form side */}
        <div className="lg:col-span-7 p-8 flex flex-col justify-center bg-white">
          <div className="flex items-center justify-between mb-6 pb-2 border-b border-slate-100">
            <div className="flex gap-4">
              <button
                onClick={() => setMode('login')}
                className={`text-sm font-semibold pb-2 -mb-2.5 border-b-2 transition-all ${
                  mode === 'login'
                    ? 'border-indigo-600 text-indigo-600'
                    : 'border-transparent text-slate-400 hover:text-slate-600'
                }`}
              >
                Sign In
              </button>
              <button
                onClick={() => setMode('register')}
                className={`text-sm font-semibold pb-2 -mb-2.5 border-b-2 transition-all ${
                  mode === 'register'
                    ? 'border-indigo-600 text-indigo-600'
                    : 'border-transparent text-slate-400 hover:text-slate-600'
                }`}
              >
                Create Account
              </button>
            </div>

            <button
              onClick={handleDemoSignIn}
              disabled={isLoading}
              className="text-xs font-semibold text-indigo-700 bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 shadow-2xs"
            >
              <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
              <span>Instant Demo Sign-In</span>
            </button>
          </div>

          {error && (
            <div className="mb-4 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {mode === 'register' && (
              <>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Full Name</label>
                  <div className="relative">
                    <User className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                    <input
                      type="text"
                      required
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      placeholder="e.g. Ramesh Kumar"
                      className="w-full text-xs pl-9 pr-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">Age Bracket</label>
                    <select
                      value={ageBracket}
                      onChange={(e) => setAgeBracket(e.target.value)}
                      className="w-full text-xs p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                    >
                      <option value="regular">Below 60 (Regular)</option>
                      <option value="senior">60 to 79 (Senior)</option>
                      <option value="super_senior">80+ (Super Senior)</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">Employment</label>
                    <select
                      value={employmentType}
                      onChange={(e) => setEmploymentType(e.target.value)}
                      className="w-full text-xs p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                    >
                      <option value="salaried">Salaried</option>
                      <option value="pensioner">Pensioner</option>
                      <option value="self_employed_basic">Self-Employed</option>
                    </select>
                  </div>
                </div>

                <div className="flex items-center justify-between p-2.5 bg-slate-50 border border-slate-200 rounded-lg text-xs">
                  <div className="flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-slate-500" />
                    <span className="font-medium text-slate-700">Metro City (HRA 50%)</span>
                  </div>
                  <input
                    type="checkbox"
                    checked={isMetro}
                    onChange={(e) => setIsMetro(e.target.checked)}
                    className="w-4 h-4 text-indigo-600 rounded"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    PAN (Optional, Encrypted at Rest)
                  </label>
                  <input
                    type="text"
                    maxLength={10}
                    value={pan}
                    onChange={(e) => setPan(e.target.value.toUpperCase())}
                    placeholder="e.g. ABCDE1234F"
                    className="w-full text-xs p-2 border border-slate-300 rounded-lg uppercase tracking-wider font-mono focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  />
                </div>
              </>
            )}

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Email Address</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="taxpayer@example.com"
                  className="w-full text-xs pl-9 pr-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full text-xs pl-9 pr-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full mt-2 py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs rounded-lg shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2 cursor-pointer"
            >
              <span>{isLoading ? 'Processing...' : mode === 'login' ? 'Sign In to Dashboard' : 'Register & Start Planning'}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </form>

          <p className="mt-6 text-center text-[11px] text-slate-400">
            Estimate only; not professional tax advice. Complies with DPDP Act 2023.
          </p>
        </div>
      </div>
    </div>
  );
};
