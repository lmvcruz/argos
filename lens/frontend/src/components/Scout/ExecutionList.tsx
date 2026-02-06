/**
 * ExecutionList
 *
 * Browse and list CI executions from the Scout database.
 * Light-weight listing without automatic fetching.
 */

import React, { useState, useEffect } from 'react';
import { RefreshCw, Filter, Clock, GitBranch, CheckCircle, XCircle, AlertCircle } from 'lucide-react';

interface Execution {
  run_id: number;
  run_number: number;
  workflow_name: string;
  status: string;
  conclusion: string;
  started_at: string;
  branch: string;
  commit_sha: string;
}

const ExecutionList: React.FC = () => {
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [limit, setLimit] = useState(50);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [branchFilter, setBranchFilter] = useState<string>('');
  const [selectedExecution, setSelectedExecution] = useState<Execution | null>(null);
  const [dbStatus, setDbStatus] = useState<any>(null);
  const [checkingDb, setCheckingDb] = useState(false);

  // Check database status
  const checkDbStatus = async () => {
    setCheckingDb(true);
    try {
      const response = await fetch('/api/scout/database/status');
      if (response.ok) {
        const status = await response.json();
        setDbStatus(status);
        console.log('Database status:', status);
      }
    } catch (err) {
      console.error('Failed to check database status:', err);
    } finally {
      setCheckingDb(false);
    }
  };

  // Load executions
  const loadExecutions = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      params.append('limit', limit.toString());
      if (statusFilter) params.append('status', statusFilter);
      if (branchFilter) params.append('branch', branchFilter);

      const response = await fetch(`/api/scout/executions?${params}`);
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to load executions: ${response.statusText}`);
      }
      const data = await response.json();
      setExecutions(data.executions || []);

      // Debug log
      console.log('Loaded executions:', data);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMsg);
      console.error('Error loading executions:', errorMsg);
    } finally {
      setLoading(false);
    }
  };

  // Load on mount
  useEffect(() => {
    checkDbStatus();
    loadExecutions();
  }, []);

  const getStatusIcon = (status: string, conclusion: string) => {
    if (status === 'completed') {
      if (conclusion === 'success') {
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      } else if (conclusion === 'failure') {
        return <XCircle className="w-5 h-5 text-red-600" />;
      }
    }
    if (status === 'in_progress') {
      return <AlertCircle className="w-5 h-5 text-yellow-600 animate-pulse" />;
    }
    return <AlertCircle className="w-5 h-5 text-gray-400" />;
  };

  const getStatusBadgeColor = (status: string, conclusion: string) => {
    if (status === 'completed') {
      if (conclusion === 'success') return 'bg-green-100 text-green-800';
      if (conclusion === 'failure') return 'bg-red-100 text-red-800';
      return 'bg-gray-100 text-gray-800';
    }
    if (status === 'in_progress') return 'bg-yellow-100 text-yellow-800';
    return 'bg-blue-100 text-blue-800';
  };

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="px-8 py-6 border-b border-gray-200 bg-gradient-to-r from-gray-50 to-gray-100">
        <h2 className="text-2xl font-bold text-gray-900">CI Executions</h2>
        <p className="text-sm text-gray-600 mt-1">
          Browse workflow executions from the local Scout database
        </p>
      </div>

      {/* Filters */}
      <div className="px-8 py-4 border-b border-gray-200 bg-gray-50">
        <div className="flex flex-col md:flex-row gap-4 items-end">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <Filter size={16} className="inline mr-2" />
              Status
            </label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">All Status</option>
              <option value="queued">Queued</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
            </select>
          </div>

          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <GitBranch size={16} className="inline mr-2" />
              Branch
            </label>
            <input
              type="text"
              value={branchFilter}
              onChange={(e) => setBranchFilter(e.target.value)}
              placeholder="Filter by branch name"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Limit
            </label>
            <input
              type="number"
              min="1"
              max="500"
              value={limit}
              onChange={(e) => setLimit(parseInt(e.target.value))}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent w-24"
            />
          </div>

          <button
            onClick={loadExecutions}
            disabled={loading}
            className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors font-medium"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            {loading ? 'Loading...' : 'Load'}
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="px-8 py-4 bg-red-50 border-b border-red-200">
          <p className="text-sm text-red-800">Error: {error}</p>
        </div>
      )}

      {/* Content */}
      <div className="flex flex-1 gap-6 p-8 overflow-hidden">
        {/* Executions List */}
        <div className="flex-1 flex flex-col min-w-0">
          {executions.length === 0 ? (
            <div className="flex items-center justify-center h-full text-gray-500">
              <div className="text-center max-w-md">
                <AlertCircle className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p className="font-semibold text-gray-700 mb-2">No executions found</p>

                {/* Database Status Info */}
                {dbStatus && !dbStatus.exists && (
                  <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 text-left text-xs text-orange-800 mb-4">
                    <p className="font-semibold mb-2">📂 Database Not Found</p>
                    <p className="mb-2">Path: <code className="bg-orange-100 px-1 rounded">{dbStatus.path}</code></p>
                    <p>To create the database, run Scout sync:</p>
                    <code className="bg-orange-100 px-2 py-1 rounded block mt-2">scout sync</code>
                  </div>
                )}

                {dbStatus && dbStatus.exists && dbStatus.total_workflows === 0 && (
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-left text-xs text-yellow-800 mb-4">
                    <p className="font-semibold mb-2">📊 Database Empty</p>
                    <p className="mb-2">The database exists but has no workflow data.</p>
                    <p>Run Scout fetch to populate data:</p>
                    <code className="bg-yellow-100 px-2 py-1 rounded block mt-2">scout fetch</code>
                  </div>
                )}

                {dbStatus && dbStatus.exists && dbStatus.total_workflows > 0 && executions.length === 0 && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-left text-xs text-blue-800 mb-4">
                    <p className="font-semibold mb-2">🔍 Data Exists But Filtered Out</p>
                    <p className="mb-2">Database has {dbStatus.total_workflows} workflows.</p>
                    <p>Try:</p>
                    <ul className="list-disc list-inside space-y-1 mt-2">
                      <li>Clearing filters (Status, Branch)</li>
                      <li>Increasing limit</li>
                      <li>Reloading the data</li>
                    </ul>
                  </div>
                )}

                {!dbStatus && (
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-left text-xs text-gray-800 mb-4">
                    <p className="text-center">Checking database status...</p>
                  </div>
                )}

                <div className="flex gap-2 justify-center">
                  <button
                    onClick={loadExecutions}
                    disabled={loading}
                    className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors disabled:opacity-50"
                  >
                    {loading ? 'Loading...' : 'Reload Executions'}
                  </button>
                  <button
                    onClick={checkDbStatus}
                    disabled={checkingDb}
                    className="px-4 py-2 text-sm bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors disabled:opacity-50"
                  >
                    {checkingDb ? 'Checking...' : 'Check Status'}
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex-1 overflow-y-auto space-y-2 bg-gray-50 rounded-lg p-4">
              {executions.map((exec) => (
                <button
                  key={exec.run_id}
                  onClick={() => setSelectedExecution(exec)}
                  className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
                    selectedExecution?.run_id === exec.run_id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 bg-white hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    {getStatusIcon(exec.status, exec.conclusion)}
                    <div className="flex-1 min-w-0">
                      <div className="font-semibold text-gray-900 truncate">
                        {exec.workflow_name}
                      </div>
                      <div className="text-xs text-gray-600 mt-1">
                        Run #{exec.run_number} • {exec.branch}
                      </div>
                    </div>
                    <div className={`px-2 py-1 rounded text-xs font-medium whitespace-nowrap ${getStatusBadgeColor(exec.status, exec.conclusion)}`}>
                      {exec.conclusion}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Details Panel */}
        {selectedExecution && (
          <div className="w-80 bg-gray-50 rounded-lg p-6 border border-gray-200 overflow-y-auto">
            <h3 className="font-bold text-lg text-gray-900 mb-4">Execution Details</h3>

            <div className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-gray-600 uppercase">Workflow</label>
                <p className="text-sm text-gray-900">{selectedExecution.workflow_name}</p>
              </div>

              <div>
                <label className="text-xs font-semibold text-gray-600 uppercase">Run</label>
                <p className="text-sm text-gray-900">#{selectedExecution.run_number}</p>
              </div>

              <div>
                <label className="text-xs font-semibold text-gray-600 uppercase">Status</label>
                <p className={`text-sm font-medium ${
                  selectedExecution.conclusion === 'success'
                    ? 'text-green-700'
                    : selectedExecution.conclusion === 'failure'
                    ? 'text-red-700'
                    : 'text-yellow-700'
                }`}>
                  {selectedExecution.status} / {selectedExecution.conclusion}
                </p>
              </div>

              <div>
                <label className="text-xs font-semibold text-gray-600 uppercase">Branch</label>
                <p className="text-sm text-gray-900 font-mono">{selectedExecution.branch}</p>
              </div>

              <div>
                <label className="text-xs font-semibold text-gray-600 uppercase">Commit</label>
                <p className="text-sm text-gray-900 font-mono truncate">{selectedExecution.commit_sha}</p>
              </div>

              <div>
                <label className="text-xs font-semibold text-gray-600 uppercase flex items-center gap-2">
                  <Clock size={14} />
                  Started
                </label>
                <p className="text-sm text-gray-900">
                  {new Date(selectedExecution.started_at).toLocaleString()}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ExecutionList;
