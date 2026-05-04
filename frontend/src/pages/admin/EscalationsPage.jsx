import React, { useEffect, useState } from 'react';

const API = 'http://localhost:8000/api/v1/admin';
function authHeaders() {
  return { Authorization: `Bearer ${localStorage.getItem('admin_token')}` };
}

export default function EscalationsPage() {
  const [escalations, setEscalations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API}/escalations`, { headers: authHeaders() })
      .then(r => r.json())
      .then(setEscalations)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="admin-loading">Loading escalations...</div>;

  return (
    <div className="data-table-wrapper">
      <div className="table-header">
        <h3>Escalations ({escalations.length})</h3>
      </div>
      {escalations.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">🚨</div>
          <p>No escalations found</p>
        </div>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>Ticket ID</th>
              <th>Customer</th>
              <th>Mobile</th>
              <th>Agent</th>
              <th>ETA</th>
              <th>Reason</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {escalations.map(e => (
              <tr key={e.ticket_id}>
                <td><strong>{e.ticket_id}</strong></td>
                <td>{e.customer_name || '—'}</td>
                <td>{e.mobile}</td>
                <td>{e.agent_name}</td>
                <td>{e.eta}</td>
                <td>{e.reason}</td>
                <td>{e.created_at ? new Date(e.created_at).toLocaleDateString() : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
