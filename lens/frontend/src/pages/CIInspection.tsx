/**
 * CI Inspection scenario page
 * Analyze CI/CD workflow execution and results
 */

import {
  Activity,
  GitBranch,
  Clock,
  AlertTriangle,
  Loader,
  RefreshCw,
  XCircle,
} from 'lucide-react';
import { useEffect } from 'react';
import {
  ResultsTable,
  SeverityBadge,
  CollapsibleSection,
  type TableColumn,
  type TableRow,
} from '../components';
import { useConfig } from '../config/ConfigContext';
import { useWorkflowHistory } from '../hooks';

/**
 * CIInspection page - Analyze CI/CD workflow execution
 */
export default function CIInspection() {
  const { isFeatureEnabled } = useConfig();
  const { data, loading, error, fetch } = useWorkflowHistory();

  // Initial load
  useEffect(() => {
    fetch();
  }, [fetch]);

  // Convert workflows to table rows
  const results: TableRow[] = (data?.workflows || []).map((workflow) => ({
    id: workflow.id,
    workflowName: workflow.name,
    run: `#${workflow.run_number}`,
    branch: workflow.branch,
    status: workflow.status,
    result: workflow.result,
    duration: `${Math.round(workflow.duration / 1000)}s`,
    timestamp: new Date(workflow.started_at).toLocaleString(),
  }));

  const columns: TableColumn[] = [
    { key: 'workflowName', label: 'Workflow', width: '25%', sortable: true },
    { key: 'run', label: 'Run', width: '10%', sortable: true },
    {
      key: 'branch',
      label: 'Branch',
      width: '20%',
      sortable: true,
      render: (value) => (
        <div className="flex items-center gap-1">
          <GitBranch size={14} />
          {value}
        </div>
      ),
    },
    {
      key: 'result',
      label: 'Result',
      width: '15%',
      sortable: true,
      render: (value) => {
        const severityMap: Record<string, any> = {
          passed: 'success',
          failed: 'error',
          pending: 'info',
        };
        return (
          <SeverityBadge
            severity={severityMap[value as string] || 'info'}
            label={value as string}
            size="sm"
          />
        );
      },
    },
    {
      key: 'duration',
      label: 'Duration',
      width: '15%',
      sortable: true,
      render: (value) => (
        <div className="flex items-center gap-1">
          <Clock size={14} />
          {value}
        </div>
      ),
    },
    { key: 'timestamp', label: 'Timestamp', width: '15%', sortable: true },
  ];

  // Calculate stats
  const passedCount = data?.workflows.filter((w) => w.result === 'passed').length || 0;
  const failedCount = data?.workflows.filter((w) => w.result === 'failed').length || 0;
  const runningCount = data?.workflows.filter((w) => w.status === 'in_progress').length || 0;
  const successRate =
    data && data.workflows.length > 0
      ? Math.round((passedCount / data.workflows.length) * 100)
      : 0;

  if (!isFeatureEnabled('ciInspection')) {
    return (
      <div className="p-6">
        <div className="bg-yellow-50 dark:bg-yellow-900/30 border border-yellow-200 dark:border-yellow-700 rounded-lg p-4">
          <AlertTriangle className="inline mr-2 text-yellow-600" size={20} />
          <span className="text-yellow-800 dark:text-yellow-200">
            CI Inspection feature is disabled in configuration
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2">CI Inspection</h1>
        <p className="text-gray-600 dark:text-gray-400">
          Monitor and analyze CI/CD workflow execution and results
        </p>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700 rounded-lg p-4 flex items-start gap-3">
          <XCircle className="text-red-600 flex-shrink-0 mt-0.5" size={20} />
          <div>
            <p className="font-semibold text-red-800 dark:text-red-200">Failed to load workflows</p>
            <p className="text-sm text-red-700 dark:text-red-300">{error.message}</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <div className="lg:col-span-1 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <h3 className="font-semibold text-sm text-gray-600 dark:text-gray-400 mb-2">
            RECENT STATUS
          </h3>
          <div className="space-y-3">
            <div>
              <div className="text-xs text-gray-500 mb-1">Passed</div>
              <div className="text-2xl font-bold text-green-600">{passedCount}</div>
            </div>
            <div>
              <div className="text-xs text-gray-500 mb-1">Failed</div>
              <div className="text-2xl font-bold text-red-600">{failedCount}</div>
            </div>
            <div>
              <div className="text-xs text-gray-500 mb-1">Running</div>
              <div className="text-2xl font-bold text-blue-600">{runningCount}</div>
            </div>
            <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
              <div className="text-xs text-gray-500 mb-1">Success Rate</div>
              <div className="text-2xl font-bold text-blue-600">{successRate}%</div>
            </div>
          </div>
        </div>

        <div className="lg:col-span-3 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-bold text-lg flex items-center gap-2">
              <Activity size={20} />
              Workflow History
            </h2>
            <button
              onClick={() => fetch()}
              disabled={loading}
              className="px-3 py-1.5 text-sm bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded flex items-center gap-2 disabled:opacity-50"
            >
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
              Refresh
            </button>
          </div>

          {loading && data === null ? (
            <div className="flex items-center justify-center py-12">
              <Loader size={24} className="animate-spin text-blue-600" />
              <span className="ml-2 text-gray-600 dark:text-gray-400">
                Loading workflows...
              </span>
            </div>
          ) : results.length > 0 ? (
            <ResultsTable columns={columns} rows={results} pageSize={10} />
          ) : (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              No workflows found
            </div>
          )}
        </div>
      </div>

      <CollapsibleSection
        title="Workflow Configuration"
        icon={<Activity size={20} />}
        defaultExpanded={false}
      >
        <div className="space-y-3 font-mono text-sm">
          <div className="bg-gray-50 dark:bg-gray-900 p-3 rounded">
            <div className="text-gray-600 dark:text-gray-400">Sync Status:</div>
            <div className={data?.sync_status.is_syncing ? 'text-yellow-600' : 'text-green-600'}>
              {data?.sync_status.is_syncing ? 'Syncing...' : 'Connected & Synced'}
            </div>
          </div>
          <div className="bg-gray-50 dark:bg-gray-900 p-3 rounded">
            <div className="text-gray-600 dark:text-gray-400">
              Last Sync:
            </div>
            <div className="text-gray-900 dark:text-gray-100">
              {data?.sync_status.last_sync
                ? new Date(data.sync_status.last_sync).toLocaleString()
                : 'Never'}
            </div>
          </div>
          <div className="bg-gray-50 dark:bg-gray-900 p-3 rounded">
            <div className="text-gray-600 dark:text-gray-400">
              Backend:
            </div>
            <div className="text-gray-900 dark:text-gray-100">
              http://localhost:8000
            </div>
          </div>
        </div>
      </CollapsibleSection>
    </div>
  );
}