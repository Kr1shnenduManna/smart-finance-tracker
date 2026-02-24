import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Bell, LogOut, ChevronDown } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Topbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef(null);

  const initials = user
    ? (user.first_name?.[0] || '') + (user.last_name?.[0] || user.username?.[0] || '')
    : '?';

  const handleLogout = async () => {
    setMenuOpen(false);
    await logout();
    navigate('/login');
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <header className="topbar">
      <div className="topbar-search">
        <Search size={16} />
        <input type="text" placeholder="Search transactions, bills, or insights..." />
      </div>

      <div className="topbar-links">
        <a href="/">Dashboard</a>
        <a href="/analytics">Reports</a>
      </div>

      <div className="topbar-right">
        <button className="notification-btn">
          <Bell size={18} />
          <span className="badge" />
        </button>

        <div className="user-menu" ref={menuRef}>
          <button className="user-menu-trigger" onClick={() => setMenuOpen(!menuOpen)}>
            <div className="user-avatar">{initials.toUpperCase()}</div>
            <span className="name">{user?.first_name || user?.username || 'User'}</span>
            <ChevronDown size={14} />
          </button>

          {menuOpen && (
            <div className="user-dropdown">
              <div className="user-dropdown-header">
                <div className="user-avatar">{initials.toUpperCase()}</div>
                <div>
                  <div className="name">{user?.first_name || user?.username}</div>
                  <div className="email">{user?.email || ''}</div>
                </div>
              </div>
              <hr />
              <button className="user-dropdown-item logout" onClick={handleLogout}>
                <LogOut size={16} />
                Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
