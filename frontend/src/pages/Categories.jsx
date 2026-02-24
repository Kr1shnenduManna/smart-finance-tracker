import { useState, useEffect } from 'react';
import { getCategories } from '../api/endpoints';
import API from '../api/axios';
import { Plus, Pencil, Trash2, Tag } from 'lucide-react';
import Modal from '../components/Modal';
import { useToast } from '../context/ToastContext';

const PRESET_COLORS = ['#6366f1', '#f43f5e', '#10b981', '#f59e0b', '#3b82f6', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316', '#64748b', '#ef4444', '#22c55e'];
const PRESET_ICONS = ['🍔', '🚗', '🏠', '💊', '🎮', '📚', '✈️', '🛒', '💰', '📱', '🎬', '💳', '👕', '🎁', '⚡', '🏥'];

export default function Categories() {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState(null);
  const [filter, setFilter] = useState('all');
  const { addToast } = useToast();

  const [form, setForm] = useState({
    name: '', category_type: 'expense', description: '', icon: '🏷️', color: '#6366f1',
  });

  useEffect(() => { loadCategories(); }, []);

  const loadCategories = async () => {
    setLoading(true);
    try {
      const res = await getCategories();
      setCategories(res.data?.results || res.data || []);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const openCreate = () => {
    setEditing(null);
    setForm({ name: '', category_type: 'expense', description: '', icon: '🏷️', color: '#6366f1' });
    setShowModal(true);
  };

  const openEdit = (cat) => {
    setEditing(cat);
    setForm({ name: cat.name, category_type: cat.category_type, description: cat.description || '', icon: cat.icon || '🏷️', color: cat.color || '#6366f1' });
    setShowModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editing) {
        await API.put(`/api/transactions/categories/${editing.id}/`, form);
        addToast('Category updated');
      } else {
        await API.post('/api/transactions/categories/', form);
        addToast('Category created');
      }
      setShowModal(false);
      loadCategories();
    } catch (err) {
      const data = err.response?.data;
      const msg = typeof data === 'object' ? Object.values(data).flat().join(', ') : 'Failed to save category';
      addToast(msg, 'error');
    }
  };

  const handleDelete = async (cat) => {
    if (cat.is_system) { addToast('System categories cannot be deleted', 'info'); return; }
    if (!window.confirm(`Delete "${cat.name}"? Transactions using it will become uncategorized.`)) return;
    try {
      await API.delete(`/api/transactions/categories/${cat.id}/`);
      addToast('Category deleted');
      loadCategories();
    } catch { addToast('Failed to delete category', 'error'); }
  };

  const filtered = filter === 'all' ? categories : categories.filter(c => c.category_type === filter);
  const expenseCount = categories.filter(c => c.category_type === 'expense').length;
  const incomeCount = categories.filter(c => c.category_type === 'income').length;

  return (
    <div>
      <div className="page-header">
        <h1>Categories</h1>
        <button className="btn btn-primary" onClick={openCreate}><Plus size={16} /> New Category</button>
      </div>

      {/* Filter Tabs */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 24 }}>
        {[
          { key: 'all', label: `All (${categories.length})` },
          { key: 'expense', label: `Expense (${expenseCount})` },
          { key: 'income', label: `Income (${incomeCount})` },
        ].map((tab) => (
          <button
            key={tab.key}
            className={`btn btn-sm ${filter === tab.key ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setFilter(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="loading-spinner"><div className="spinner" /></div>
      ) : filtered.length === 0 ? (
        <div className="empty-state">
          <Tag size={32} color="var(--gray-400)" />
          <h3>No categories found</h3>
          <p>Create custom categories to organize your transactions.</p>
          <button className="btn btn-primary" onClick={openCreate}><Plus size={16} /> New Category</button>
        </div>
      ) : (
        <div className="category-grid">
          {filtered.map((cat) => (
            <div className="card" key={cat.id} style={{ borderLeft: `4px solid ${cat.color || '#6366f1'}` }}>
              <div className="card-body" style={{ padding: 16, display: 'flex', alignItems: 'center', gap: 14 }}>
                <div style={{
                  width: 44, height: 44, borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 22, background: `${cat.color || '#6366f1'}15`,
                }}>
                  {cat.icon || '🏷️'}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600, fontSize: 15 }}>{cat.name}</div>
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginTop: 4 }}>
                    <span className={`badge-tag ${cat.category_type === 'income' ? 'badge-income' : 'badge-expense'}`} style={{ fontSize: 11 }}>
                      {cat.category_type}
                    </span>
                    {cat.is_system && (
                      <span className="badge-tag" style={{ fontSize: 11, background: 'var(--gray-100)', color: 'var(--gray-500)' }}>System</span>
                    )}
                  </div>
                  {cat.description && <div style={{ fontSize: 12, color: 'var(--gray-500)', marginTop: 4 }}>{cat.description}</div>}
                </div>
                {!cat.is_system && (
                  <div className="table-actions">
                    <button title="Edit" onClick={() => openEdit(cat)}><Pencil size={14} /></button>
                    <button title="Delete" className="delete" onClick={() => handleDelete(cat)}><Trash2 size={14} /></button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create / Edit Modal */}
      {showModal && (
        <Modal title={editing ? 'Edit Category' : 'New Category'} onClose={() => setShowModal(false)}>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Category Name</label>
              <input type="text" placeholder="e.g. Groceries, Freelance Income" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
            </div>
            <div className="form-group">
              <label>Type</label>
              <select value={form.category_type} onChange={(e) => setForm({ ...form, category_type: e.target.value })}>
                <option value="expense">Expense</option>
                <option value="income">Income</option>
              </select>
            </div>
            <div className="form-group">
              <label>Description (optional)</label>
              <input type="text" placeholder="Short description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
            </div>
            <div className="form-group">
              <label>Icon</label>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 4 }}>
                {PRESET_ICONS.map((icon) => (
                  <button
                    key={icon} type="button"
                    onClick={() => setForm({ ...form, icon })}
                    style={{
                      width: 40, height: 40, borderRadius: 8, border: form.icon === icon ? '2px solid var(--primary)' : '1px solid var(--gray-200)',
                      background: form.icon === icon ? 'var(--primary-light)' : '#fff', fontSize: 20, cursor: 'pointer',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                    }}
                  >
                    {icon}
                  </button>
                ))}
              </div>
            </div>
            <div className="form-group">
              <label>Color</label>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 4 }}>
                {PRESET_COLORS.map((c) => (
                  <button
                    key={c} type="button"
                    onClick={() => setForm({ ...form, color: c })}
                    style={{
                      width: 32, height: 32, borderRadius: '50%', border: form.color === c ? '3px solid var(--gray-800)' : '2px solid transparent',
                      background: c, cursor: 'pointer',
                    }}
                  />
                ))}
              </div>
            </div>
            <div className="modal-actions">
              <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
              <button type="submit" className="btn btn-primary">{editing ? 'Update' : 'Create'}</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
