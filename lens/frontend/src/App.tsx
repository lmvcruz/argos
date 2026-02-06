import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import {
  BarChart3,
  Activity,
  AlertTriangle,
  FileText,
  CheckCircle,
} from 'lucide-react';
import LocalInspection from './pages/LocalInspection';
import LocalTests from './pages/LocalTests';
import CIInspection from './pages/CIInspection';
import ScoutLayout from './components/Scout/ScoutLayout';
import ExecutionList from './components/Scout/ExecutionList';
import WorkflowBrowser from './components/Scout/WorkflowBrowser';
import AnalysisPanel from './components/Scout/AnalysisPanel';
import HealthDashboard from './components/Scout/HealthDashboard';
import ComparisonView from './components/Scout/ComparisonView';
import ConfigPanel from './components/Scout/ConfigPanel';
import DatabaseCommands from './components/Scout/DatabaseCommands';
import { ScoutProvider } from './contexts/ScoutContext';
import { ConfigProvider, useConfig } from './config/ConfigContext';
import api from './api/client';

/**
 * Main Lens Frontend Application
 *
 * Provides scenario-based analysis dashboard with:
 * - Local code inspection
 * - Local test execution
 * - CI workflow inspection
 */
function AppContent() {
  const [serverHealthy, setServerHealthy] = useState(true);
  const [loading, setLoading] = useState(true);
  const { config } = useConfig();

  useEffect(() => {
    // Check server health on app load
    const checkHealth = async () => {
      try {
        await api.checkHealth();
        setServerHealthy(true);
      } catch (error) {
        console.error('Server health check failed:', error);
        setServerHealthy(false);
      } finally {
        setLoading(false);
      }
    };

    checkHealth();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-900">
        <div className="text-white text-center">
          <Activity className="animate-spin mx-auto mb-4" size={40} />
          <p>Loading Lens...</p>
        </div>
      </div>
    );
  }

  if (!serverHealthy) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-900">
        <div className="text-white text-center">
          <AlertTriangle className="mx-auto mb-4 text-red-500" size={40} />
          <p className="text-xl mb-2">Backend Server Unavailable</p>
          <p className="text-gray-400 mb-4">Make sure the Lens backend is running on port 8000</p>
          <code className="bg-gray-800 p-4 rounded block text-sm">
            python -m lens.backend.server:app
          </code>
        </div>
      </div>
    );
  }

  return (
    <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <AppLayout />
    </Router>
  );
}

function AppLayout() {
  const { config } = useConfig();
  const location = useLocation();

  return (
    <div className="flex h-screen bg-gray-900 text-gray-100">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-800 border-r border-gray-700 overflow-y-auto">
        <div className="p-6">
          <div className="flex items-center gap-3 mb-8">
            <BarChart3 className="text-blue-500" size={32} />
            <h1 className="text-2xl font-bold">Lens</h1>
          </div>

          {/* Scenario Section */}
          {config && (
            <div>
              <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
                Scenarios
              </h3>
              <nav className="space-y-2">
                {config.features.localInspection.enabled && (
                  <NavLink
                    to="/local-inspection"
                    icon={FileText}
                    label="Local Inspection"
                    active={location.pathname === '/local-inspection'}
                  />
                )}
                {config.features.localTests.enabled && (
                  <NavLink
                    to="/local-tests"
                    icon={CheckCircle}
                    label="Local Tests"
                    active={location.pathname === '/local-tests'}
                  />
                )}
                {config.features.ciInspection.enabled && (
                  <NavLink
                    to="/ci-inspection"
                    icon={Activity}
                    label="CI Inspection (Legacy)"
                    active={location.pathname === '/ci-inspection'}
                  />
                )}
                {config.features.ciInspection.enabled && (
                  <NavLink
                    to="/scout/workflows"
                    icon={Activity}
                    label="Scout CI (New)"
                    active={location.pathname.startsWith('/scout')}
                  />
                )}
              </nav>
            </div>
          )}
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <Routes>
          {/* Scenario Routes */}
          <Route path="/" element={<LocalInspection />} />
          <Route path="/local-inspection" element={<LocalInspection />} />
          <Route path="/local-tests" element={<LocalTests />} />
          <Route path="/ci-inspection" element={<CIInspection />} />

          {/* Scout CI Inspection Routes */}
          <Route
            path="/scout/*"
            element={
              <ScoutProvider>
                <ScoutLayout />
              </ScoutProvider>
            }
          >
            <Route path="executions" element={<ExecutionList />} />
            <Route path="workflows" element={<WorkflowBrowser />} />
            <Route path="database-commands" element={<DatabaseCommands />} />
            <Route path="analysis" element={<AnalysisPanel />} />
            <Route path="health" element={<HealthDashboard />} />
            <Route path="comparison" element={<ComparisonView />} />
            <Route path="config" element={<ConfigPanel />} />
          </Route>
        </Routes>
      </main>
    </div>
  );
}

function AppWrapper() {
  return (
    <ConfigProvider>
      <AppContent />
    </ConfigProvider>
  );
}

function NavLink({
  to,
  icon: Icon,
  label,
  active,
}: {
  to: string;
  icon: any;
  label: string;
  active?: boolean;
}) {
  return (
    <Link
      to={to}
      className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
        active
          ? 'bg-blue-600 text-white'
          : 'hover:bg-gray-700 text-gray-100'
      }`}
    >
      <Icon size={20} />
      <span>{label}</span>
    </Link>
  );
}

export default AppWrapper;
