import { useState, useEffect } from 'react';
import { getGoals, getGoalsSummary, createGoal, deleteGoal, addGoalContribution, completeGoal, getAccounts } from '../api/endpoints';
import { Plus, Target, TrendingUp, CheckCircle, Trash2, Calendar, Sparkles, PiggyBank, Flag } from 'lucide-react';
import Modal from '../components/Modal';
import { useToast } from '../context/ToastContext';
import { useCurrency } from '../context/CurrencyContext';

const categoryLabels = {
  emergency: 'Emergency Fund', vacation: 'Vacation', car: 'Car', home: 'Home',
  education: 'Education', retirement: 'Retirement', investment: 'Investment',
  debt_payoff: 'Debt Payoff', other: 'Other',
};

export default function SavingsGoals() {
  const [goals, setGoals] = useState([]);
  const [summary, setSummary] = useState({});
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [showContributionModal, setShowContributionModal] = useState(false);
  const [selectedGoal, setSelectedGoal] = useState(null);
  const [contributionAmount, setContributionAmount] = useState('');
  const [contributionSource, setContributionSource] = useState('');
  const { addToast } = useToast();
  const { fc, symbol } = useCurrency();

  const nextYear = new Date(new Date().getFullYear() + 1, new Date().getMonth(), new Date().getDate()).toISOString().split('T')[0];

  const [form, setForm] = useState({
    name: '', category: 'emergency', priority: 'medium',
    target_amount: '', target_date: nextYear, description: '', account: '',
  });

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [goalsRes, summaryRes, accountsRes] = await Promise.all([
        getGoals().catch(() => ({ data: [] })),
        getGoalsSummary().catch(() => ({ data: {} })),
        getAccounts().catch(() => ({ data: [] })),
      ]);
      setGoals(goalsRes.data?.results || goalsRes.data || []);
      setSummary(summaryRes.data || {});
      setAccounts(accountsRes.data?.results || accountsRes.data || []);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      const payload = { ...form, target_amount: parseFloat(form.target_amount) };
      if (!payload.account) delete payload.account;
      await createGoal(payload);
      addToast('Savings goal created!');
      setShowModal(false);
      setForm({ name: '', category: 'emergency', priority: 'medium', target_amount: '', target_date: nextYear, description: '', account: '' });
      loadData();
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to create goal', 'error');
    }
  };

  const handleAddContribution = async (e) => {
    e.preventDefault();
    if (!selectedGoal) return;
    try {
      await addGoalContribution(selectedGoal.id, { amount: parseFloat(contributionAmount), source: contributionSource });
      addToast('Contribution added!');
      setShowContributionModal(false);
      setContributionAmount('');
      setContributionSource('');
      setSelectedGoal(null);
      loadData();
    } catch { addToast('Failed to add contribution', 'error'); }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this goal?')) return;
    try { await deleteGoal(id); addToast('Goal deleted'); loadData(); }
    catch { addToast('Failed to delete', 'error'); }
  };

  const handleComplete = async (id) => {
    try { await completeGoal(id); addToast('Goal completed! 🎉'); loadData(); }
    catch { addToast('Failed to complete goal', 'error'); }
  };

  const priorityStyle = {
    high: { bg: 'var(--danger-light)', color: 'var(--danger)' },
    medium: { bg: 'var(--warning-light)', color: 'var(--warning)' },
    low: { bg: 'var(--info-light)', color: 'var(--info)' },
  };

  // Calculate overall progress
  const overallProgress = summary.total_target_amount > 0
    ? ((parseFloat(summary.total_saved_amount) || 0) / parseFloat(summary.total_target_amount) * 100).toFixed(0)
    : 0;

  return (
    <div>
      <div className="page-header">
        <h1>Savings Goals</h1>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}><Plus size={16} /> New Goal</button>
      </div>

      {/* Summary Stats */}
      <div className="stat-cards">
        <div className="stat-card">
          <div className="stat-top">
            <span className="stat-label">Active Goals</span>
            <div style={{ width: 36, height: 36, borderRadius: 10, background: 'rgba(79,70,229,.08)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Target size={18} color="var(--primary)" />
            </div>
          </div>
          <div className="stat-value">{summary.total_active || 0}</div>
          <div style={{ fontSize: 12, color: 'var(--gray-400)' }}>In progress</div>
        </div>

        <div className="stat-card">
          <div className="stat-top">
            <span className="stat-label">Total Saved</span>
            <div style={{ width: 36, height: 36, borderRadius: 10, background: 'rgba(34,197,94,.08)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <PiggyBank size={18} color="var(--success)" />
            </div>
          </div>
          <div className="stat-value income" style={{ fontSize: 24 }}>{fc(summary.total_saved_amount)}</div>
          <div style={{ fontSize: 12, color: 'var(--gray-400)' }}>of {fc(summary.total_target_amount)}</div>
        </div>

        <div className="stat-card">
          <div className="stat-top">
            <span className="stat-label">Overall Progress</span>
            <div style={{ width: 36, height: 36, borderRadius: 10, background: 'rgba(245,158,11,.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <TrendingUp size={18} color="var(--warning)" />
            </div>
          </div>
          <div className="stat-value" style={{ fontSize: 28 }}>{overallProgress}%</div>
          <div style={{ background: 'var(--gray-100)', borderRadius: 8, height: 6, overflow: 'hidden', marginTop: 4 }}>
            <div style={{ width: `${Math.min(overallProgress, 100)}%`, background: 'var(--primary)', height: '100%', borderRadius: 8, transition: 'width .5s ease' }} />
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-top">
            <span className="stat-label">On Track</span>
            <div style={{ width: 36, height: 36, borderRadius: 10, background: 'rgba(34,197,94,.08)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Flag size={18} color="var(--success)" />
            </div>
          </div>
          <div className="stat-value">{summary.on_track_count || 0}</div>
          <div style={{ fontSize: 12, color: 'var(--gray-400)' }}>{summary.total_completed || 0} completed</div>
        </div>
      </div>

      {/* Goals Grid */}
      {loading ? (
        <div className="loading-spinner"><div className="spinner" /></div>
      ) : goals.length === 0 ? (
        <div className="empty-state">
          <h3>No savings goals yet</h3>
          <p>Create a goal to start saving towards what matters most.</p>
          <button className="btn btn-primary" onClick={() => setShowModal(true)}><Plus size={16} /> New Goal</button>
        </div>
      ) : (
        <div className="budget-grid">
          {goals.map((goal) => {
            const pct = Math.min(goal.progress_percentage || 0, 100);
            const ps = priorityStyle[goal.priority] || priorityStyle.medium;
            const barColor = goal.is_on_track ? 'var(--success)' : pct >= 50 ? 'var(--warning)' : 'var(--danger)';

            return (
              <div className="card" key={goal.id}>
                <div className="card-body" style={{ padding: 20 }}>
                  {/* Header */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 600, fontSize: 16, color: 'var(--gray-900)' }}>{goal.name}</div>
                      <div style={{ fontSize: 12, color: 'var(--gray-500)', marginTop: 2 }}>{categoryLabels[goal.category] || goal.category}</div>
                    </div>
                    <span className="badge-tag" style={{ background: ps.bg, color: ps.color, textTransform: 'capitalize', fontSize: 11 }}>
                      {goal.priority}
                    </span>
                  </div>

                  {/* Progress */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, color: 'var(--gray-600)', marginBottom: 6 }}>
                    <span>{fc(goal.current_amount)}</span>
                    <span style={{ fontWeight: 600 }}>{pct.toFixed(0)}%</span>
                  </div>
                  <div style={{ background: 'var(--gray-100)', borderRadius: 8, height: 10, overflow: 'hidden', marginBottom: 8 }}>
                    <div style={{ width: `${pct}%`, background: barColor, height: '100%', borderRadius: 8, transition: 'width 0.5s ease' }} />
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--gray-400)', marginBottom: 16 }}>
                    Target: {fc(goal.target_amount)}
                  </div>

                  {/* Stats row */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 16 }}>
                    <div style={{ background: 'var(--gray-50)', borderRadius: 8, padding: '10px 12px' }}>
                      <div style={{ fontSize: 11, color: 'var(--gray-400)', marginBottom: 2 }}>Days Left</div>
                      <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--gray-800)' }}>{goal.days_remaining ?? '—'}</div>
                    </div>
                    <div style={{ background: 'var(--gray-50)', borderRadius: 8, padding: '10px 12px' }}>
                      <div style={{ fontSize: 11, color: 'var(--gray-400)', marginBottom: 2 }}>Monthly Need</div>
                      <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--primary)' }}>{fc(goal.suggested_monthly_savings)}</div>
                    </div>
                  </div>

                  {/* Target date */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--gray-500)', marginBottom: 12 }}>
                    <Calendar size={12} />
                    Target: {new Date(goal.target_date).toLocaleDateString('en-IN', { month: 'short', day: 'numeric', year: 'numeric' })}
                  </div>

                  {goal.description && (
                    <div style={{ fontSize: 12, color: 'var(--gray-400)', marginBottom: 12, fontStyle: 'italic', lineHeight: 1.5 }}>
                      {goal.description}
                    </div>
                  )}

                  {/* On-track indicator */}
                  {goal.is_on_track !== undefined && (
                    <div style={{
                      display: 'inline-flex', alignItems: 'center', gap: 6,
                      padding: '4px 10px', borderRadius: 20, fontSize: 11, fontWeight: 600,
                      background: goal.is_on_track ? 'var(--success-light)' : 'var(--warning-light)',
                      color: goal.is_on_track ? 'var(--success)' : 'var(--warning)',
                      marginBottom: 16,
                    }}>
                      <Sparkles size={12} />
                      {goal.is_on_track ? 'On Track' : 'Behind Schedule'}
                    </div>
                  )}

                  {/* Actions */}
                  <div style={{ display: 'flex', gap: 8, paddingTop: 16, borderTop: '1px solid var(--gray-100)' }}>
                    <button
                      className="btn btn-primary btn-sm"
                      style={{ flex: 1 }}
                      onClick={() => { setSelectedGoal(goal); setShowContributionModal(true); }}
                    >
                      <Plus size={14} /> Add Funds
                    </button>
                    <button className="btn btn-outline btn-sm" title="Complete" onClick={() => handleComplete(goal.id)}>
                      <CheckCircle size={14} />
                    </button>
                    <button className="btn-icon delete" title="Delete" onClick={() => handleDelete(goal.id)}>
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Create Goal Modal */}
      {showModal && (
        <Modal title="Create Savings Goal" onClose={() => setShowModal(false)}>
          <form onSubmit={handleCreate}>
            <div className="form-group">
              <label>Goal Name</label>
              <input type="text" placeholder="e.g. Emergency Fund, Dream Vacation" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
            </div>
            <div className="form-group">
              <label>Description (optional)</label>
              <textarea rows={2} placeholder="Why is this goal important to you?" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
            </div>
            <div style={{ display: 'flex', gap: 12 }}>
              <div className="form-group" style={{ flex: 1 }}>
                <label>Category</label>
                <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
                  {Object.entries(categoryLabels).map(([key, label]) => (
                    <option key={key} value={key}>{label}</option>
                  ))}
                </select>
              </div>
              <div className="form-group" style={{ flex: 1 }}>
                <label>Priority</label>
                <select value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value })}>
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 12 }}>
              <div className="form-group" style={{ flex: 1 }}>
                <label>Target Amount ({symbol})</label>
                <input type="number" step="0.01" placeholder="e.g. 50000" value={form.target_amount} onChange={(e) => setForm({ ...form, target_amount: e.target.value })} required />
              </div>
              <div className="form-group" style={{ flex: 1 }}>
                <label>Target Date</label>
                <input type="date" value={form.target_date} onChange={(e) => setForm({ ...form, target_date: e.target.value })} required />
              </div>
            </div>
            <div className="form-group">
              <label>Linked Account</label>
              <select value={form.account} onChange={(e) => setForm({ ...form, account: e.target.value })}>
                <option value="">No account (track only)</option>
                {accounts.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
              </select>
              <div style={{ fontSize: 11, color: 'var(--gray-400)', marginTop: 4 }}>Contributions will be deducted from this account and recorded as transactions</div>
            </div>
            <div className="modal-actions">
              <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
              <button type="submit" className="btn btn-primary">Create Goal</button>
            </div>
          </form>
        </Modal>
      )}

      {/* Add Contribution Modal */}
      {showContributionModal && (
        <Modal title="Add Contribution" onClose={() => { setShowContributionModal(false); setSelectedGoal(null); }}>
          <form onSubmit={handleAddContribution}>
            {selectedGoal && (
              <div style={{ background: 'var(--gray-50)', padding: 16, borderRadius: 10, marginBottom: 20 }}>
                <div style={{ fontSize: 12, color: 'var(--gray-500)', marginBottom: 4 }}>Contributing to</div>
                <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--gray-900)', marginBottom: 8 }}>{selectedGoal.name}</div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: 13, color: 'var(--gray-500)' }}>
                    {fc(selectedGoal.current_amount)} / {fc(selectedGoal.target_amount)}
                  </span>
                  <span className="badge-tag" style={{ background: 'var(--primary)', color: '#fff', fontSize: 11 }}>
                    {(selectedGoal.progress_percentage || 0).toFixed(0)}%
                  </span>
                </div>
                <div style={{ background: 'var(--gray-200)', borderRadius: 8, height: 6, overflow: 'hidden', marginTop: 10 }}>
                  <div style={{ width: `${Math.min(selectedGoal.progress_percentage || 0, 100)}%`, background: 'var(--primary)', height: '100%', borderRadius: 8 }} />
                </div>
              </div>
            )}
            <div className="form-group">
              <label>Amount ({symbol})</label>
              <input type="number" step="0.01" placeholder="Enter contribution amount" value={contributionAmount} onChange={(e) => setContributionAmount(e.target.value)} required />
            </div>
            <div className="form-group">
              <label>Source (optional)</label>
              <input type="text" placeholder="e.g. Monthly salary, Bonus" value={contributionSource} onChange={(e) => setContributionSource(e.target.value)} />
            </div>
            <div className="modal-actions">
              <button type="button" className="btn btn-secondary" onClick={() => { setShowContributionModal(false); setSelectedGoal(null); }}>Cancel</button>
              <button type="submit" className="btn btn-primary">Add Contribution</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
