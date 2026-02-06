/**
 * DatabaseCommands
 *
 * UI for Scout database commands: list, show-log, show-data
 * Provides interfaces to query local Scout database and display results.
 */

import React, { useState } from 'react';
import {
  Database,
  Search,
  Filter,
  Copy,
  Download,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  Clock,
  GitBranch,
  CheckCircle,
  XCircle,
} from 'lucide-react';

interface ExecutionListItem {
  run_id: number;
  workflow_name: string;
  status: string;
  conclusion: string;
  branch: string;
  started_at: string;
  completed_at?: string;
  duration_seconds?: number;
}

interface JobLogItem {
  job_id: string;
  job_name: string;
  status: string;
  conclusion: string;
  started_at?: string;
  completed_at?: string;
  test_summary: {
    total: number;
    passed: number;
    failed: number;
    skipped: number;
  };
}

interface AnalysisData {
  run_id: number;
  workflow_name: string;
  branch: string;
  status: string;
  started_at?: string;
  statistics: {
    total_tests: number;
    passed: number;
    failed: number;
    skipped: number;
    pass_rate: number;
  };
  failure_patterns: Record<string, string[]>;
  jobs_count: number;
}

type CommandType = 'list' | 'show-log' | 'show-data';

const DatabaseCommands: React.FC = () => {
  const [activeCommand, setActiveCommand] = useState<CommandType>('list');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // List command state
  const [executions, setExecutions] = useState<ExecutionListItem[]>([]);
  const [listFilters, setListFilters] = useState({
    workflow: '',
    branch: '',
    status: '',
    last: 10,
  });

  // Show-log command state
  const [selectedRunId, setSelectedRunId] = useState<number | null>(null);
  const [logData, setLogData] = useState<{
    run_id: number;
    workflow_name: string;
    branch: string;
    status: string;
    started_at?: string;
    completed_at?: string;
    jobs: JobLogItem[];
    total_jobs: number;
  } | null>(null);
  const [expandedJobs, setExpandedJobs] = useState<Set<string>>(new Set());

  // Show-data command state
  const [analysisRunId, setAnalysisRunId] = useState<number | null>(null);
  const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null);

  // Execute list command
  const handleListCommand = async () => {
    setLoading(true);
    setError(null);
    console.log('📋 List command clicked');
    try {
      const params = new URLSearchParams();
      if (listFilters.workflow) params.append('workflow', listFilters.workflow);
      if (listFilters.branch) params.append('branch', listFilters.branch);
      if (listFilters.status) params.append('status', listFilters.status);
      params.append('last', listFilters.last.toString());

      const url = `/api/scout/list?${params}`;
      console.log('🔗 Fetching from:', url);

      const response = await fetch(url);
      console.log('📡 Response status:', response.status);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.detail || `Command failed: ${response.statusText}`
        );
      }
      const data = await response.json();
      console.log('✅ Data received:', data);
      setExecutions(data.executions || []);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error occurred';
      console.error('❌ Error:', errorMsg);
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  // Execute show-log command
  const handleShowLog = async (runId: number) => {
    setSelectedRunId(runId);
    setLoading(true);
    setError(null);
    console.log('📜 Show log command clicked with run ID:', runId);
    try {
      const url = `/api/scout/show-log/${runId}`;
      console.log('🔗 Fetching from:', url);

      const response = await fetch(url);
      console.log('📡 Response status:', response.status);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.detail || `Failed to fetch logs: ${response.statusText}`
        );
      }
      const data = await response.json();
      console.log('✅ Log data received:', data);
      setLogData(data);
      setExpandedJobs(new Set());
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error occurred';
      console.error('❌ Error:', errorMsg);
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  // Execute show-data command
  const handleShowData = async (runId: number) => {
    setAnalysisRunId(runId);
    setLoading(true);
    setError(null);
    console.log('📊 Show data command clicked with run ID:', runId);
    try {
      const url = `/api/scout/show-data/${runId}`;
      console.log('🔗 Fetching from:', url);

      const response = await fetch(url);
      console.log('📡 Response status:', response.status);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.detail || `Failed to fetch analysis: ${response.statusText}`
        );
      }
      const data = await response.json();
      console.log('✅ Analysis data received:', data);
      setAnalysisData(data);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error occurred';
      console.error('❌ Error:', errorMsg);
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const toggleJobExpansion = (jobId: string) => {
    const newExpanded = new Set(expandedJobs);
    if (newExpanded.has(jobId)) {
      newExpanded.delete(jobId);
    } else {
      newExpanded.add(jobId);
    }
    setExpandedJobs(newExpanded);
  };

  const getStatusIcon = (status: string, conclusion?: string) => {
    if (status === 'completed' && conclusion === 'success') {
      return <CheckCircle className="w-4 h-4 text-green-600" />;
    }
    if (status === 'completed' && conclusion === 'failure') {
      return <XCircle className="w-4 h-4 text-red-600" />;
    }
    return <AlertCircle className="w-4 h-4 text-yellow-600" />;
  };

  return (
    <div className="w-full h-full bg-gray-50 p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-4">
          <Database className="w-6 h-6 text-blue-600" />
          <h1 className="text-2xl font-bold text-gray-900">
            Scout Database Commands
          </h1>
        </div>
        <p className="text-gray-600">
          Query and inspect local Scout database executions and analysis data
        </p>
      </div>

      {/* Command Selector */}
      <div className="mb-6 flex gap-4 border-b border-gray-200">
        <button
          onClick={() => setActiveCommand('list')}
          className={`px-4 py-2 font-medium border-b-2 transition-colors ${
            activeCommand === 'list'
              ? 'text-blue-600 border-blue-600'
              : 'text-gray-600 border-transparent hover:text-gray-900'
          }`}
        >
          List Executions
        </button>
        <button
          onClick={() => setActiveCommand('show-log')}
          className={`px-4 py-2 font-medium border-b-2 transition-colors ${
            activeCommand === 'show-log'
              ? 'text-blue-600 border-blue-600'
              : 'text-gray-600 border-transparent hover:text-gray-900'
          }`}
        >
          Show Logs
        </button>
        <button
          onClick={() => setActiveCommand('show-data')}
          className={`px-4 py-2 font-medium border-b-2 transition-colors ${
            activeCommand === 'show-data'
              ? 'text-blue-600 border-blue-600'
              : 'text-gray-600 border-transparent hover:text-gray-900'
          }`}
        >
          Analysis Data
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-red-900">Error</h3>
            <p className="text-red-700 text-sm mt-1">{error}</p>
            <div className="text-red-600 text-xs mt-2 space-y-1">
              <p><strong>Troubleshooting:</strong></p>
              <p>1. Make sure the Lens backend is running:</p>
              <code className="block bg-red-100 p-1 rounded mt-1">python -m lens.backend.server</code>
              <p className="mt-1">2. Check browser console (F12) for more details</p>
              <p>3. Verify API endpoint is reachable (check Network tab)</p>
            </div>
          </div>
        </div>
      )}

      {/* List Executions Command */}
      {activeCommand === 'list' && (
        <div className="space-y-4">
          {/* Filters */}
          <div className="bg-white p-4 rounded-lg border border-gray-200 space-y-3">
            <div className="flex items-center gap-2 mb-3">
              <Filter className="w-4 h-4 text-gray-600" />
              <h2 className="font-semibold text-gray-900">Filters</h2>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <input
                type="text"
                placeholder="Workflow name..."
                value={listFilters.workflow}
                onChange={(e) =>
                  setListFilters({ ...listFilters, workflow: e.target.value })
                }
                className="px-3 py-2 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <input
                type="text"
                placeholder="Branch..."
                value={listFilters.branch}
                onChange={(e) =>
                  setListFilters({ ...listFilters, branch: e.target.value })
                }
                className="px-3 py-2 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <select
                value={listFilters.status}
                onChange={(e) =>
                  setListFilters({ ...listFilters, status: e.target.value })
                }
                className="px-3 py-2 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Status (all)</option>
                <option value="completed">Completed</option>
                <option value="in_progress">In Progress</option>
                <option value="queued">Queued</option>
              </select>
              <select
                value={listFilters.last}
                onChange={(e) =>
                  setListFilters({
                    ...listFilters,
                    last: parseInt(e.target.value),
                  })
                }
                className="px-3 py-2 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="5">Last 5</option>
                <option value="10">Last 10</option>
                <option value="20">Last 20</option>
                <option value="50">Last 50</option>
              </select>
            </div>
            <button
              onClick={handleListCommand}
              disabled={loading}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {loading ? 'Loading...' : 'Execute List Command'}
            </button>
          </div>

          {/* Results */}
          {executions.length > 0 && (
            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
              <div className="p-4 bg-gray-50 border-b border-gray-200">
                <h2 className="font-semibold text-gray-900">
                  Found {executions.length} Execution(s)
                </h2>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="px-4 py-2 text-left text-sm font-semibold text-gray-900">
                        Run ID
                      </th>
                      <th className="px-4 py-2 text-left text-sm font-semibold text-gray-900">
                        Workflow
                      </th>
                      <th className="px-4 py-2 text-left text-sm font-semibold text-gray-900">
                        Status
                      </th>
                      <th className="px-4 py-2 text-left text-sm font-semibold text-gray-900">
                        Branch
                      </th>
                      <th className="px-4 py-2 text-left text-sm font-semibold text-gray-900">
                        Started
                      </th>
                      <th className="px-4 py-2 text-left text-sm font-semibold text-gray-900">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {executions.map((execution) => (
                      <tr
                        key={execution.run_id}
                        className="border-b border-gray-200 hover:bg-gray-50 transition-colors"
                      >
                        <td className="px-4 py-2 text-sm font-medium text-gray-900">
                          {execution.run_id}
                        </td>
                        <td className="px-4 py-2 text-sm text-gray-600">
                          {execution.workflow_name}
                        </td>
                        <td className="px-4 py-2 text-sm">
                          <div className="flex items-center gap-2">
                            {getStatusIcon(execution.status, execution.conclusion)}
                            <span className="capitalize">
                              {execution.conclusion || execution.status}
                            </span>
                          </div>
                        </td>
                        <td className="px-4 py-2 text-sm text-gray-600">
                          <div className="flex items-center gap-1">
                            <GitBranch className="w-4 h-4" />
                            {execution.branch}
                          </div>
                        </td>
                        <td className="px-4 py-2 text-sm text-gray-600">
                          <div className="flex items-center gap-1">
                            <Clock className="w-4 h-4" />
                            {new Date(execution.started_at).toLocaleString()}
                          </div>
                        </td>
                        <td className="px-4 py-2 text-sm">
                          <div className="flex gap-2">
                            <button
                              onClick={() =>
                                handleShowLog(execution.run_id)
                              }
                              className="px-3 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
                            >
                              Logs
                            </button>
                            <button
                              onClick={() =>
                                handleShowData(execution.run_id)
                              }
                              className="px-3 py-1 text-xs bg-green-100 text-green-700 rounded hover:bg-green-200 transition-colors"
                            >
                              Data
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Show Logs Command */}
      {activeCommand === 'show-log' && (
        <div className="space-y-4">
          {/* Input */}
          <div className="bg-white p-4 rounded-lg border border-gray-200 space-y-3">
            <label className="block text-sm font-semibold text-gray-900">
              Workflow Run ID
            </label>
            <div className="flex gap-2">
              <input
                type="number"
                placeholder="Enter run ID..."
                value={selectedRunId || ''}
                onChange={(e) =>
                  setSelectedRunId(
                    e.target.value ? parseInt(e.target.value) : null
                  )
                }
                className="flex-1 px-3 py-2 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={() =>
                  selectedRunId && handleShowLog(selectedRunId)
                }
                disabled={loading || !selectedRunId}
                className="px-4 py-2 bg-blue-600 text-white rounded font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                {loading ? 'Loading...' : 'Show Logs'}
              </button>
            </div>
          </div>

          {/* Logs Display */}
          {logData && (
            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
              <div className="p-4 bg-gray-50 border-b border-gray-200">
                <h2 className="font-semibold text-gray-900 mb-2">
                  Logs for Run {logData.run_id}
                </h2>
                <div className="text-sm text-gray-600 grid grid-cols-2 gap-2">
                  <div>
                    Workflow: <span className="font-medium">{logData.workflow_name}</span>
                  </div>
                  <div>
                    Branch: <span className="font-medium">{logData.branch}</span>
                  </div>
                </div>
              </div>
              <div className="space-y-2 p-4">
                {logData.jobs.map((job) => (
                  <div
                    key={job.job_id}
                    className="border border-gray-200 rounded"
                  >
                    <button
                      onClick={() => toggleJobExpansion(job.job_id)}
                      className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex items-center gap-3 text-left flex-1">
                        {getStatusIcon(job.status, job.conclusion)}
                        <div>
                          <div className="font-medium text-gray-900">
                            {job.job_name}
                          </div>
                          <div className="text-sm text-gray-600">
                            {job.test_summary.total} tests:{' '}
                            <span className="text-green-600">
                              {job.test_summary.passed} passed
                            </span>
                            {', '}
                            <span className="text-red-600">
                              {job.test_summary.failed} failed
                            </span>
                            {', '}
                            <span className="text-gray-600">
                              {job.test_summary.skipped} skipped
                            </span>
                          </div>
                        </div>
                      </div>
                      {expandedJobs.has(job.job_id) ? (
                        <ChevronUp className="w-5 h-5" />
                      ) : (
                        <ChevronDown className="w-5 h-5" />
                      )}
                    </button>
                    {expandedJobs.has(job.job_id) && (
                      <div className="px-4 py-3 bg-gray-50 border-t border-gray-200 text-sm">
                        <div className="space-y-1 font-mono text-xs text-gray-700">
                          <div>Job ID: {job.job_id}</div>
                          <div>Status: {job.status}</div>
                          <div>
                            Started:{' '}
                            {job.started_at
                              ? new Date(job.started_at).toLocaleString()
                              : 'N/A'}
                          </div>
                          <div>
                            Completed:{' '}
                            {job.completed_at
                              ? new Date(job.completed_at).toLocaleString()
                              : 'N/A'}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Show Analysis Data Command */}
      {activeCommand === 'show-data' && (
        <div className="space-y-4">
          {/* Input */}
          <div className="bg-white p-4 rounded-lg border border-gray-200 space-y-3">
            <label className="block text-sm font-semibold text-gray-900">
              Workflow Run ID
            </label>
            <div className="flex gap-2">
              <input
                type="number"
                placeholder="Enter run ID..."
                value={analysisRunId || ''}
                onChange={(e) =>
                  setAnalysisRunId(
                    e.target.value ? parseInt(e.target.value) : null
                  )
                }
                className="flex-1 px-3 py-2 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={() =>
                  analysisRunId && handleShowData(analysisRunId)
                }
                disabled={loading || !analysisRunId}
                className="px-4 py-2 bg-blue-600 text-white rounded font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                {loading ? 'Loading...' : 'Show Analysis'}
              </button>
            </div>
          </div>

          {/* Analysis Display */}
          {analysisData && (
            <div className="space-y-4">
              {/* Header */}
              <div className="bg-white p-4 rounded-lg border border-gray-200">
                <h2 className="font-semibold text-gray-900 mb-3">
                  Analysis Results for Run {analysisData.run_id}
                </h2>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Workflow:</span>
                    <span className="ml-2 font-medium">
                      {analysisData.workflow_name}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600">Branch:</span>
                    <span className="ml-2 font-medium">
                      {analysisData.branch}
                    </span>
                  </div>
                </div>
              </div>

              {/* Statistics */}
              <div className="grid grid-cols-4 gap-4">
                <div className="bg-white p-4 rounded-lg border border-gray-200">
                  <div className="text-sm text-gray-600 mb-1">Total Tests</div>
                  <div className="text-2xl font-bold text-gray-900">
                    {analysisData.statistics.total_tests}
                  </div>
                </div>
                <div className="bg-white p-4 rounded-lg border border-gray-200">
                  <div className="text-sm text-gray-600 mb-1">Passed</div>
                  <div className="text-2xl font-bold text-green-600">
                    {analysisData.statistics.passed}
                  </div>
                </div>
                <div className="bg-white p-4 rounded-lg border border-gray-200">
                  <div className="text-sm text-gray-600 mb-1">Failed</div>
                  <div className="text-2xl font-bold text-red-600">
                    {analysisData.statistics.failed}
                  </div>
                </div>
                <div className="bg-white p-4 rounded-lg border border-gray-200">
                  <div className="text-sm text-gray-600 mb-1">Pass Rate</div>
                  <div className="text-2xl font-bold text-blue-600">
                    {analysisData.statistics.pass_rate.toFixed(1)}%
                  </div>
                </div>
              </div>

              {/* Failure Patterns */}
              {Object.keys(analysisData.failure_patterns).length > 0 && (
                <div className="bg-white p-4 rounded-lg border border-gray-200">
                  <h3 className="font-semibold text-gray-900 mb-3">
                    Failure Patterns
                  </h3>
                  <div className="space-y-2">
                    {Object.entries(analysisData.failure_patterns).map(
                      ([pattern, tests]) => (
                        <div key={pattern} className="border border-gray-200 rounded p-3">
                          <div className="font-medium text-gray-900 mb-2 capitalize">
                            {pattern}
                          </div>
                          <div className="text-sm text-gray-600 space-y-1">
                            {tests.slice(0, 5).map((test, idx) => (
                              <div key={idx} className="font-mono text-xs">
                                • {test}
                              </div>
                            ))}
                            {tests.length > 5 && (
                              <div className="text-gray-500 text-xs">
                                ... and {tests.length - 5} more
                              </div>
                            )}
                          </div>
                        </div>
                      )
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default DatabaseCommands;
