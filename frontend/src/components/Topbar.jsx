import { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Bell, LogOut, ChevronDown, Check, CheckCheck, AlertTriangle, CreditCard, Clock } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { getUnreadNotifications, getBillNotifications, markNotificationRead, markAllNotificationsRead } from '../api/endpoints';

export default function Topbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const menuRef = useRef(null);
  const notifRef = useRef(null);

  const initials = user
    ? (user.first_name?.[0] || '') + (user.last_name?.[0] || user.username?.[0] || '')
    : '?';

  // Fetch unread count on mount and periodically
  const fetchUnreadCount = useCallback(async () => {
    try {
      const res = await getUnreadNotifications();
      const data = Array.isArray(res.data) ? res.data : (res.data?.results || []);
      setUnreadCount(data.length);
    } catch (err) {
      // silently fail
    }
  }, []);

  useEffect(() => {
    fetchUnreadCount();
    const interval = setInterval(fetchUnreadCount, 30000); // poll every 30s
    return () => clearInterval(interval);
  }, [fetchUnreadCount]);

  // Fetch all notifications when dropdown opens
  const handleBellClick = async () => {
    const opening = !notifOpen;
    setNotifOpen(opening);
    setMenuOpen(false);
    if (opening) {
      setLoading(true);
      try {
        const res = await getBillNotifications();
        const data = Array.isArray(res.data) ? res.data : (res.data?.results || []);
        setNotifications(data);
      } catch (err) {
        setNotifications([]);
      } finally {
        setLoading(false);
      }
    }
  };

  const handleMarkRead = async (id) => {
    try {
      await markNotificationRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
      setUnreadCount((prev) => Math.max(0, prev - 1));
    } catch {
      // silently fail
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await markAllNotificationsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch {
      // silently fail
    }
  };

  const handleLogout = async () => {
    setMenuOpen(false);
    await logout();
    navigate('/login');
  };

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setMenuOpen(false);
      }
      if (notifRef.current && !notifRef.current.contains(e.target)) {
        setNotifOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const getNotifIcon = (type) => {
    switch (type) {
      case 'overdue': return <AlertTriangle size={16} className="notif-icon overdue" />;
      case 'paid': return <CreditCard size={16} className="notif-icon paid" />;
      case 'due_soon': return <Clock size={16} className="notif-icon due-soon" />;
      default: return <Bell size={16} className="notif-icon" />;
    }
  };

  const getNotifMessage = (n) => {
    switch (n.notification_type) {
      case 'overdue': return `"${n.bill_name}" is overdue`;
      case 'paid': return `"${n.bill_name}" has been paid`;
      case 'due_soon': return `"${n.bill_name}" is due soon`;
      default: return `Notification for "${n.bill_name}"`;
    }
  };

  const timeAgo = (dateStr) => {
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'Just now';
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    const days = Math.floor(hrs / 24);
    if (days < 7) return `${days}d ago`;
    return new Date(dateStr).toLocaleDateString();
  };

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
        <div className="notification-wrapper" ref={notifRef}>
          <button className="notification-btn" onClick={handleBellClick} title="Notifications">
            <Bell size={18} />
            {unreadCount > 0 && (
              <span className="badge">{unreadCount > 9 ? '9+' : unreadCount}</span>
            )}
          </button>

          {notifOpen && (
            <div className="notification-dropdown">
              <div className="notif-header">
                <h4>Notifications</h4>
                {unreadCount > 0 && (
                  <button className="notif-mark-all" onClick={handleMarkAllRead}>
                    <CheckCheck size={14} />
                    Mark all read
                  </button>
                )}
              </div>

              <div className="notif-list">
                {loading ? (
                  <div className="notif-empty">Loading...</div>
                ) : notifications.length === 0 ? (
                  <div className="notif-empty">
                    <Bell size={32} />
                    <p>No notifications yet</p>
                  </div>
                ) : (
                  notifications.map((n) => (
                    <div
                      key={n.id}
                      className={`notif-item${n.is_read ? '' : ' unread'}`}
                      onClick={() => !n.is_read && handleMarkRead(n.id)}
                    >
                      <div className="notif-item-icon">{getNotifIcon(n.notification_type)}</div>
                      <div className="notif-item-content">
                        <p className="notif-item-message">{getNotifMessage(n)}</p>
                        {n.bill_amount && (
                          <span className="notif-item-amount">
                            Amount: {Number(n.bill_amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                          </span>
                        )}
                        <span className="notif-item-time">{timeAgo(n.created_at)}</span>
                      </div>
                      {!n.is_read && (
                        <button
                          className="notif-item-read-btn"
                          title="Mark as read"
                          onClick={(e) => { e.stopPropagation(); handleMarkRead(n.id); }}
                        >
                          <Check size={14} />
                        </button>
                      )}
                    </div>
                  ))
                )}
              </div>

              {notifications.length > 0 && (
                <div className="notif-footer">
                  <button onClick={() => { setNotifOpen(false); navigate('/bills'); }}>
                    View all bills
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

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
