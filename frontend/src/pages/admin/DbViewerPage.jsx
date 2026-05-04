import React, { useEffect, useState } from 'react';

const API = 'http://localhost:8000/api/v1/admin';
function authHeaders() {
  return { Authorization: `Bearer ${localStorage.getItem('admin_token')}` };
}

export default function DbViewerPage() {
  const [tables, setTables] = useState([]);
  const [selected, setSelected] = useState(null);
  const [tableData, setTableData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API}/db/tables`, { headers: authHeaders() })
      .then(r => r.json())
      .then(setTables)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const loadTable = (name) => {
    setSelected(name);
    setTableData(null);
    fetch(`${API}/db/${name}`, { headers: authHeaders() })
      .then(r => r.json())
      .then(setTableData)
      .catch(console.error);
  };

  if (loading) return <div className="admin-loading">Loading DB info...</div>;

  return (
    <>
      {/* Table list */}
      <div className="stats-grid" style={{marginBottom: 24}}>
        {tables.map(t => (
          <div
            key={t.name}
            className={`stat-card purple`}
            style={{cursor: 'pointer', border: selected === t.name ? '1px solid rgba(124,106,247,0.5)' : undefined}}
            onClick={() => loadTable(t.name)}
          >
            <div className="stat-card-icon">🗄️</div>
            <div className="stat-card-value">{t.row_count}</div>
            <div className="stat-card-label">{t.name}</div>
            <div style={{marginTop: 8, fontSize: '0.7rem', color: 'rgba(255,255,255,0.3)'}}>
              {t.columns.map(c => c.name).join(', ')}
            </div>
          </div>
        ))}
      </div>

      {/* Table data */}
      {tableData && (
        <div className="data-table-wrapper">
          <div className="table-header">
            <h3>{tableData.table} ({tableData.total} rows)</h3>
          </div>
          {tableData.rows.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">📭</div>
              <p>Table is empty</p>
            </div>
          ) : (
            <div style={{overflowX: 'auto'}}>
              <table className="data-table">
                <thead>
                  <tr>
                    {tableData.columns.map(c => <th key={c}>{c}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {tableData.rows.map((row, i) => (
                    <tr key={i}>
                      {tableData.columns.map(c => (
                        <td key={c}>{row[c] != null ? String(row[c]) : '—'}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </>
  );
}
