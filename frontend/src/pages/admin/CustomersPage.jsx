import React, { useEffect, useState } from 'react';

const API = 'http://localhost:8000/api/v1/admin';
function authHeaders() {
  return { Authorization: `Bearer ${localStorage.getItem('admin_token')}` };
}

export default function CustomersPage() {
  const [customers, setCustomers] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API}/customers`, { headers: authHeaders() })
      .then(r => r.json())
      .then(setCustomers)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const filtered = customers.filter(c =>
    (c.name || '').toLowerCase().includes(search.toLowerCase()) ||
    (c.mobile || '').includes(search)
  );

  if (loading) return <div className="admin-loading">Loading customers...</div>;

  return (
    <div className="data-table-wrapper">
      <div className="table-header">
        <h3>Registered Customers ({filtered.length})</h3>
        <div className="table-controls">
          <input className="table-search" placeholder="Search by name or mobile..." value={search} onChange={e => setSearch(e.target.value)} />
        </div>
      </div>
      {filtered.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">👥</div>
          <p>No customers found</p>
        </div>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Mobile</th>
              <th>Address</th>
              <th>Pincode</th>
              <th>Appointments</th>
              <th>Registered</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(c => (
              <tr key={c.mobile}>
                <td><strong>{c.name || '—'}</strong></td>
                <td>{c.mobile}</td>
                <td>{c.address || '—'}</td>
                <td>{c.pincode || '—'}</td>
                <td>{c.appointment_count}</td>
                <td>{c.created_at ? new Date(c.created_at).toLocaleDateString() : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
