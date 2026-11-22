import React, { useState, useEffect, useCallback } from 'react';
import { useTax } from '../context/TaxContext';
import { api } from '../api/client';
import { Transaction, CategoryTotalItem } from '../types';
import { formatINR } from '../components/common/CurrencyDisplay';
import {
  Receipt,
  Search,
  Tag,
  Split,
  X,
} from 'lucide-react';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
} from 'recharts';

export const ExpenseCategoriesPage: React.FC = () => {
  const { financialYear, showToast, refreshAll } = useTax();

  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [totals, setTotals] = useState<CategoryTotalItem[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [onlyTaxEligible, setOnlyTaxEligible] = useState<boolean>(false);

  // Split transaction modal
  const [splittingTx, setSplittingTx] = useState<Transaction | null>(null);
  const [splitPart1Cat, setSplitPart1Cat] = useState('80C_TUITION');
  const [splitPart1Amount, setSplitPart1Amount] = useState<number>(0);
  const [splitPart2Cat, setSplitPart2Cat] = useState('PERSONAL');
  const [splitPart2Amount, setSplitPart2Amount] = useState<number>(0);

  // Recategorise modal
  const [editingTx, setEditingTx] = useState<Transaction | null>(null);
  const [newCat, setNewCat] = useState('');
  const [applySimilar, setApplySimilar] = useState(false);

  const loadTransactions = useCallback(async () => {
    try {
      const txs = await api.transactions.list({
        financial_year: financialYear,
        category: selectedCategory !== 'ALL' ? selectedCategory : undefined,
        only_tax_eligible: onlyTaxEligible ? true : undefined,
      });
      setTransactions(Array.isArray(txs) ? txs : []);

      const catTotals: any = await api.transactions.getTotals(financialYear);
      const list = Array.isArray(catTotals)
        ? catTotals
        : Array.isArray(catTotals?.categories)
        ? catTotals.categories
        : [];
      setTotals(list);
    } catch (err) {
      console.error(err);
      showToast('Could not load bank transactions', 'error');
    }
  }, [financialYear, selectedCategory, onlyTaxEligible, showToast]);

  useEffect(() => {
    loadTransactions();
  }, [loadTransactions]);

  const handleRecategorise = async () => {
    if (!editingTx) return;
    try {
      await api.transactions.update(editingTx.id, {
        category: newCat,
        apply_to_similar: applySimilar,
      });
      showToast('Transaction recategorised successfully', 'success');
      setEditingTx(null);
      await loadTransactions();
      await refreshAll();
    } catch (err: any) {
      showToast('Failed to update category', 'error');
    }
  };

  const handleOpenSplit = (tx: Transaction) => {
    setSplittingTx(tx);
    const half = Math.round(tx.amount / 2);
    setSplitPart1Amount(half);
    setSplitPart2Amount(tx.amount - half);
  };

  const handleSplitSubmit = async () => {
    if (!splittingTx) return;
    if (splitPart1Amount + splitPart2Amount !== splittingTx.amount) {
      showToast('Split amounts must sum exactly to original transaction total', 'error');
      return;
    }

    try {
      await api.transactions.split(splittingTx.id, [
        { category: splitPart1Cat, amount: splitPart1Amount, description: `${splittingTx.description} (Part 1)` },
        { category: splitPart2Cat, amount: splitPart2Amount, description: `${splittingTx.description} (Part 2)` },
      ]);
      showToast('Transaction split successfully!', 'success');
      setSplittingTx(null);
      await loadTransactions();
      await refreshAll();
    } catch (err: any) {
      showToast('Failed to split transaction', 'error');
    }
  };

  const safeTransactions = Array.isArray(transactions) ? transactions : [];
  const safeTotals = Array.isArray(totals) ? totals : [];

  const filteredTransactions = safeTransactions.filter((tx) =>
    (tx?.description || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  const pieColors = [
    '#4f46e5',
    '#10b981',
    '#f59e0b',
    '#ec4899',
    '#8b5cf6',
    '#06b6d4',
    '#64748b',
    '#ef4444',
  ];

  const pieData = safeTotals
    .filter((t) => t && t.total_amount > 0)
    .slice(0, 8)
    .map((t) => ({
      name: t.category || 'Other',
      value: t.total_amount,
    }));

  const totalTaxEligibleAmount = safeTotals.reduce((acc, curr) => acc + (curr?.tax_eligible_amount || 0), 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1 rounded bg-indigo-100 text-indigo-700">
              <Receipt className="w-5 h-5" />
            </span>
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">
              Bank Transactions & Expense Categorisation
            </h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Automated ML & rule-based detection of tax-deductible expenses (80C, 80D, 80CCD, 80G, 24b) from bank statements.
          </p>
        </div>

        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs flex items-center gap-3">
          <div>
            <span className="text-emerald-700 font-medium">Tax-Deductible Spend Detected</span>
            <div className="text-base font-bold text-emerald-800">{formatINR(totalTaxEligibleAmount)}</div>
          </div>
          <span className="text-[10px] bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded font-semibold">
            Auto-Linked
          </span>
        </div>
      </div>

      {/* Visual Chart & Category Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-5 bg-white p-5 rounded-xl border border-slate-200 shadow-2xs flex flex-col items-center">
          <h2 className="text-sm font-bold text-slate-800 self-start">Expense Distribution</h2>
          <div className="h-60 w-full mt-2 flex items-center justify-center">
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height={230}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    outerRadius={75}
                    dataKey="value"
                    label={({ name, percent }: any) =>
                      name ? `${String(name).slice(0, 8)} (${Math.round((percent || 0) * 100)}%)` : ''
                    }
                    labelLine={false}
                  >
                    {pieData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={pieColors[index % pieColors.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value: any) => formatINR(value)} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-xs text-slate-400 text-center">
                No categorized transactions found for FY {financialYear}.
              </div>
            )}
          </div>
        </div>

        <div className="lg:col-span-7 bg-white p-5 rounded-xl border border-slate-200 shadow-2xs overflow-hidden flex flex-col">
          <h2 className="text-sm font-bold text-slate-800 mb-2">Category Spending & Tax Headroom</h2>
          <div className="flex-1 overflow-y-auto divide-y divide-slate-100 max-h-60">
            {safeTotals.length === 0 ? (
              <div className="p-6 text-center text-xs text-slate-400">
                No transaction category totals available.
              </div>
            ) : (
              safeTotals.map((t) => (
                <div key={t.category} className="py-2.5 flex items-center justify-between text-xs">
                  <div>
                    <div className="flex items-center gap-1.5">
                      <span className="font-semibold text-slate-800">{t.category}</span>
                      {t.applicable_section && (
                        <span className="text-[10px] px-1.5 py-0.2 bg-indigo-100 text-indigo-700 font-bold rounded">
                          Sec {t.applicable_section}
                        </span>
                      )}
                    </div>
                    <span className="text-[11px] text-slate-400">{t.count} transactions</span>
                  </div>
                  <div className="text-right">
                    <div className="font-mono font-bold text-slate-800">{formatINR(t.total_amount)}</div>
                    {t.tax_eligible_amount > 0 && (
                      <span className="text-[10px] text-emerald-600 font-medium">
                        Eligible: {formatINR(t.tax_eligible_amount)}
                      </span>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2 flex-1 max-w-sm">
          <Search className="w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search description, merchant..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full p-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <span className="text-slate-500 font-medium">Category:</span>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="p-1.5 border border-slate-300 rounded-lg font-medium text-slate-700"
            >
              <option value="ALL">All Categories</option>
              {safeTotals.map((t) => (
                <option key={t.category} value={t.category}>
                  {t.category}
                </option>
              ))}
            </select>
          </div>

          <label className="flex items-center gap-1.5 cursor-pointer font-medium text-slate-700">
            <input
              type="checkbox"
              checked={onlyTaxEligible}
              onChange={(e) => setOnlyTaxEligible(e.target.checked)}
              className="w-4 h-4 text-indigo-600 rounded"
            />
            <span>Tax-Eligible Only</span>
          </label>
        </div>
      </div>

      {/* Transactions Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-2xs overflow-hidden">
        <div className="p-3 border-b border-slate-100 flex items-center justify-between bg-slate-50 text-xs text-slate-500">
          <span className="font-semibold text-slate-700">
            Transactions ({filteredTransactions.length})
          </span>
          <span>Double-click or click split/tag to edit</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-100 text-slate-500 uppercase text-[10px]">
              <tr>
                <th className="py-2.5 px-4 font-semibold">Date</th>
                <th className="py-2.5 px-4 font-semibold">Description</th>
                <th className="py-2.5 px-4 font-semibold">Category</th>
                <th className="py-2.5 px-4 font-semibold">Section</th>
                <th className="py-2.5 px-4 font-semibold text-right">Amount</th>
                <th className="py-2.5 px-4 font-semibold text-center">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredTransactions.length === 0 ? (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-slate-400">
                    No transactions match your search filters.
                  </td>
                </tr>
              ) : (
                filteredTransactions.map((tx) => (
                  <tr key={tx.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-2.5 px-4 text-slate-600 whitespace-nowrap">{tx.date}</td>
                    <td className="py-2.5 px-4 font-medium text-slate-800 max-w-xs truncate">
                      {tx.description}
                    </td>
                    <td className="py-2.5 px-4">
                      <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 font-semibold text-[10px]">
                        {tx.category}
                      </span>
                    </td>
                    <td className="py-2.5 px-4">
                      {tx.applicable_section ? (
                        <span className="px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 font-bold border border-indigo-200 text-[10px]">
                          {tx.applicable_section}
                        </span>
                      ) : (
                        <span className="text-slate-300">-</span>
                      )}
                    </td>
                    <td
                      className={`py-2.5 px-4 font-mono font-bold text-right whitespace-nowrap ${
                        tx.transaction_type === 'credit' ? 'text-emerald-600' : 'text-slate-800'
                      }`}
                    >
                      {tx.transaction_type === 'credit' ? '+' : '-'} {formatINR(tx.amount)}
                    </td>
                    <td className="py-2.5 px-4 text-center">
                      <div className="inline-flex items-center gap-1">
                        <button
                          onClick={() => {
                            setEditingTx(tx);
                            setNewCat(tx.category);
                          }}
                          className="p-1 text-slate-400 hover:text-indigo-600 rounded"
                          title="Recategorise"
                        >
                          <Tag className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => handleOpenSplit(tx)}
                          className="p-1 text-slate-400 hover:text-emerald-600 rounded"
                          title="Split Transaction"
                        >
                          <Split className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Recategorise Modal */}
      {editingTx && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-5 space-y-4 border border-slate-200">
            <div className="flex items-center justify-between border-b pb-2">
              <h3 className="text-sm font-bold text-slate-800">Recategorise Transaction</h3>
              <button onClick={() => setEditingTx(null)} className="text-slate-400 hover:text-slate-600">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="text-xs space-y-1">
              <span className="text-slate-500">Transaction Description:</span>
              <p className="font-semibold text-slate-800">{editingTx.description}</p>
              <p className="font-mono text-indigo-700">{formatINR(editingTx.amount)}</p>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">New Category</label>
              <select
                value={newCat}
                onChange={(e) => setNewCat(e.target.value)}
                className="w-full text-xs p-2 border border-slate-300 rounded-lg"
              >
                <option value="80C_INVESTMENT">80C: Investment (ELSS / PPF / LIC)</option>
                <option value="80C_TUITION">80C: School / College Tuition Fees</option>
                <option value="80C_HL_PRINCIPAL">80C: Home Loan Principal Repayment</option>
                <option value="80D_HEALTH_INSURANCE">80D: Health Insurance Premium</option>
                <option value="80CCD_NPS">80CCD: National Pension System (NPS)</option>
                <option value="80G_DONATION">80G: Charitable Donation</option>
                <option value="24B_HL_INTEREST">24(b): Home Loan Interest</option>
                <option value="80E_EDUCATION_LOAN">80E: Education Loan Interest</option>
                <option value="RENT">Rent Payment (HRA eligible)</option>
                <option value="SALARY">Salary Credit</option>
                <option value="PERSONAL">Personal / Household Expense</option>
              </select>
            </div>

            <label className="flex items-center gap-2 text-xs text-slate-700 cursor-pointer">
              <input
                type="checkbox"
                checked={applySimilar}
                onChange={(e) => setApplySimilar(e.target.checked)}
                className="w-4 h-4 text-indigo-600 rounded"
              />
              <span>Apply this category to matching transactions in the statement</span>
            </label>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setEditingTx(null)}
                className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-md"
              >
                Cancel
              </button>
              <button
                onClick={handleRecategorise}
                className="px-4 py-1.5 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-md"
              >
                Save Category
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Split Modal */}
      {splittingTx && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-5 space-y-4 border border-slate-200">
            <div className="flex items-center justify-between border-b pb-2">
              <h3 className="text-sm font-bold text-slate-800">Split Transaction</h3>
              <button onClick={() => setSplittingTx(null)} className="text-slate-400 hover:text-slate-600">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="text-xs">
              <span className="text-slate-500">Original Total:</span>
              <p className="font-mono text-base font-bold text-slate-900">{formatINR(splittingTx.amount)}</p>
            </div>

            {/* Part 1 */}
            <div className="p-3 bg-slate-50 rounded-lg space-y-2 border border-slate-200 text-xs">
              <span className="font-semibold text-slate-800">Part 1</span>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-[10px] text-slate-500">Category</label>
                  <select
                    value={splitPart1Cat}
                    onChange={(e) => setSplitPart1Cat(e.target.value)}
                    className="w-full p-1.5 border border-slate-300 rounded text-xs"
                  >
                    <option value="24B_HL_INTEREST">24(b): Loan Interest</option>
                    <option value="80C_HL_PRINCIPAL">80C: Principal Repayment</option>
                    <option value="80C_TUITION">80C: Tuition Fees</option>
                    <option value="PERSONAL">Personal Expense</option>
                  </select>
                </div>
                <div>
                  <label className="text-[10px] text-slate-500">Amount (₹)</label>
                  <input
                    type="number"
                    value={splitPart1Amount}
                    onChange={(e) => setSplitPart1Amount(Number(e.target.value))}
                    className="w-full p-1.5 border border-slate-300 rounded text-xs font-mono"
                  />
                </div>
              </div>
            </div>

            {/* Part 2 */}
            <div className="p-3 bg-slate-50 rounded-lg space-y-2 border border-slate-200 text-xs">
              <span className="font-semibold text-slate-800">Part 2</span>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-[10px] text-slate-500">Category</label>
                  <select
                    value={splitPart2Cat}
                    onChange={(e) => setSplitPart2Cat(e.target.value)}
                    className="w-full p-1.5 border border-slate-300 rounded text-xs"
                  >
                    <option value="80C_HL_PRINCIPAL">80C: Principal Repayment</option>
                    <option value="24B_HL_INTEREST">24(b): Loan Interest</option>
                    <option value="PERSONAL">Personal Expense</option>
                    <option value="80C_INVESTMENT">80C: Investment</option>
                  </select>
                </div>
                <div>
                  <label className="text-[10px] text-slate-500">Amount (₹)</label>
                  <input
                    type="number"
                    value={splitPart2Amount}
                    onChange={(e) => setSplitPart2Amount(Number(e.target.value))}
                    className="w-full p-1.5 border border-slate-300 rounded text-xs font-mono"
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-500">
                Sum:{' '}
                <strong
                  className={
                    splitPart1Amount + splitPart2Amount === splittingTx.amount
                      ? 'text-emerald-600'
                      : 'text-rose-600'
                  }
                >
                  {formatINR(splitPart1Amount + splitPart2Amount)}
                </strong>
              </span>
              <div className="flex gap-2">
                <button
                  onClick={() => setSplittingTx(null)}
                  className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-md"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSplitSubmit}
                  className="px-4 py-1.5 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-md"
                >
                  Confirm Split
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
