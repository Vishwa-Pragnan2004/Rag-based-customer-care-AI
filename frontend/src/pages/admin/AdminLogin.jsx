import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../../styles/admin.css';

const API = 'http://localhost:8000/api/v1/admin';

export default function AdminLogin() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await fetch(`${API}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      if (!res.ok) {
        const d = await res.json();
        throw new Error(d.detail || 'Login failed');
      }
      const data = await res.json();
      localStorage.setItem('admin_token', data.token);
      localStorage.setItem('admin_user', data.username);
      navigate('/admin/dashboard');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-brand">
          <div className="login-brand-icon">❄️</div>
          <h1>FrostGuard Admin</h1>
          <p>Sign in to manage your service operations</p>
        </div>
        {error && <div className="login-error">{error}</div>}
        <form className="login-form" onSubmit={handleLogin}>
          <div className="form-group">
            <label>Username</label>
            <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="Enter username" autoFocus required />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Enter password" required />
          </div>
          <button type="submit" className="login-btn" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
        <div className="login-footer">
          <a href="/">← Back to Chatbot</a>
        </div>
      </div>
    </div>
  );
}
