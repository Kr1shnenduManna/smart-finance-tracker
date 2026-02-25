import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { updateProfile } from '../api/endpoints';
import { Mail, Phone, User, Calendar, Pencil, X, Check } from 'lucide-react';

export default function Profile() {
  const { user, fetchUser } = useAuth();
  const { addToast } = useToast();
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({});
  const [errors, setErrors] = useState({});

  const initials = user
    ? (user.first_name?.[0] || '') + (user.last_name?.[0] || user.username?.[0] || '')
    : '?';

  const startEditing = () => {
    setForm({
      first_name: user?.first_name || '',
      last_name: user?.last_name || '',
      email: user?.email || '',
      phone: user?.phone || '',
    });
    setErrors({});
    setEditing(true);
  };

  const cancelEditing = () => {
    setEditing(false);
    setErrors({});
  };

  const handleSave = async () => {
    setSaving(true);
    setErrors({});
    try {
      await updateProfile(form);
      await fetchUser();
      setEditing(false);
      addToast('Profile updated successfully', 'success');
    } catch (err) {
      const data = err.response?.data;
      if (data && typeof data === 'object') {
        setErrors(data);
      }
      addToast('Failed to update profile', 'error');
    } finally {
      setSaving(false);
    }
  };

  const fieldError = (field) =>
    errors[field] ? (
      <div style={{ color: 'var(--danger)', fontSize: 12, marginTop: 4 }}>
        {Array.isArray(errors[field]) ? errors[field][0] : errors[field]}
      </div>
    ) : null;

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>Profile</h1>
        {!editing ? (
          <button className="btn btn-primary" onClick={startEditing}>
            <Pencil size={16} /> Edit Profile
          </button>
        ) : (
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-secondary" onClick={cancelEditing} disabled={saving}>
              <X size={16} /> Cancel
            </button>
            <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
              <Check size={16} /> {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        )}
      </div>

      <div className="profile-grid">
        {/* Left: Avatar Section */}
        <div className="card">
          <div className="profile-avatar-section">
            <div className="avatar-large">{initials.toUpperCase()}</div>
            <div className="name">
              {editing
                ? `${form.first_name || ''} ${form.last_name || ''}`.trim() || user?.username
                : `${user?.first_name || ''} ${user?.last_name || ''}`.trim() || user?.username}
            </div>
            <div className="email">@{user?.username}</div>
          </div>
        </div>

        {/* Right: Details */}
        <div className="card">
          <div className="card-header"><h3>Account Details</h3></div>
          <div className="card-body">
            <div style={{ display: 'grid', gap: 20 }}>
              <DetailRow icon={<User size={16} />} label="Username" value={user?.username || '—'} />

              {editing ? (
                <EditRow icon={<Mail size={16} />} label="Email" value={form.email}
                  onChange={(v) => setForm({ ...form, email: v })} error={fieldError('email')} type="email" />
              ) : (
                <DetailRow icon={<Mail size={16} />} label="Email" value={user?.email || '—'} />
              )}

              {editing ? (
                <EditRow icon={<User size={16} />} label="First Name" value={form.first_name}
                  onChange={(v) => setForm({ ...form, first_name: v })} error={fieldError('first_name')} />
              ) : (
                <DetailRow icon={<User size={16} />} label="First Name" value={user?.first_name || '—'} />
              )}

              {editing ? (
                <EditRow icon={<User size={16} />} label="Last Name" value={form.last_name}
                  onChange={(v) => setForm({ ...form, last_name: v })} error={fieldError('last_name')} />
              ) : (
                <DetailRow icon={<User size={16} />} label="Last Name" value={user?.last_name || '—'} />
              )}

              {editing ? (
                <EditRow icon={<Phone size={16} />} label="Phone" value={form.phone}
                  onChange={(v) => setForm({ ...form, phone: v })} error={fieldError('phone')} type="tel" />
              ) : (
                <DetailRow icon={<Phone size={16} />} label="Phone" value={user?.phone || 'Not set'} />
              )}

              <DetailRow icon={<Calendar size={16} />} label="Joined" value={user?.created_at ? new Date(user.created_at).toLocaleDateString() : '—'} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function DetailRow({ icon, label, value }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '12px 0', borderBottom: '1px solid var(--gray-100)' }}>
      <div style={{ color: 'var(--gray-400)' }}>{icon}</div>
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 12, color: 'var(--gray-500)', marginBottom: 2 }}>{label}</div>
        <div style={{ fontSize: 14, fontWeight: 500, color: 'var(--gray-800)' }}>{value}</div>
      </div>
    </div>
  );
}

function EditRow({ icon, label, value, onChange, error, type = 'text' }) {
  return (
    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 14, padding: '12px 0', borderBottom: '1px solid var(--gray-100)' }}>
      <div style={{ color: 'var(--gray-400)', marginTop: 10 }}>{icon}</div>
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 12, color: 'var(--gray-500)', marginBottom: 4 }}>{label}</div>
        <input
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          style={{
            width: '100%',
            padding: '8px 12px',
            border: '1px solid var(--gray-300)',
            borderRadius: 8,
            fontSize: 14,
            background: '#fff',
            transition: 'border-color .2s, box-shadow .2s',
          }}
          onFocus={(e) => {
            e.target.style.borderColor = 'var(--primary)';
            e.target.style.boxShadow = '0 0 0 3px rgba(79,70,229,.1)';
          }}
          onBlur={(e) => {
            e.target.style.borderColor = 'var(--gray-300)';
            e.target.style.boxShadow = 'none';
          }}
        />
        {error}
      </div>
    </div>
  );
}
