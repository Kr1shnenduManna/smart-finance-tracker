import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Wallet } from 'lucide-react';
import { register as registerApi } from '../api/endpoints';
import API from '../api/axios';

export default function Register() {
  const [form, setForm] = useState({ username: '', email: '', password: '', password2: '' });
  const [errors, setErrors] = useState({});
  const [generalError, setGeneralError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { fetchUser } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrors({});
    setGeneralError('');

    if (form.password !== form.password2) {
      setErrors({ password2: 'Passwords do not match' });
      return;
    }

    setLoading(true);
    try {
      // Fetch CSRF cookie first
      await API.get('/api-auth/login/');

      await registerApi({
        username: form.username,
        email: form.email,
        password: form.password,
        password2: form.password2,
      });

      // The register endpoint auto-logs the user in
      await fetchUser();
      navigate('/');
    } catch (err) {
      const data = err.response?.data;
      if (data && typeof data === 'object' && !data.detail) {
        // Field-level errors
        setErrors(data);
      } else {
        setGeneralError(data?.detail || 'Registration failed. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const fieldError = (field) =>
    errors[field] ? (
      <div className="error">{Array.isArray(errors[field]) ? errors[field][0] : errors[field]}</div>
    ) : null;

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="logo">
          <div className="logo-icon"><Wallet size={22} /></div>
          <div>
            <h1 style={{ fontSize: 18, marginBottom: 0 }}>FinanceTracker</h1>
          </div>
        </div>

        <h1>Create account</h1>
        <p className="subtitle">Get started with Smart Finance Tracker</p>

        {generalError && (
          <div style={{ background: 'var(--danger-light)', color: 'var(--danger)', padding: '10px 14px', borderRadius: 8, fontSize: 13, marginBottom: 20 }}>
            {generalError}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Username</label>
            <input type="text" placeholder="Choose a username" value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} required />
            {fieldError('username')}
          </div>
          <div className="form-group">
            <label>Email</label>
            <input type="email" placeholder="you@example.com" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
            {fieldError('email')}
          </div>
          <div className="form-group">
            <label>Password</label>
            <input type="password" placeholder="Create a password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
            {fieldError('password')}
          </div>
          <div className="form-group">
            <label>Confirm Password</label>
            <input type="password" placeholder="Confirm your password" value={form.password2} onChange={(e) => setForm({ ...form, password2: e.target.value })} required />
            {fieldError('password2')}
          </div>
          <button type="submit" className="btn btn-primary btn-full" disabled={loading} style={{ marginTop: 8 }}>
            {loading ? 'Creating...' : 'Create Account'}
          </button>
        </form>

        <p style={{ textAlign: 'center', marginTop: 24, fontSize: 13, color: 'var(--gray-500)' }}>
          Already have an account? <Link to="/login" style={{ color: 'var(--primary)', fontWeight: 600 }}>Sign in</Link>
        </p>
      </div>
    </div>
  );
}
