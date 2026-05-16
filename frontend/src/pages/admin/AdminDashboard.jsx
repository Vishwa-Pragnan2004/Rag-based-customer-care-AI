import React, { useEffect, useState } from 'react';

const API = 'http://localhost:8000/api/v1/admin';

function authHeaders() {
  return { Authorization: `Bearer ${localStorage.getItem('admin_token')}`, 'Content-Type': 'application/json' };
}

export default function AdminDashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API}/dashboard`, { headers: authHeaders() })
      .then(r => r.json())
      .then(setStats)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="admin-loading">Loading dashboard...</div>;
  if (!stats) return <div className="admin-loading">Failed to load dashboard data.</div>;

  const cards = [
    { icon: '👥', value: stats.total_customers, label: 'Total Customers', color: 'purple' },
    { icon: '📋', value: stats.total_appointments, label: 'Total Appointments', color: 'blue' },
    { icon: '⚡', value: stats.active_appointments, label: 'Active Tickets', color: 'amber' },
    { icon: '✅', value: stats.completed_appointments, label: 'Completed', color: 'teal' },
    { icon: '🚨', value: stats.total_escalations, label: 'Escalations', color: 'rose' },
  ];

  return (
    <>
      <div className="stats-grid">
        {cards.map((c, i) => (
          <div key={i} className={`stat-card ${c.color}`}>
            <div className="stat-card-icon">{c.icon}</div>
            <div className="stat-card-value">{c.value}</div>
            <div className="stat-card-label">{c.label}</div>
          </div>
        ))}
      </div>

      <div className="data-table-wrapper">
        <div className="table-header">
          <h3>Status Breakdown</h3>
        </div>
        <div className="data-table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                <th>Status</th>
                <th>Count</th>
                <th>Percentage</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(stats.status_breakdown || {})
                .filter(([status]) => status !== 'technician_assigned')
                .map(([status, count]) => (
                <tr key={status}>
                  <td><span className={`status-badge status-${status}`}>{status.replace('_', ' ')}</span></td>
                  <td>{count}</td>
                  <td>{stats.total_appointments ? ((count / stats.total_appointments) * 100).toFixed(1) + '%' : '0%'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
