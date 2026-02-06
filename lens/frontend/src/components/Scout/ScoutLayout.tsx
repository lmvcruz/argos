import React, { useState, useEffect } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  Activity,
  GitBranch,
  Zap,
  BarChart3,
  Settings,
  CheckCircle,
  AlertCircle,
} from 'lucide-react';
import { useScout } from '../../contexts/ScoutContext';

/**
 * ScoutLayout
 *
 * Main container for Scout CI Inspection features.
 * Provides navigation, sync status, and layout for sub-pages.
 */

const ScoutLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { syncStatus, fetchSyncStatus, syncStatusLoading } = useScout();
  const [isCollapsed, setIsCollapsed] = useState(false);

  // Load sync status on mount
  useEffect(() => {
    fetchSyncStatus();
  }, [fetchSyncStatus]);

  const navItems = [
    {
      path: '/scout/workflows',
      label: 'Workflows',
      icon: Activity,
      description: 'Browse CI workflow runs',
    },
    {
      path: '/scout/analysis',
      label: 'Analysis',
      icon: BarChart3,
      description: 'Analyze failure patterns',
    },
    {
      path: '/scout/health',
      label: 'Health',
      icon: Zap,
      description: 'Flaky test detection',
    },
    {
      path: '/scout/comparison',
      label: 'Comparison',
      icon: GitBranch,
      description: 'Compare workflow runs',
    },
    {
      path: '/scout/config',
      label: 'Config',
      icon: Settings,
      description: 'Scout settings',
    },
  ];

  const isActive = (path: string) => location.pathname === path;

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar Navigation */}
      <div
        className={`${
          isCollapsed ? 'w-20' : 'w-64'
        } bg-white border-r border-gray-200 flex flex-col transition-all duration-200`}
      >
        {/* Header */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            {!isCollapsed && (
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center">
                  <Activity className="w-5 h-5 text-white" />
                </div>
                <h1 className="text-lg font-bold text-gray-900">Scout</h1>
              </div>
            )}
            <button
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="p-1 hover:bg-gray-100 rounded-lg transition-colors"
              title={isCollapsed ? 'Expand' : 'Collapse'}
            >
              <GitBranch className="w-5 h-5 text-gray-600" />
            </button>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 overflow-y-auto p-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.path);

            return (
              <button
                key={item.path}
                onClick={() => navigate(item.path)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg mb-1 transition-colors text-left ${
                  active
                    ? 'bg-blue-50 text-blue-700 border-l-4 border-blue-500'
                    : 'text-gray-700 hover:bg-gray-50'
                }`}
                title={isCollapsed ? item.label : undefined}
              >
                <Icon className={`flex-shrink-0 ${active ? 'w-5 h-5 text-blue-600' : 'w-5 h-5'}`} />
                {!isCollapsed && (
                  <div className="flex-1 min-w-0">
                    <div className="font-medium truncate">{item.label}</div>
                    <div className="text-xs text-gray-500 truncate">{item.description}</div>
                  </div>
                )}
              </button>
            );
          })}
        </nav>

        {/* Sync Status Card */}
        {!isCollapsed && syncStatus && (
          <div className="border-t border-gray-200 p-4">
            <div className="text-sm font-semibold text-gray-700 mb-2">Database Status</div>

            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-600">Workflows:</span>
                <span className="font-semibold text-gray-900">
                  {syncStatusLoading ? '...' : syncStatus.total_workflows}
                </span>
              </div>

              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-600">Jobs:</span>
                <span className="font-semibold text-gray-900">
                  {syncStatusLoading ? '...' : syncStatus.total_jobs}
                </span>
              </div>

              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-600">Tests:</span>
                <span className="font-semibold text-gray-900">
                  {syncStatusLoading ? '...' : syncStatus.total_test_results}
                </span>
              </div>

              {syncStatus.last_sync && (
                <div className="pt-2 border-t border-gray-200">
                  <div className="text-xs text-gray-500">
                    Last sync:{' '}
                    {new Date(syncStatus.last_sync).toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </div>
                </div>
              )}

              {syncStatus.total_workflows > 0 ? (
                <div className="flex items-center gap-1 mt-2 text-green-700 text-xs">
                  <CheckCircle className="w-4 h-4" />
                  <span>Ready</span>
                </div>
              ) : (
                <div className="flex items-center gap-1 mt-2 text-yellow-700 text-xs">
                  <AlertCircle className="w-4 h-4" />
                  <span>Sync required</span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header Bar */}
        <div className="bg-white border-b border-gray-200 px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">CI Inspection</h2>
              <p className="text-sm text-gray-600 mt-1">Browse, analyze, and compare CI data</p>
            </div>

            {/* Quick Status */}
            {syncStatus && (
              <div className="flex items-center gap-4 px-4 py-2 bg-gray-50 rounded-lg">
                {syncStatus.total_workflows > 0 ? (
                  <>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-gray-900">
                        {syncStatus.total_workflows}
                      </div>
                      <div className="text-xs text-gray-600">Workflows</div>
                    </div>
                    <div className="w-px h-8 bg-gray-300"></div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-gray-900">
                        {syncStatus.total_jobs}
                      </div>
                      <div className="text-xs text-gray-600">Jobs</div>
                    </div>
                  </>
                ) : (
                  <div className="text-sm text-gray-600">No CI data available</div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Page Content */}
        <div className="flex-1 overflow-auto">
          <Outlet />
        </div>
      </div>
    </div>
  );
};

export default ScoutLayout;
