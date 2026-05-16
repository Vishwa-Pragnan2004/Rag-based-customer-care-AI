import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

const API = 'http://localhost:8000/api/v1/admin';
const PIPELINE = ['requested', 'booked', 'in_progress', 'completed'];
const PIPELINE_LABELS = { requested: 'Requested', booked: 'Booked', in_progress: 'In Progress', completed: 'Completed' };
const TECHS = ['Rajesh', 'Amit', 'Vikram', 'Suresh'];

function authHeaders() {
  return { Authorization: `Bearer ${localStorage.getItem('admin_token')}`, 'Content-Type': 'application/json' };
}

export default function AppointmentDetail() {
  const { ticketId } = useParams();
  const navigate = useNavigate();
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [form, setForm] = useState({ status: '', technician: '', arrival_date: '', notes: '' });
  const [msg, setMsg] = useState('');

  const fetchDetail = () => {
    setLoading(true);
    fetch(`${API}/appointments/${ticketId}`, { headers: authHeaders() })
      .then(r => r.json())
      .then(d => {
        setDetail(d);
        // Format arrival_date for datetime-local input (needs YYYY-MM-DDTHH:MM format)
        let arrivalForInput = '';
        if (d.arrival_date) {
          try {
            const dt = new Date(d.arrival_date);
            if (!isNaN(dt.getTime())) {
              arrivalForInput = dt.toISOString().slice(0, 16);
            }
          } catch (e) {
            arrivalForInput = d.arrival_date;
          }
        }
        setForm({
          status: d.status || '',
          technician: d.technician || '',
          arrival_date: arrivalForInput,
          notes: d.notes || ''
        });
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchDetail(); }, [ticketId]);

  const handleUpdate = async () => {
    setUpdating(true);
    setMsg('');
    try {
      const res = await fetch(`${API}/appointments/${ticketId}/status`, {
        method: 'PUT',
        headers: authHeaders(),
        body: JSON.stringify(form),
      });
      if (!res.ok) {
        const d = await res.json();
        throw new Error(d.detail || 'Update failed');
      }
      setMsg('✅ Updated successfully');
      fetchDetail();
    } catch (e) {
      setMsg('❌ ' + e.message);
    } finally {
      setUpdating(false);
    }
  };

  if (loading) return <div className="admin-loading">Loading appointment...</div>;
  if (!detail) return <div className="admin-loading">Appointment not found.</div>;

  // Map legacy statuses to pipeline
  let displayStatus = detail.status;
  if (displayStatus === 'scheduled') displayStatus = 'booked';
  if (displayStatus === 'technician_assigned') displayStatus = 'booked';
  const currentIdx = PIPELINE.indexOf(displayStatus);

  return (
    <>
      <button className="back-btn" onClick={() => navigate('/admin/appointments')}>← Back to Appointments</button>

      {/* Status Pipeline */}
      <div className="detail-card">
        <h3>📊 Status Pipeline</h3>
        <div className="status-pipeline">
          {PIPELINE.map((step, i) => (
            <React.Fragment key={step}>
              {i > 0 && <div className={`pipeline-line ${i <= currentIdx ? 'done' : ''}`} />}
              <div className={`pipeline-step ${i < currentIdx ? 'done' : i === currentIdx ? 'current' : ''}`}>
                <div className="pipeline-dot">
                  {i < currentIdx ? '✓' : i === currentIdx ? '●' : (i + 1)}
                </div>
                <span className="pipeline-label">{PIPELINE_LABELS[step]}</span>
              </div>
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Details */}
      <div className="detail-card">
        <h3>📋 Appointment Details</h3>
        <div className="detail-grid">
          <div className="detail-item"><label>Ticket ID</label><span>{detail.ticket_id}</span></div>
          <div className="detail-item"><label>Customer</label><span>{detail.customer_name || '—'}</span></div>
          <div className="detail-item"><label>Mobile</label><span>{detail.mobile}</span></div>
          <div className="detail-item"><label>Service</label><span style={{textTransform:'capitalize'}}>{detail.service_type}</span></div>
          <div className="detail-item"><label>Scheduled Date</label><span>{detail.scheduled_date || '—'}</span></div>
          <div className="detail-item"><label>Technician</label><span>{detail.technician || '—'}</span></div>
          <div className="detail-item"><label>Arrival Date</label><span>{detail.arrival_date || '—'}</span></div>
          <div className="detail-item"><label>Address</label><span>{detail.address || '—'}</span></div>
          <div className="detail-item"><label>Pincode</label><span>{detail.pincode || '—'}</span></div>
          <div className="detail-item"><label>Notes</label><span>{detail.notes || '—'}</span></div>
        </div>
      </div>

      {/* Update Form */}
      <div className="update-form">
        <h3>🔄 Update Status</h3>
        <div className="form-grid">
          <div className="form-group">
            <label>Status</label>
            <select value={form.status} onChange={e => setForm({...form, status: e.target.value})}>
              {PIPELINE.map(s => <option key={s} value={s}>{PIPELINE_LABELS[s]}</option>)}
              {/* Include current status if it's legacy */}
              {!PIPELINE.includes(form.status) && form.status && (
                <option value={form.status}>{form.status}</option>
              )}
            </select>
          </div>
          <div className="form-group">
            <label>Technician</label>
            <select value={form.technician} onChange={e => setForm({...form, technician: e.target.value})}>
              <option value="">Select technician</option>
              {TECHS.map(t => <option key={t} value={t}>{t}</option>)}
              {/* Include current tech if not in list */}
              {form.technician && !TECHS.includes(form.technician) && (
                <option value={form.technician}>{form.technician}</option>
              )}
            </select>
          </div>
          <div className="form-group">
            <label>Arrival Date</label>
            <input
              type="date"
              value={form.arrival_date ? form.arrival_date.slice(0, 10) : ''}
              onChange={e => setForm({...form, arrival_date: e.target.value})}
            />
          </div>
        </div>
        <div className="form-group">
          <label>Notes</label>
          <textarea value={form.notes} onChange={e => setForm({...form, notes: e.target.value})} placeholder="Add notes about this appointment..." />
        </div>
        {msg && <p style={{margin: '12px 0', fontSize: '0.9rem'}}>{msg}</p>}
        <div className="btn-row">
          <button className="btn-primary" onClick={handleUpdate} disabled={updating}>
            {updating ? 'Updating...' : 'Update Appointment'}
          </button>
          <button className="btn-secondary" onClick={() => navigate('/admin/appointments')}>Cancel</button>
        </div>
      </div>
    </>
  );
}
