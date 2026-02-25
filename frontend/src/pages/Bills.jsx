import { useState, useEffect } from 'react';
import { getBills, getUpcomingBills, getOverdueBills, getBillsSummary, createBill, deleteBill, markBillPaid, cancelBill, getAccounts, getExpenseCategories } from '../api/endpoints';
import { Plus, AlertTriangle, CheckCircle, Trash2, Clock, Receipt, CalendarClock, CreditCard, XCircle } from 'lucide-react';
import Modal from '../components/Modal';
import { useToast } from '../context/ToastContext';
import { useCurrency } from '../context/CurrencyContext';

export default function Bills() {
  const [bills, setBills] = useState([]);
  const [overdueBills, setOverdueBills] = useState([]);
  const [summary, setSummary] = useState({});
  const [accounts, setAccounts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const { addToast } = useToast();
  const { fc, symbol } = useCurrency();

  const today = new Date().toISOString().split('T')[0];

  const [form, setForm] = useState({
    name: '', amount: '', frequency: 'monthly', description: '',
    due_date: 15, is_automatic: false, notify_days_before: 3,
    account: '', category: '',
  });

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [billRes, overdueRes, summaryRes, accountsRes, categoriesRes] = await Promise.all([
        getBills().catch(() => ({ data: [] })),
        getOverdueBills().catch(() => ({ data: [] })),
        getBillsSummary().catch(() => ({ data: {} })),
        getAccounts().catch(() => ({ data: [] })),
        getExpenseCategories().catch(() => ({ data: [] })),
      ]);
      setBills(billRes.data?.results || billRes.data || []);
      setOverdueBills(overdueRes.data || []);
      setSummary(summaryRes.data || {});
      setAccounts(accountsRes.data?.results || accountsRes.data || []);
      setCategories(categoriesRes.data?.results || categoriesRes.data || []);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...form,
        amount: parseFloat(form.amount),
        due_date: parseInt(form.due_date),
        notify_days_before: parseInt(form.notify_days_before),
        next_due_date: today,
        status: 'pending',
      };
      if (!payload.account) delete payload.account;
      if (!payload.category) delete payload.category;
      await createBill(payload);
      addToast('Bill created successfully!');
      setShowModal(false);
      setForm({ name: '', amount: '', frequency: 'monthly', description: '', due_date: 15, is_automatic: false, notify_days_before: 3, account: '', category: '' });
      loadData();
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to create bill', 'error');
    }
  };

  const handleMarkPaid = async (bill) => {
    try {
      await markBillPaid(bill.id, { amount_paid: bill.amount });
      addToast('Bill marked as paid!');
      loadData();
    } catch { addToast('Failed to mark bill as paid', 'error'); }
  };

  const handleCancel = async (id) => {
    try {
      await cancelBill(id);
      addToast('Bill cancelled');
      loadData();
    } catch { addToast('Failed to cancel', 'error'); }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this bill?')) return;
    try { await deleteBill(id); addToast('Bill deleted'); loadData(); }
    catch { addToast('Failed to delete', 'error'); }
  };

  const getStatusBadge = (status) => {
    const map = {
      paid: { bg: 'var(--success-light)', color: 'var(--success)' },
      pending: { bg: 'var(--info-light)', color: 'var(--info)' },
      overdue: { bg: 'var(--danger-light)', color: 'var(--danger)' },
      cancelled: { bg: 'var(--gray-100)', color: 'var(--gray-500)' },
    };
    const s = map[status] || map.pending;
    return <span className="badge-tag" style={{ background: s.bg, color: s.color, textTransform: 'capitalize' }}>{status}</span>;
  };

  return (
    <div>
      <div className="page-header">
        <h1>Bills & Reminders</h1>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}><Plus size={16} /> Add Bill</button>
      </div>

      {/* Summary Stats */}
      <div className="stat-cards">
        <div className="stat-card">
          <div className="stat-top">
            <span className="stat-label">Active Bills</span>
            <div style={{ width: 36, height: 36, borderRadius: 10, background: 'rgba(79,70,229,.08)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Receipt size={18} color="var(--primary)" />
            </div>
          </div>
          <div className="stat-value">{summary.active_bills || 0}</div>
          <div style={{ fontSize: 12, color: 'var(--gray-400)' }}>{summary.pending_bills || 0} pending</div>
        </div>

        <div className="stat-card">
          <div className="stat-top">
            <span className="stat-label">Overdue</span>
            <div style={{ width: 36, height: 36, borderRadius: 10, background: summary.overdue_bills > 0 ? 'var(--danger-light)' : 'var(--success-light)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <AlertTriangle size={18} color={summary.overdue_bills > 0 ? 'var(--danger)' : 'var(--success)'} />
            </div>
          </div>
          <div className="stat-value" style={{ color: summary.overdue_bills > 0 ? 'var(--danger)' : 'var(--success)' }}>{summary.overdue_bills || 0}</div>
          <div style={{ fontSize: 12, color: 'var(--gray-400)' }}>{summary.overdue_bills > 0 ? 'Needs attention' : 'All clear'}</div>
        </div>

        <div className="stat-card">
          <div className="stat-top">
            <span className="stat-label">Monthly Total</span>
            <div style={{ width: 36, height: 36, borderRadius: 10, background: 'rgba(245,158,11,.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <CreditCard size={18} color="var(--warning)" />
            </div>
          </div>
          <div className="stat-value" style={{ fontSize: 24 }}>{fc(summary.total_monthly_amount)}</div>
          <div style={{ fontSize: 12, color: 'var(--gray-400)' }}>Monthly commitment</div>
        </div>

        <div className="stat-card">
          <div className="stat-top">
            <span className="stat-label">Total Bills</span>
            <div style={{ width: 36, height: 36, borderRadius: 10, background: 'rgba(59,130,246,.08)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <CalendarClock size={18} color="var(--info)" />
            </div>
          </div>
          <div className="stat-value">{summary.total_bills || 0}</div>
          <div style={{ fontSize: 12, color: 'var(--gray-400)' }}>Lifetime tracked</div>
        </div>
      </div>

      {/* Overdue Alert Banner */}
      {overdueBills.length > 0 && (
        <div className="card" style={{ marginBottom: 24, background: 'linear-gradient(135deg, #FFF3CD, #FFEEBA)', border: '1px solid #FFD93D' }}>
          <div className="card-body" style={{ padding: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
              <AlertTriangle size={18} color="#856404" />
              <strong style={{ color: '#856404' }}>Overdue Bills ({overdueBills.length})</strong>
            </div>
            {overdueBills.map((bill) => (
              <div key={bill.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderTop: '1px solid rgba(133,100,4,.12)' }}>
                <span style={{ fontSize: 13, color: '#856404' }}>
                  ⚠ {bill.name} — {fc(bill.amount)} (due {new Date(bill.next_due_date).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' })})
                </span>
                <button className="btn btn-sm" style={{ background: '#856404', color: '#fff', padding: '4px 14px' }} onClick={() => handleMarkPaid(bill)}>Mark Paid</button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Bills Table */}
      {loading ? (
        <div className="loading-spinner"><div className="spinner" /></div>
      ) : bills.length === 0 ? (
        <div className="empty-state">
          <h3>No bills yet</h3>
          <p>Add your first bill to track payments and get reminders.</p>
          <button className="btn btn-primary" onClick={() => setShowModal(true)}><Plus size={16} /> Add Bill</button>
        </div>
      ) : (
        <div className="card">
          <div className="card-body">
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Bill</th>
                    <th>Amount</th>
                    <th>Frequency</th>
                    <th>Next Due</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {bills.map((bill) => (
                    <tr key={bill.id}>
                      <td>
                        <div style={{ fontWeight: 600, color: 'var(--gray-800)' }}>{bill.name}</div>
                        {bill.description && <div style={{ fontSize: 12, color: 'var(--gray-400)', marginTop: 2 }}>{bill.description}</div>}
                      </td>
                      <td style={{ fontWeight: 700 }}>{fc(bill.amount)}</td>
                      <td>
                        <span className="badge-tag" style={{ background: 'var(--gray-100)', color: 'var(--gray-700)', textTransform: 'capitalize' }}>
                          {bill.frequency}
                        </span>
                      </td>
                      <td>
                        <div style={{ fontSize: 13 }}>{new Date(bill.next_due_date).toLocaleDateString('en-IN', { month: 'short', day: 'numeric', year: 'numeric' })}</div>
                        {bill.days_until_due !== undefined && bill.status === 'pending' && (
                          <div style={{ fontSize: 11, color: bill.days_until_due <= 3 ? 'var(--warning)' : 'var(--gray-400)', marginTop: 2, display: 'flex', alignItems: 'center', gap: 4 }}>
                            <Clock size={10} /> {bill.days_until_due >= 0 ? `${bill.days_until_due}d left` : `${Math.abs(bill.days_until_due)}d overdue`}
                          </div>
                        )}
                      </td>
                      <td>{getStatusBadge(bill.is_overdue ? 'overdue' : bill.status)}</td>
                      <td>
                        <div className="table-actions">
                          {bill.status === 'pending' && (
                            <button title="Mark Paid" onClick={() => handleMarkPaid(bill)}><CheckCircle size={14} /></button>
                          )}
                          {bill.status === 'pending' && (
                            <button title="Cancel" onClick={() => handleCancel(bill.id)}><XCircle size={14} /></button>
                          )}
                          <button className="delete" title="Delete" onClick={() => handleDelete(bill.id)}><Trash2 size={14} /></button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Create Bill Modal */}
      {showModal && (
        <Modal title="Add New Bill" onClose={() => setShowModal(false)}>
          <form onSubmit={handleCreate}>
            <div className="form-group">
              <label>Bill Name</label>
              <input type="text" placeholder="e.g. Electric Bill, Internet, Rent" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
            </div>
            <div className="form-group">
              <label>Description (optional)</label>
              <input type="text" placeholder="Brief description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
            </div>
            <div style={{ display: 'flex', gap: 12 }}>
              <div className="form-group" style={{ flex: 1 }}>
                <label>Amount ({symbol})</label>
                <input type="number" step="0.01" placeholder="0.00" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} required />
              </div>
              <div className="form-group" style={{ flex: 1 }}>
                <label>Frequency</label>
                <select value={form.frequency} onChange={(e) => setForm({ ...form, frequency: e.target.value })}>
                  <option value="once">One-time</option>
                  <option value="weekly">Weekly</option>
                  <option value="biweekly">Bi-weekly</option>
                  <option value="monthly">Monthly</option>
                  <option value="quarterly">Quarterly</option>
                  <option value="yearly">Yearly</option>
                </select>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 12 }}>
              <div className="form-group" style={{ flex: 1 }}>
                <label>Due Date (Day of Month)</label>
                <input type="number" min="1" max="31" placeholder="15" value={form.due_date} onChange={(e) => setForm({ ...form, due_date: e.target.value })} />
              </div>
              <div className="form-group" style={{ flex: 1 }}>
                <label>Remind Before (days)</label>
                <input type="number" min="0" placeholder="3" value={form.notify_days_before} onChange={(e) => setForm({ ...form, notify_days_before: e.target.value })} />
              </div>
            </div>
            <div style={{ display: 'flex', gap: 12 }}>
              <div className="form-group" style={{ flex: 1 }}>
                <label>Account</label>
                <select value={form.account} onChange={(e) => setForm({ ...form, account: e.target.value })}>
                  <option value="">No account</option>
                  {accounts.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
                </select>
              </div>
              <div className="form-group" style={{ flex: 1 }}>
                <label>Category</label>
                <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
                  <option value="">Auto (Bills)</option>
                  {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
            </div>
            <div className="form-group" style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <input type="checkbox" id="auto_pay" checked={form.is_automatic} onChange={(e) => setForm({ ...form, is_automatic: e.target.checked })} style={{ width: 'auto' }} />
              <label htmlFor="auto_pay" style={{ marginBottom: 0, cursor: 'pointer' }}>Auto-pay from account</label>
            </div>
            {form.is_automatic && !form.account && (
              <div style={{ fontSize: 12, color: 'var(--danger)', marginTop: -8, marginBottom: 8 }}>⚠ Auto-pay requires an account to be selected</div>
            )}
            <div className="modal-actions">
              <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
              <button type="submit" className="btn btn-primary">Create Bill</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
