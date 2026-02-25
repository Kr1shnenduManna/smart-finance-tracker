import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { getTransactions, getCategories, getAccounts, createTransaction, deleteTransaction, getCurrencies, getExchangeRate } from '../api/endpoints';
import { Plus, Trash2, ArrowRightLeft } from 'lucide-react';
import Modal from '../components/Modal';
import { useToast } from '../context/ToastContext';
import { useAuth } from '../context/AuthContext';
import { useCurrency } from '../context/CurrencyContext';
import { formatCurrency } from '../utils/currency';

export default function Transactions() {
  const [transactions, setTransactions] = useState([]);
  const [categories, setCategories] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [currencies, setCurrencies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [filters, setFilters] = useState({ type: '', category: '', start_date: '', end_date: '' });
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const { addToast } = useToast();
  const { user } = useAuth();
  const { fc } = useCurrency();

  const preferredCurrency = user?.preferred_currency || 'INR';

  const [form, setForm] = useState({
    account: '', category: '', transaction_type: 'expense',
    amount: '', description: '', date: new Date().toISOString().split('T')[0], notes: '',
    customCategory: '', input_currency: '',
  });

  // Real-time conversion state
  const [conversionPreview, setConversionPreview] = useState(null);
  const [convertingRate, setConvertingRate] = useState(false);

  useEffect(() => { loadTransactions(); loadMeta(); }, [page, filters]);

  // Set default input_currency to user's preferred currency
  useEffect(() => {
    if (preferredCurrency) {
      setForm(f => ({ ...f, input_currency: f.input_currency || preferredCurrency }));
    }
  }, [preferredCurrency]);

  const loadMeta = async () => {
    try {
      const [catRes, accRes, currRes] = await Promise.all([
        getCategories().catch(() => ({ data: [] })),
        getAccounts().catch(() => ({ data: [] })),
        getCurrencies().catch(() => ({ data: [] })),
      ]);
      setCategories(catRes.data?.results || catRes.data || []);
      setAccounts(accRes.data?.results || accRes.data || []);
      setCurrencies(currRes.data || []);
    } catch (err) { console.error(err); }
  };

  const loadTransactions = async () => {
    setLoading(true);
    try {
      const params = { page };
      if (filters.type) params.type = filters.type;
      if (filters.category) params.category = filters.category;
      if (filters.start_date) params.start_date = filters.start_date;
      if (filters.end_date) params.end_date = filters.end_date;
      const res = await getTransactions(params);
      const data = res.data;
      setTransactions(data.results || data || []);
      if (data.count) setTotalPages(Math.ceil(data.count / 20));
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  // Fetch conversion preview when amount or currency changes
  const fetchConversion = useCallback(async (amount, inputCurrency) => {
    if (!amount || !inputCurrency || inputCurrency === preferredCurrency) {
      setConversionPreview(null);
      return;
    }
    setConvertingRate(true);
    try {
      const res = await getExchangeRate(inputCurrency, preferredCurrency, amount);
      setConversionPreview({
        converted: res.data.converted,
        rate: res.data.rate,
        from: inputCurrency,
        to: preferredCurrency,
      });
    } catch {
      setConversionPreview(null);
    } finally {
      setConvertingRate(false);
    }
  }, [preferredCurrency]);

  // Debounced conversion on amount/currency change
  useEffect(() => {
    const timer = setTimeout(() => {
      if (showModal && form.amount && form.input_currency && form.input_currency !== preferredCurrency) {
        fetchConversion(form.amount, form.input_currency);
      } else {
        setConversionPreview(null);
      }
    }, 400);
    return () => clearTimeout(timer);
  }, [form.amount, form.input_currency, showModal, preferredCurrency, fetchConversion]);

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...form,
        amount: parseFloat(form.amount),
        account: parseInt(form.account) || undefined,
        category: form.category ? parseInt(form.category) : undefined,
      };
      // Only send input_currency if different from preferred
      if (form.input_currency === preferredCurrency) {
        delete payload.input_currency;
      }
      delete payload.customCategory;
      await createTransaction(payload);
      addToast('Transaction added successfully!');
      setShowModal(false);
      setConversionPreview(null);
      setForm({ account: '', category: '', transaction_type: 'expense', amount: '', description: '', date: new Date().toISOString().split('T')[0], notes: '', customCategory: '', input_currency: preferredCurrency });
      loadTransactions();
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to create transaction', 'error');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this transaction?')) return;
    try { await deleteTransaction(id); addToast('Transaction deleted'); loadTransactions(); }
    catch { addToast('Failed to delete', 'error'); }
  };

  // Allow user to type custom category or pick from list
  const filteredCategories = categories.filter((c) => c.category_type === form.transaction_type);

  return (
    <div>
      <div className="page-header">
        <h1>Transactions</h1>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}><Plus size={16} /> Add Transaction</button>
      </div>

      {/* Filters */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-body" style={{ display: 'flex', gap: 16, alignItems: 'flex-end', flexWrap: 'wrap' }}>
          <div className="form-group" style={{ marginBottom: 0, flex: '1 1 150px' }}>
            <label>Type</label>
            <select value={filters.type} onChange={(e) => { setFilters({ ...filters, type: e.target.value }); setPage(1); }}>
              <option value="">All Types</option>
              <option value="income">Income</option>
              <option value="expense">Expense</option>
            </select>
          </div>
          <div className="form-group" style={{ marginBottom: 0, flex: '1 1 150px' }}>
            <label>Category</label>
            <select value={filters.category} onChange={(e) => { setFilters({ ...filters, category: e.target.value }); setPage(1); }}>
              <option value="">All Categories</option>
              {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
          <div className="form-group" style={{ marginBottom: 0, flex: '1 1 150px' }}>
            <label>Start Date</label>
            <input type="date" value={filters.start_date} onChange={(e) => { setFilters({ ...filters, start_date: e.target.value }); setPage(1); }} />
          </div>
          <div className="form-group" style={{ marginBottom: 0, flex: '1 1 150px' }}>
            <label>End Date</label>
            <input type="date" value={filters.end_date} onChange={(e) => { setFilters({ ...filters, end_date: e.target.value }); setPage(1); }} />
          </div>
          <button className="btn btn-secondary btn-sm" onClick={() => { setFilters({ type: '', category: '', start_date: '', end_date: '' }); setPage(1); }}>Clear</button>
        </div>
      </div>

      {/* Table */}
      <div className="card">
        <div className="card-body">
          {loading ? (
            <div className="loading-spinner"><div className="spinner" /></div>
          ) : transactions.length === 0 ? (
            <div className="empty-state">
              <h3>No transactions found</h3>
              <p>Start tracking your finances by adding your first transaction.</p>
              <button className="btn btn-primary" onClick={() => setShowModal(true)}><Plus size={16} /> Add Transaction</button>
            </div>
          ) : (
            <div className="table-wrapper">
              <table>
                <thead><tr><th>Date</th><th>Description</th><th>Category</th><th>Type</th><th>Amount</th><th>Actions</th></tr></thead>
                <tbody>
                  {transactions.map((tx) => (
                    <tr key={tx.id}>
                      <td>{new Date(tx.date).toLocaleDateString('en-IN', { month: 'short', day: 'numeric', year: 'numeric' })}</td>
                      <td style={{ fontWeight: 500 }}>{tx.description || '—'}</td>
                      <td><span className="badge-tag" style={{ background: 'var(--gray-100)', color: 'var(--gray-700)' }}>{tx.category_name || 'Uncategorized'}</span></td>
                      <td><span className={`badge-tag ${tx.transaction_type === 'income' ? 'badge-income' : 'badge-expense'}`}>{tx.transaction_type}</span></td>
                      <td style={{ fontWeight: 700, color: tx.transaction_type === 'income' ? 'var(--success)' : 'var(--gray-800)' }}>
                        <div>
                          {tx.transaction_type === 'income' ? '+' : '-'}{fc(tx.amount, tx.currency || 'INR')}
                        </div>
                        {tx.original_currency && tx.original_currency !== tx.currency && (
                          <div style={{ fontSize: 11, color: 'var(--gray-400)', fontWeight: 400 }}>
                            {formatCurrency(tx.original_amount, tx.original_currency)}
                          </div>
                        )}
                      </td>
                      <td><div className="table-actions"><button title="Delete" className="delete" onClick={() => handleDelete(tx.id)}><Trash2 size={14} /></button></div></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {totalPages > 1 && (
            <div className="pagination">
              <button disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</button>
              {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => i + 1).map((p) => (
                <button key={p} className={page === p ? 'active' : ''} onClick={() => setPage(p)}>{p}</button>
              ))}
              <button disabled={page >= totalPages} onClick={() => setPage(page + 1)}>Next</button>
            </div>
          )}
        </div>
      </div>

      {/* Create Modal */}
      {showModal && (
        <Modal title="Add Transaction" onClose={() => setShowModal(false)}>
          <form onSubmit={handleCreate}>
            <div className="form-group">
              <label>Type</label>
              <select value={form.transaction_type} onChange={(e) => setForm({ ...form, transaction_type: e.target.value, category: '' })} required>
                <option value="expense">Expense</option>
                <option value="income">Income</option>
              </select>
            </div>
            <div className="form-group">
              <label>Amount</label>
              <div style={{ display: 'flex', gap: 8 }}>
                <select
                  value={form.input_currency}
                  onChange={(e) => setForm({ ...form, input_currency: e.target.value })}
                  style={{ width: 110, flex: '0 0 110px' }}
                >
                  {currencies.map((c) => (
                    <option key={c.code} value={c.code}>{c.symbol} {c.code}</option>
                  ))}
                </select>
                <input type="number" step="0.01" placeholder="0.00" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} required style={{ flex: 1 }} />
              </div>
              {/* Real-time conversion preview */}
              {conversionPreview && (
                <div style={{
                  marginTop: 8,
                  padding: '8px 12px',
                  background: 'var(--gray-50)',
                  borderRadius: 8,
                  border: '1px solid var(--gray-200)',
                  fontSize: 13,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                }}>
                  <ArrowRightLeft size={14} style={{ color: 'var(--primary)' }} />
                  <span>
                    <strong>{formatCurrency(conversionPreview.converted, conversionPreview.to)}</strong>
                    <span style={{ color: 'var(--gray-400)', marginLeft: 8 }}>
                      (1 {conversionPreview.from} = {Number(conversionPreview.rate).toFixed(4)} {conversionPreview.to})
                    </span>
                  </span>
                </div>
              )}
              {convertingRate && (
                <div style={{ fontSize: 12, color: 'var(--gray-400)', marginTop: 4 }}>Fetching rate...</div>
              )}
            </div>
            <div className="form-group">
              <label>Description</label>
              <input type="text" placeholder="e.g. Swiggy Order, Uber Ride" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
            </div>
            <div className="form-group">
              <label>Category</label>
              <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
                <option value="">Auto-categorize (ML)</option>
                {filteredCategories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
              <div style={{ fontSize: 12, color: 'var(--gray-400)', marginTop: 4 }}>
                Want a custom category? <Link to="/categories" style={{ color: 'var(--primary)' }}>Manage Categories</Link>
              </div>
            </div>
            <div className="form-group">
              <label>Account</label>
              <select value={form.account} onChange={(e) => setForm({ ...form, account: e.target.value })} required>
                <option value="">Select account</option>
                {accounts.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label>Date</label>
              <input type="date" value={form.date} onChange={(e) => setForm({ ...form, date: e.target.value })} required />
            </div>
            <div className="form-group">
              <label>Notes (optional)</label>
              <textarea rows={2} value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
            </div>
            <div className="modal-actions">
              <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
              <button type="submit" className="btn btn-primary">Add Transaction</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
