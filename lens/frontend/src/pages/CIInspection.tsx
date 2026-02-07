/**
 * CI Inspection scenario page
 * Analyze CI/CD workflow execution and results with enhanced timeline view
 */

import {
  Activity,
  AlertTriangle,
  Loader,
  XCircle,
  BarChart3,
  Zap,
  TrendingUp,
  RefreshCw,
} from 'lucide-react';
import { useEffect, useState } from 'react';
import {
  SeverityBadge,
  CollapsibleSection,
  SyncStatusBar,
  WorkflowTimeline,
  FailureAnalysisDashboard,
  PerformanceTrendingChart,
  RunComparison,
  ExecutionTree,
  type WorkflowExecution,
} from '../components';
import { useConfig } from '../config/ConfigContext';
import { useWorkflowHistory } from '../hooks';

type TabType = 'timeline' | 'executions' | 'failures' | 'performance' | 'comparison';

/**
 * CIInspection page - Analyze CI/CD workflow execution
 */
export default function CIInspection() {
  const { isFeatureEnabled } = useConfig();
  const { data, loading, error, fetch } = useWorkflowHistory();
  const [activeTab, setActiveTab] = useState<TabType>('executions');
  const [selectedWorkflow, setSelectedWorkflow] = useState<string | null>(null);
  const [selectedJob, setSelectedJob] = useState<string | null>(null);

  // Initial load
  useEffect(() => {
    fetch();
  }, [fetch]);

  // Convert workflows to executions format
  const executions: WorkflowExecution[] = (data?.workflows || []).map((w) => ({
    id: w.id,
    name: w.name,
    status: w.status,
    result: w.result,
    duration: w.duration,
    started_at: w.started_at,
    jobs: w.jobs || [],
  }));

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
    <div className="space-y-0">
      {/* Sync Status Bar */}
      <SyncStatusBar onRefresh={() => fetch()} />

      {/* Main Content */}
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
              <p className="font-semibold text-red-800 dark:text-red-200">
                Failed to load workflows
              </p>
              <p className="text-sm text-red-700 dark:text-red-300">{error.message}</p>
            </div>
          </div>
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <StatCard
            icon={<Activity size={20} />}
            label="Total Runs"
            value={data?.workflows.length || 0}
            color="blue"
          />
          <StatCard
            icon={<Activity size={20} />}
            label="Passed"
            value={passedCount}
            color="green"
          />
          <StatCard
            icon={<Activity size={20} />}
            label="Failed"
            value={failedCount}
            color="red"
          />
          <StatCard
            icon={<Zap size={20} />}
            label="Running"
            value={runningCount}
            color="blue"
          />
          <StatCard
            icon={<TrendingUp size={20} />}
            label="Success Rate"
            value={`${successRate}%`}
            color="purple"
          />
        </div>

        {/* Two-Column Layout for Executions Tab */}
        {activeTab === 'executions' && (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Execution Tree */}
            <div className="lg:col-span-1 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
              <div className="flex items-center justify-between mb-3">
                <h2 className="font-bold text-lg flex items-center gap-2">
                  <Activity size={20} />
                  Executions
                </h2>
                <button
                  onClick={() => fetch()}
                  disabled={loading}
                  className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                  title="Refresh executions"
                >
                  <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
                </button>
              </div>
              <ExecutionTree
                executions={executions}
                onSelectExecution={setSelectedWorkflow}
                selectedExecutionId={selectedWorkflow ?? undefined}
                onSelectJob={(executionId, jobId) => {
                  setSelectedWorkflow(executionId);
                  setSelectedJob(jobId);
                }}
              />
            </div>

            {/* Execution Details */}
            <div className="lg:col-span-3 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
              {selectedWorkflow ? (
                <div className="space-y-4">
                  <h3 className="font-bold text-lg">Execution Details</h3>
                  {executions.find((e) => e.id === selectedWorkflow) && (
                    <div className="space-y-2 font-mono text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600 dark:text-gray-400">ID:</span>
                        <span>{selectedWorkflow}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600 dark:text-gray-400">Name:</span>
                        <span>{executions.find((e) => e.id === selectedWorkflow)?.name}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600 dark:text-gray-400">Status:</span>
                        <span>{executions.find((e) => e.id === selectedWorkflow)?.status}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600 dark:text-gray-400">Duration:</span>
                        <span>{executions.find((e) => e.id === selectedWorkflow)?.duration.toFixed(1)}s</span>
                      </div>
                    </div>
                  )}
                  {selectedJob && (
                    <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                      <h4 className="font-semibold mb-2">Job Details</h4>
                      <div className="space-y-2 font-mono text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-600 dark:text-gray-400">Job ID:</span>
                          <span>{selectedJob}</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                  <Activity size={32} className="mx-auto mb-2 opacity-50" />
                  <p>Select an execution to view details</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Tabs for other views */}
        {activeTab !== 'executions' && (
          <>
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
              <div className="flex border-b border-gray-200 dark:border-gray-700 overflow-x-auto">
                <TabButton
                  label="Executions"
                  icon={<Activity size={16} />}
                  active={activeTab === 'executions'}
                  onClick={() => setActiveTab('executions')}
                />
                <TabButton
                  label="Timeline"
                  icon={<Activity size={16} />}
                  active={activeTab === 'timeline'}
                  onClick={() => setActiveTab('timeline')}
                />
                <TabButton
                  label="Failures"
                  icon={<AlertTriangle size={16} />}
                  active={activeTab === 'failures'}
                  onClick={() => setActiveTab('failures')}
                />
                <TabButton
                  label="Performance"
                  icon={<BarChart3 size={16} />}
                  active={activeTab === 'performance'}
                  onClick={() => setActiveTab('performance')}
                />
                <TabButton
                  label="Comparison"
                  icon={<TrendingUp size={16} />}
                  active={activeTab === 'comparison'}
                  onClick={() => setActiveTab('comparison')}
                />
              </div>

              <div className="p-6">
                {loading && data === null ? (
                  <div className="flex items-center justify-center py-12">
                    <Loader size={24} className="animate-spin text-blue-600" />
                    <span className="ml-2 text-gray-600 dark:text-gray-400">
                      Loading workflows...
                    </span>
                  </div>
                ) : (
                  <>
                    {activeTab === 'timeline' && (
                      <TabContent>
                        {data?.workflows && data.workflows.length > 0 ? (
                          <WorkflowTimeline
                            workflows={data.workflows}
                            onSelectWorkflow={setSelectedWorkflow}
                            loading={loading}
                          />
                        ) : (
                          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                            No workflows found. Sync CI data to view runs.
                          </div>
                        )}
                      </TabContent>
                    )}

                    {activeTab === 'failures' && (
                      <TabContent>
                        <FailureAnalysisDashboard />
                      </TabContent>
                    )}

                    {activeTab === 'performance' && (
                      <TabContent>
                        <PerformanceTrendingChart />
                      </TabContent>
                    )}

                    {activeTab === 'comparison' && (
                      <TabContent>
                        <RunComparison />
                      </TabContent>
                    )}
                  </>
                )}
              </div>
        </div>

        {/* Configuration Section */}
        <CollapsibleSection
          title="Workflow Configuration"
          icon={<Activity size={20} />}
          defaultExpanded={false}
        >
          <div className="space-y-3 font-mono text-sm">
            <div className="bg-gray-50 dark:bg-gray-900 p-3 rounded">
              <div className="text-gray-600 dark:text-gray-400">Sync Status:</div>
              <div className={data?.sync_status?.is_syncing ? 'text-yellow-600' : 'text-green-600'}>
                {data?.sync_status?.is_syncing ? 'Syncing...' : 'Connected & Synced'}
              </div>
            </div>
            <div className="bg-gray-50 dark:bg-gray-900 p-3 rounded">
              <div className="text-gray-600 dark:text-gray-400">Last Sync:</div>
              <div className="text-gray-900 dark:text-gray-100">
                {data?.sync_status?.last_sync
                  ? new Date(data.sync_status.last_sync).toLocaleString()
                  : 'Never'}
              </div>
            </div>
            <div className="bg-gray-50 dark:bg-gray-900 p-3 rounded">
              <div className="text-gray-600 dark:text-gray-400">Backend:</div>
              <div className="text-gray-900 dark:text-gray-100">
                http://localhost:8000
              </div>
            </div>
          </div>
        </CollapsibleSection>
      </div>
    </div>
  );
}

/**
 * StatCard - Display a single stat
 */
function StatCard({
  icon,
  label,
  value,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  color: 'blue' | 'green' | 'red' | 'purple';
}) {
  const colorClasses = {
    blue: 'text-blue-600 dark:text-blue-400',
    green: 'text-green-600 dark:text-green-400',
    red: 'text-red-600 dark:text-red-400',
    purple: 'text-purple-600 dark:text-purple-400',
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
      <div className={`${colorClasses[color]} mb-2`}>{icon}</div>
      <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">{label}</div>
      <div className={`text-2xl font-bold ${colorClasses[color]}`}>{value}</div>
    </div>
  );
}

/**
 * TabButton - Tab navigation button
 */
function TabButton({
  label,
  icon,
  active,
  onClick,
}: {
  label: string;
  icon: React.ReactNode;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`
        flex items-center gap-2 px-4 py-3 font-medium text-sm transition-colors
        ${
          active
            ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400'
            : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
        }
      `}
    >
      {icon}
      {label}
    </button>
  );
}

/**
 * TabContent - Wrapper for tab content
 */
function TabContent({ children }: { children: React.ReactNode }) {
  return <div className="space-y-4">{children}</div>;
}
