import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import {
  BarChart3,
  Activity,
  AlertTriangle,
  Settings,
  Home,
} from 'lucide-react';
import CIDashboard from './pages/CIDashboard';
import Comparison from './pages/Comparison';
import FlakyTests from './pages/FlakyTests';
import FailurePatterns from './pages/FailurePatterns';
import api from './api/client';

/**
 * Main Lens Frontend Application
 *
 * Provides CI analytics and visualization dashboard with:
 * - CI health monitoring
 * - Platform-specific failure detection
 * - Local vs CI comparison
 * - Flaky test analysis
 */
function App() {
  const [serverHealthy, setServerHealthy] = useState(true);
  const [loading, setLoading] = useState(true);

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
    <Router>
      <div className="flex h-screen bg-gray-900 text-gray-100">
        {/* Sidebar */}
        <aside className="w-64 bg-gray-800 border-r border-gray-700">
          <div className="p-6">
            <div className="flex items-center gap-3 mb-8">
              <BarChart3 className="text-blue-500" size={32} />
              <h1 className="text-2xl font-bold">Lens</h1>
            </div>
            <nav className="space-y-2">
              <NavLink to="/" icon={Home} label="CI Health" />
              <NavLink to="/comparison" icon={Activity} label="Local vs CI" />
              <NavLink to="/flaky-tests" icon={AlertTriangle} label="Flaky Tests" />
              <NavLink to="/failure-patterns" icon={Settings} label="Failure Patterns" />
            </nav>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 overflow-auto">
          <Routes>
            <Route path="/" element={<CIDashboard />} />
            <Route path="/comparison" element={<Comparison />} />
            <Route path="/flaky-tests" element={<FlakyTests />} />
            <Route path="/failure-patterns" element={<FailurePatterns />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

function NavLink({ to, icon: Icon, label }: { to: string; icon: any; label: string }) {
  return (
    <Link
      to={to}
      className="flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-gray-700 transition-colors"
    >
      <Icon size={20} />
      <span>{label}</span>
    </Link>
  );
}

export default App;
