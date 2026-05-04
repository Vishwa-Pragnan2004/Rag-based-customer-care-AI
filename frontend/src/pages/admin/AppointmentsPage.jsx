import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

const API = 'http://localhost:8000/api/v1/admin';
const STATUSES = ['all', 'requested', 'booked', 'technician_assigned', 'in_progress', 'completed', 'scheduled'];

function authHeaders() {
  return { Authorization: `Bearer ${localStorage.getItem('admin_token')}` };
}

export default function AppointmentsPage() {
  const [appointments, setAppointments] = useState([]);
  const [filter, setFilter] = useState('all');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const fetchData = () => {
    setLoading(true);
    const url = filter === 'all' ? `${API}/appointments` : `${API}/appointments?status=${filter}`;
    fetch(url, { headers: authHeaders() })
      .then(r => r.json())
      .then(setAppointments)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(); }, [filter]);

  const filtered = appointments.filter(a =>
    (a.ticket_id || '').toLowerCase().includes(search.toLowerCase()) ||
    (a.customer_name || '').toLowerCase().includes(search.toLowerCase()) ||
    (a.mobile || '').includes(search)
  );

  return (
    <>
      <div className="data-table-wrapper">
        <div className="table-header">
          <h3>Appointments ({filtered.length})</h3>
          <div className="table-controls">
            <input className="table-search" placeholder="Search ticket, name, mobile..." value={search} onChange={e => setSearch(e.target.value)} />
            {STATUSES.map(s => (
              <button key={s} className={`filter-btn ${filter === s ? 'active' : ''}`} onClick={() => setFilter(s)}>
                {s === 'all' ? 'All' : s.replace('_', ' ')}
              </button>
            ))}
          </div>
        </div>
        {loading ? (
          <div className="admin-loading">Loading...</div>
        ) : filtered.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">📋</div>
            <p>No appointments found</p>
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Ticket ID</th>
                <th>Customer</th>
                <th>Mobile</th>
                <th>Service</th>
                <th>Scheduled</th>
                <th>Technician</th>
                <th>Status</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(a => (
                <tr key={a.ticket_id} className="clickable-row" onClick={() => navigate(`/admin/appointments/${a.ticket_id}`)}>
                  <td><strong>{a.ticket_id}</strong></td>
                  <td>{a.customer_name || '—'}</td>
                  <td>{a.mobile}</td>
                  <td style={{textTransform:'capitalize'}}>{a.service_type}</td>
                  <td>{a.scheduled_date || '—'}</td>
                  <td>{a.technician || '—'}</td>
                  <td><span className={`status-badge status-${a.status}`}>{(a.status || '').replace('_', ' ')}</span></td>
                  <td>{a.created_at ? new Date(a.created_at).toLocaleDateString() : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}
