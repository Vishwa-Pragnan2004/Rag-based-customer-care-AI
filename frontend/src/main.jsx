import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import App from './App.jsx'
import AdminLogin from './pages/admin/AdminLogin.jsx'
import AdminLayout from './pages/admin/AdminLayout.jsx'
import AdminDashboard from './pages/admin/AdminDashboard.jsx'
import CustomersPage from './pages/admin/CustomersPage.jsx'
import AppointmentsPage from './pages/admin/AppointmentsPage.jsx'
import AppointmentDetail from './pages/admin/AppointmentDetail.jsx'
import EscalationsPage from './pages/admin/EscalationsPage.jsx'
import DbViewerPage from './pages/admin/DbViewerPage.jsx'
import './index.css'

// Global fetch patch for Vercel deployment: redirect http://localhost:8000 requests to same-domain in production
const originalFetch = window.fetch;
window.fetch = function (url, options) {
  let targetUrl = url;
  if (typeof targetUrl === 'string' && targetUrl.startsWith('http://localhost:8000')) {
    if (window.location.hostname !== 'localhost') {
      targetUrl = targetUrl.replace('http://localhost:8000', window.location.origin + '/_/backend');
    }
  }
  return originalFetch(targetUrl, options);
};

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        {/* User Chatbot */}
        <Route path="/" element={<App />} />

        {/* Admin */}
        <Route path="/admin" element={<AdminLogin />} />
        <Route path="/admin" element={<AdminLayout />}>
          <Route path="dashboard" element={<AdminDashboard />} />
          <Route path="customers" element={<CustomersPage />} />
          <Route path="appointments" element={<AppointmentsPage />} />
          <Route path="appointments/:ticketId" element={<AppointmentDetail />} />
          <Route path="escalations" element={<EscalationsPage />} />
          <Route path="db" element={<DbViewerPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
)
