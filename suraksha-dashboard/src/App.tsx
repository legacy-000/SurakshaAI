import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import { useLanguage } from './context/LanguageContext';
import { Sidebar } from './components/Sidebar';
import { LoginPage } from './pages/LoginPage';
import { LandingPage } from './pages/LandingPage';
import { DashboardPage } from './pages/DashboardPage';
import { ChatPage } from './pages/ChatPage';
import { NetworkPage } from './pages/NetworkPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { OffenderPage } from './pages/OffenderPage';
import { ForecastPage } from './pages/ForecastPage';
import { AlertsPage } from './pages/AlertsPage';
import { WorkspacePage } from './pages/WorkspacePage';
import { getRoleConfig } from './config/roles';
import './App.css';

const ProtectedRoute = ({ children, roles }: { children: React.ReactNode; roles?: string[] }) => {
  const { isAuthenticated, user } = useAuth();
  const { lang } = useLanguage();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (roles && user && !roles.includes(user.role_name)) {
    return <Navigate to="/" replace />;
  }
  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">
        {lang === 'kn' && (
          <div style={{ position: 'fixed', top: 12, right: 12, zIndex: 1000, background: 'var(--primary)', color: '#fff', fontSize: 11, padding: '4px 10px', borderRadius: 12, fontWeight: 600, letterSpacing: '0.05em' }}>
            ಕನ್ನಡ
          </div>
        )}
        {children}
      </main>
    </div>
  );
};

function App() {
  const { isAuthenticated } = useAuth();

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />} />
        <Route path="/landing" element={<LandingPage />} />
        <Route path="/" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
        <Route path="/chat" element={<ProtectedRoute roles={['Investigator', 'Analyst', 'Supervisor', 'System Administrator']}><ChatPage /></ProtectedRoute>} />
        <Route path="/network" element={<ProtectedRoute roles={['Investigator', 'Analyst', 'Supervisor', 'System Administrator']}><NetworkPage /></ProtectedRoute>} />
        <Route path="/analytics" element={<ProtectedRoute roles={['Analyst', 'Supervisor', 'Policymaker', 'System Administrator']}><AnalyticsPage /></ProtectedRoute>} />
        <Route path="/offender" element={<ProtectedRoute roles={['Investigator', 'Supervisor', 'System Administrator']}><OffenderPage /></ProtectedRoute>} />
        <Route path="/forecast" element={<ProtectedRoute roles={['Analyst', 'Supervisor', 'Policymaker', 'System Administrator']}><ForecastPage /></ProtectedRoute>} />
        <Route path="/alerts" element={<ProtectedRoute roles={['Investigator', 'Supervisor', 'Policymaker', 'System Administrator']}><AlertsPage /></ProtectedRoute>} />
        <Route path="/workspace" element={<ProtectedRoute roles={['Investigator', 'Supervisor', 'System Administrator']}><WorkspacePage /></ProtectedRoute>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
