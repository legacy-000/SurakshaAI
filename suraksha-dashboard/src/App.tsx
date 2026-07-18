import React from 'react';
import { HashRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import { useLanguage } from './context/LanguageContext';
import { Sidebar } from './components/Sidebar';
import { ErrorBoundary } from './components/ErrorBoundary';
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
import { CaseRegistrationPage } from './pages/CaseRegistrationPage';
import { SearchPage } from './pages/SearchPage';
import { ChargesheetPage } from './pages/ChargesheetPage';
import { CommandCenterPage } from './pages/CommandCenterPage';
import { SimilarityPage } from './pages/SimilarityPage';
import { AgentWorkbenchPage } from './pages/AgentWorkbenchPage';
import DatabaseModePage from './pages/DatabaseModePage';
import { InboxPage } from './pages/InboxPage';
import { AccessControlPage } from './pages/AccessControlPage';
import { CoordinationPage } from './pages/CoordinationPage';
import { GroupManagerPage } from './pages/GroupManagerPage';
import { AuditLogPage } from './pages/AuditLogPage';
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
    <HashRouter>
      <ErrorBoundary><Routes>
        <Route path="/login" element={isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />} />
        <Route path="/landing" element={<LandingPage />} />
        <Route path="/" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
        <Route path="/chat" element={<ProtectedRoute roles={['Investigator', 'Analyst', 'Supervisor', 'System Administrator']}><ChatPage /></ProtectedRoute>} />
        <Route path="/network" element={<ProtectedRoute roles={['Investigator', 'Analyst', 'Supervisor', 'System Administrator']}><NetworkPage /></ProtectedRoute>} />
        <Route path="/analytics" element={<ProtectedRoute roles={['Analyst', 'Supervisor', 'Policymaker', 'System Administrator']}><AnalyticsPage /></ProtectedRoute>} />
        <Route path="/offender" element={<ProtectedRoute roles={['Investigator', 'Supervisor', 'System Administrator']}><OffenderPage /></ProtectedRoute>} />
        <Route path="/forecast" element={<ProtectedRoute roles={['Analyst', 'Supervisor', 'Policymaker', 'System Administrator']}><ForecastPage /></ProtectedRoute>} />
        <Route path="/alerts" element={<ProtectedRoute roles={['Investigator', 'Supervisor', 'Policymaker', 'System Administrator']}><AlertsPage /></ProtectedRoute>} />
        <Route path="/database" element={<ProtectedRoute roles={['Investigator', 'Analyst', 'Supervisor', 'System Administrator']}><DatabaseModePage /></ProtectedRoute>} />
        <Route path="/workspace" element={<ProtectedRoute roles={['Investigator', 'Supervisor', 'System Administrator']}><WorkspacePage /></ProtectedRoute>} />
        <Route path="/registration" element={<ProtectedRoute roles={['Investigator', 'Supervisor', 'System Administrator']}><CaseRegistrationPage /></ProtectedRoute>} />
        <Route path="/search" element={<ProtectedRoute roles={['Investigator', 'Analyst', 'Supervisor', 'Policymaker', 'System Administrator']}><SearchPage /></ProtectedRoute>} />
        <Route path="/chargesheet" element={<ProtectedRoute roles={['Investigator', 'Supervisor', 'System Administrator']}><ChargesheetPage /></ProtectedRoute>} />
        <Route path="/command-center" element={<ProtectedRoute roles={['Analyst', 'Supervisor', 'System Administrator']}><CommandCenterPage /></ProtectedRoute>} />
        <Route path="/similarity" element={<ProtectedRoute roles={['Analyst', 'Supervisor', 'System Administrator']}><SimilarityPage /></ProtectedRoute>} />
        <Route path="/agent-workbench" element={<ProtectedRoute roles={['Analyst', 'Supervisor', 'System Administrator']}><AgentWorkbenchPage /></ProtectedRoute>} />
        <Route path="/inbox" element={<ProtectedRoute roles={['Investigator', 'Analyst', 'Supervisor', 'System Administrator']}><InboxPage /></ProtectedRoute>} />
        <Route path="/access-control" element={<ProtectedRoute roles={['Investigator', 'Analyst', 'Supervisor', 'System Administrator']}><AccessControlPage /></ProtectedRoute>} />
        <Route path="/coordination" element={<ProtectedRoute roles={['Investigator', 'Analyst', 'Supervisor', 'System Administrator']}><CoordinationPage /></ProtectedRoute>} />
        <Route path="/groups" element={<ProtectedRoute roles={['Investigator', 'Analyst', 'Supervisor', 'System Administrator']}><GroupManagerPage /></ProtectedRoute>} />
        <Route path="/audit-log" element={<ProtectedRoute roles={['Investigator', 'Analyst', 'Supervisor', 'System Administrator']}><AuditLogPage /></ProtectedRoute>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes></ErrorBoundary>
    </HashRouter>
  );
}

export default App;
