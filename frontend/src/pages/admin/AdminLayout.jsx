import React, { useEffect } from 'react';
import { Outlet, useNavigate, useLocation, Link } from 'react-router-dom';
import '../../styles/admin.css';

const NAV_ITEMS = [
  { path: '/admin/dashboard', icon: '📊', label: 'Dashboard' },
  { path: '/admin/customers', icon: '👥', label: 'Customers' },
  { path: '/admin/appointments', icon: '📋', label: 'Appointments' },
  { path: '/admin/escalations', icon: '🚨', label: 'Escalations' },
  { path: '/admin/db', icon: '🗄️', label: 'DB Viewer' },
];

export default function AdminLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const token = localStorage.getItem('admin_token');
  const adminUser = localStorage.getItem('admin_user') || 'Admin';

  useEffect(() => {
    if (!token) navigate('/admin');
  }, [token, navigate]);

  const handleLogout = () => {
    localStorage.removeItem('admin_token');
    localStorage.removeItem('admin_user');
    navigate('/admin');
  };

  const pageTitle = NAV_ITEMS.find(n => location.pathname.startsWith(n.path))?.label || 'Admin';

  return (
    <div className="admin-layout">
      <aside className="admin-sidebar">
        <div className="sidebar-brand">
          <div className="sidebar-brand-icon">❄️</div>
          <div className="sidebar-brand-text">
            <h2>FrostGuard</h2>
            <span>Admin Panel</span>
          </div>
        </div>
        <nav className="sidebar-nav">
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`sidebar-link ${location.pathname.startsWith(item.path) ? 'active' : ''}`}
            >
              <span className="sidebar-link-icon">{item.icon}</span>
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="sidebar-footer">
          <Link to="/" className="sidebar-link">
            <span className="sidebar-link-icon">💬</span>
            Open Chatbot
          </Link>
          <button className="sidebar-logout" onClick={handleLogout}>
            <span className="sidebar-link-icon">🚪</span>
            Sign Out
          </button>
        </div>
      </aside>
      <div className="admin-main">
        <div className="admin-topbar">
          <h1>{pageTitle}</h1>
          <span className="admin-topbar-meta">Logged in as <strong>{adminUser}</strong></span>
        </div>
        <div className="admin-content">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
