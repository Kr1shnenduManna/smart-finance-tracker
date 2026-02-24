import { useState, useEffect } from 'react';
import { getAccounts, createAccount, updateAccount, deleteAccount } from '../api/endpoints';
import { Plus, Pencil, Trash2, Wallet, AlertTriangle } from 'lucide-react';
import Modal from '../components/Modal';
import { useToast } from '../context/ToastContext';

function formatCurrency(n) {
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(n || 0);
}

const ACCOUNT_TYPES = [
  { value: 'savings', label: 'Savings Account' },
  { value: 'checking', label: 'Current Account' },
  { value: 'credit_card', label: 'Credit Card' },
  { value: 'cash', label: 'Cash' },
  { value: 'investment', label: 'Investment' },
  { value: 'other', label: 'Other' },
];

export default function Settings() {
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState(null);
  const { addToast } = useToast();

  const [form, setForm] = useState({
    name: '', account_type: 'savings', balance: '', currency: 'INR',
  });

  useEffect(() => { loadAccounts(); }, []);

  const loadAccounts = async () => {
    setLoading(true);
    try {
      const res = await getAccounts();
      setAccounts(res.data?.results || res.data || []);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const openCreate = () => {
    setEditing(null);
    setForm({ name: '', account_type: 'savings', balance: '', currency: 'INR' });
    setShowModal(true);
  };

  const openEdit = (acc) => {
    setEditing(acc);
    setForm({ name: acc.name, account_type: acc.account_type, balance: acc.balance, currency: acc.currency || 'INR' });
    setShowModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = { ...form, balance: parseFloat(form.balance) || 0 };
      if (editing) {
        await updateAccount(editing.id, payload);
        addToast('Account updated');
      } else {
        await createAccount(payload);
        addToast('Account created');
      }
      setShowModal(false);
      loadAccounts();
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to save account', 'error');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this account? All associated transactions will be deleted.')) return;
    try { await deleteAccount(id); addToast('Account deleted'); loadAccounts(); }
    catch { addToast('Failed to delete account', 'error'); }
  };

  return (
    <div>
      <div className="page-header">
        <h1>Settings</h1>
      </div>

      {/* Currency Info */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-header"><h3>Currency</h3></div>
        <div className="card-body">
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span style={{ fontSize: 28, fontWeight: 700 }}>₹</span>
            <div>
              <div style={{ fontWeight: 600 }}>Indian Rupee (INR)</div>
              <div style={{ fontSize: 12, color: 'var(--gray-500)' }}>All amounts are displayed in INR</div>
            </div>
          </div>
        </div>
      </div>

      {/* Financial Accounts */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3>Financial Accounts</h3>
          <button className="btn btn-primary btn-sm" onClick={openCreate}><Plus size={14} /> Add Account</button>
        </div>
        <div className="card-body">
          {loading ? (
            <div className="loading-spinner"><div className="spinner" /></div>
          ) : accounts.length === 0 ? (
            <div className="empty-state">
              <Wallet size={32} color="var(--gray-400)" />
              <h3>No accounts</h3>
              <p>Add your first financial account to start tracking.</p>
              <button className="btn btn-primary" onClick={openCreate}><Plus size={14} /> Add Account</button>
            </div>
          ) : (
            <div className="table-wrapper">
              <table>
                <thead><tr><th>Account</th><th>Type</th><th>Balance</th><th>Actions</th></tr></thead>
                <tbody>
                  {accounts.map((acc) => (
                    <tr key={acc.id}>
                      <td style={{ fontWeight: 600 }}>{acc.name}</td>
                      <td><span className="badge-tag">{ACCOUNT_TYPES.find(t => t.value === acc.account_type)?.label || acc.account_type}</span></td>
                      <td style={{ fontWeight: 700, color: parseFloat(acc.balance) >= 0 ? 'var(--success)' : 'var(--danger)' }}>
                        {formatCurrency(acc.balance)}
                      </td>
                      <td>
                        <div className="table-actions">
                          <button title="Edit" onClick={() => openEdit(acc)}><Pencil size={14} /></button>
                          <button title="Delete" className="delete" onClick={() => handleDelete(acc.id)}><Trash2 size={14} /></button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Danger Zone */}
      <div className="card" style={{ border: '1px solid var(--danger)' }}>
        <div className="card-header" style={{ borderBottomColor: 'var(--danger)' }}>
          <h3 style={{ color: 'var(--danger)', display: 'flex', alignItems: 'center', gap: 8 }}>
            <AlertTriangle size={18} /> Danger Zone
          </h3>
        </div>
        <div className="card-body">
          <p style={{ fontSize: 13, color: 'var(--gray-600)', marginBottom: 12 }}>
            These actions are irreversible. Please be careful.
          </p>
          <button className="btn" style={{ background: 'var(--danger)', color: '#fff' }} onClick={() => addToast('Contact admin to delete account', 'info')}>
            Delete My Account
          </button>
        </div>
      </div>

      {/* Account Modal */}
      {showModal && (
        <Modal title={editing ? 'Edit Account' : 'Add Account'} onClose={() => setShowModal(false)}>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Account Name</label>
              <input type="text" placeholder="e.g. HDFC Savings, Paytm Wallet" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
            </div>
            <div className="form-group">
              <label>Account Type</label>
              <select value={form.account_type} onChange={(e) => setForm({ ...form, account_type: e.target.value })}>
                {ACCOUNT_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label>Balance (₹)</label>
              <input type="number" step="0.01" placeholder="0.00" value={form.balance} onChange={(e) => setForm({ ...form, balance: e.target.value })} required />
            </div>
            <div className="modal-actions">
              <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
              <button type="submit" className="btn btn-primary">{editing ? 'Update' : 'Add Account'}</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
