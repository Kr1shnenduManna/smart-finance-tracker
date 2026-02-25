import { useState, useEffect } from 'react';
import { getBudgets, getActiveBudgets, getBudgetAlerts, getCategories, createBudget, deleteBudget } from '../api/endpoints';
import { Plus, AlertTriangle, Trash2, TrendingUp } from 'lucide-react';
import Modal from '../components/Modal';
import { useToast } from '../context/ToastContext';
import { useCurrency } from '../context/CurrencyContext';

export default function Budgets() {
  const [budgets, setBudgets] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const { addToast } = useToast();
  const { fc, symbol } = useCurrency();

  const today = new Date().toISOString().split('T')[0];
  const monthEnd = new Date(new Date().getFullYear(), new Date().getMonth() + 1, 0).toISOString().split('T')[0];

  const [form, setForm] = useState({
    category: '', amount: '', period: 'monthly',
    start_date: today, end_date: monthEnd, alert_threshold: 80,
  });

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [budgetRes, alertRes, catRes] = await Promise.all([
        getBudgets().catch(() => ({ data: [] })),
        getBudgetAlerts().catch(() => ({ data: [] })),
        getCategories().catch(() => ({ data: [] })),
      ]);
      setBudgets(budgetRes.data?.results || budgetRes.data || []);
      setAlerts(alertRes.data || []);
      setCategories(catRes.data?.results || catRes.data || []);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      await createBudget({
        ...form,
        amount: parseFloat(form.amount),
        category: parseInt(form.category),
        alert_threshold: parseInt(form.alert_threshold),
      });
      addToast('Budget created successfully!');
      setShowModal(false);
      setForm({ category: '', amount: '', period: 'monthly', start_date: today, end_date: monthEnd, alert_threshold: 80 });
      loadData();
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to create budget', 'error');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this budget?')) return;
    try { await deleteBudget(id); addToast('Budget deleted'); loadData(); }
    catch { addToast('Failed to delete', 'error'); }
  };

  const expenseCategories = categories.filter((c) => c.category_type === 'expense');

  return (
    <div>
      <div className="page-header">
        <h1>Budgets</h1>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}><Plus size={16} /> Create Budget</button>
      </div>

      {/* Alerts Banner */}
      {alerts.length > 0 && (
        <div className="card" style={{ marginBottom: 24, background: 'linear-gradient(135deg, #FFF3CD, #FFEEBA)', border: '1px solid #FFD93D' }}>
          <div className="card-body" style={{ padding: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
              <AlertTriangle size={18} color="#856404" />
              <strong style={{ color: '#856404' }}>Budget Alerts</strong>
            </div>
            {alerts.map((a, i) => (
              <div key={i} style={{ fontSize: 13, color: '#856404', padding: '4px 0' }}>
                ⚠ {a.category || a.category_name}: {a.message || `${a.spent_percentage?.toFixed(0)}% of budget used`}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Budget Cards */}
      {loading ? (
        <div className="loading-spinner"><div className="spinner" /></div>
      ) : budgets.length === 0 ? (
        <div className="empty-state">
          <h3>No budgets yet</h3>
          <p>Create your first budget to start tracking spending limits.</p>
          <button className="btn btn-primary" onClick={() => setShowModal(true)}><Plus size={16} /> Create Budget</button>
        </div>
      ) : (
        <div className="budget-grid">
          {budgets.map((b) => {
            const pct = Math.min(b.spent_percentage || 0, 100);
            const isOver = pct >= 100;
            const isWarning = pct >= (b.alert_threshold || 80);
            const barColor = isOver ? 'var(--danger)' : isWarning ? '#fbbf24' : 'var(--primary)';

            return (
              <div className="card" key={b.id}>
                <div className="card-body" style={{ padding: 20 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: 16 }}>{b.category_name}</div>
                      <div style={{ fontSize: 12, color: 'var(--gray-500)', textTransform: 'capitalize' }}>{b.period}</div>
                    </div>
                    <button className="btn-icon delete" onClick={() => handleDelete(b.id)} title="Delete"><Trash2 size={14} /></button>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, color: 'var(--gray-600)', marginBottom: 6 }}>
                    <span>Spent: {fc(b.spent_amount)}</span>
                    <span>of {fc(b.amount)}</span>
                  </div>

                  {/* Progress bar */}
                  <div style={{ background: 'var(--gray-100)', borderRadius: 8, height: 10, overflow: 'hidden', marginBottom: 12 }}>
                    <div style={{ width: `${pct}%`, background: barColor, height: '100%', borderRadius: 8, transition: 'width 0.5s ease' }} />
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ fontSize: 12, fontWeight: 600, color: isOver ? 'var(--danger)' : 'var(--gray-600)' }}>
                      {pct.toFixed(0)}% used
                    </div>
                    {b.remaining_amount !== undefined && (
                      <div style={{ fontSize: 12, color: b.remaining_amount >= 0 ? 'var(--success)' : 'var(--danger)' }}>
                        {b.remaining_amount >= 0 ? `${fc(b.remaining_amount)} left` : `${fc(Math.abs(b.remaining_amount))} over`}
                      </div>
                    )}
                  </div>

                  {/* ML Prediction */}
                  {b.predicted_amount && (
                    <div style={{ marginTop: 12, padding: '8px 12px', background: 'var(--gray-50)', borderRadius: 8, display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--gray-600)' }}>
                      <TrendingUp size={14} color="var(--primary)" />
                      ML Predicted: {fc(b.predicted_amount)}
                    </div>
                  )}

                  <div style={{ marginTop: 8, fontSize: 11, color: 'var(--gray-400)' }}>
                    {new Date(b.start_date).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' })} — {new Date(b.end_date).toLocaleDateString('en-IN', { month: 'short', day: 'numeric', year: 'numeric' })}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Create Budget Modal */}
      {showModal && (
        <Modal title="Create Budget" onClose={() => setShowModal(false)}>
          <form onSubmit={handleCreate}>
            <div className="form-group">
              <label>Category</label>
              <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} required>
                <option value="">Select category</option>
                {expenseCategories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label>Budget Amount ({symbol})</label>
              <input type="number" step="0.01" placeholder="e.g. 5000" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} required />
            </div>
            <div className="form-group">
              <label>Period</label>
              <select value={form.period} onChange={(e) => setForm({ ...form, period: e.target.value })}>
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
                <option value="yearly">Yearly</option>
              </select>
            </div>
            <div style={{ display: 'flex', gap: 12 }}>
              <div className="form-group" style={{ flex: 1 }}>
                <label>Start Date</label>
                <input type="date" value={form.start_date} onChange={(e) => setForm({ ...form, start_date: e.target.value })} required />
              </div>
              <div className="form-group" style={{ flex: 1 }}>
                <label>End Date</label>
                <input type="date" value={form.end_date} onChange={(e) => setForm({ ...form, end_date: e.target.value })} required />
              </div>
            </div>
            <div className="form-group">
              <label>Alert Threshold (%)</label>
              <input type="number" min="1" max="100" value={form.alert_threshold} onChange={(e) => setForm({ ...form, alert_threshold: e.target.value })} />
            </div>
            <div className="modal-actions">
              <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
              <button type="submit" className="btn btn-primary">Create Budget</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
