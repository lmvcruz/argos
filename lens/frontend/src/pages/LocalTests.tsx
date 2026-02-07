/**
 * Local Tests scenario page
 * Execute and analyze test execution results
 */

import {
  CheckCircle,
  Play,
  AlertTriangle,
  Loader,
  XCircle,
  FileText,
  Settings,
  RefreshCw,
} from 'lucide-react';
import { useState, useEffect } from 'react';
import {
  ResultsTable,
  SeverityBadge,
  OutputPanel,
  TestTree,
  CollapsibleSection,
  type TableColumn,
  type TableRow,
  type LogEntry,
  type TestNode,
} from '../components';
import { useConfig } from '../config/ConfigContext';
import { useTestExecution } from '../hooks';
import { verdictClient } from '../api/tools';

/**
 * LocalTests page - Execute and analyze test suites
 */
export default function LocalTests() {
  const { isFeatureEnabled, getConfig } = useConfig();
  const { data, loading, error, execute } = useTestExecution();
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [projectPath, setProjectPath] = useState<string>('');
  const [testDiscoveryTarget, setTestDiscoveryTarget] = useState<string | null>(null);
  const [selectedTest, setSelectedTest] = useState<string | null>(null);
  const [testTree, setTestTree] = useState<TestNode[]>([]);
  const [loadingTests, setLoadingTests] = useState(false);
  const [filterStatus, setFilterStatus] = useState<'all' | 'passed' | 'failed' | 'flaky' | 'skipped'>('all');

  // Load tests on mount and project path change
  useEffect(() => {
    const loadTests = async () => {
      const path = projectPath || getConfig('tools.verdict.projectPath') || 'd:\\playground\\argos';
      setProjectPath(path);

      setLoadingTests(true);
      try {
        const result = await verdictClient.discover(path);

        // Group tests by file
        const grouped = new Map<string, TestNode[]>();
        for (const test of result.tests) {
          if (!grouped.has(test.file)) {
            grouped.set(test.file, []);
          }
          grouped.get(test.file)!.push({
            id: test.id,
            name: test.name,
            file: test.file,
            type: 'test',
            status: test.status,
          });
        }

        // Create file nodes with test children
        const fileNodes: TestNode[] = Array.from(grouped.entries()).map(([file, tests]) => ({
          id: file,
          name: file.split('/').pop() || file,
          file: file,
          type: 'file',
          status: 'not-run',
          children: tests,
        }));

        setTestTree(fileNodes);
      } catch (err) {
        console.error('Failed to discover tests:', err);
        setLogs((prev) => [
          ...prev,
          {
            timestamp: new Date().toLocaleTimeString(),
            level: 'error',
            message: `Test discovery failed: ${err instanceof Error ? err.message : 'Unknown error'}`,
          },
        ]);
      } finally {
        setLoadingTests(false);
      }
    };

    loadTests();
  }, [getConfig, projectPath]);

  // Convert test results to table rows
  const results: TableRow[] = (data?.tests || [])
    .filter((test) => {
      if (filterStatus === 'all') return true;
      return test.status === filterStatus;
    })
    .map((test) => ({
      id: test.id,
      testName: test.name,
      duration: test.duration,
      status: test.status,
      file: test.file,
    }));

  const columns: TableColumn[] = [
    { key: 'testName', label: 'Test Name', width: '40%', sortable: true },
    {
      key: 'status',
      label: 'Status',
      width: '15%',
      sortable: true,
      render: (value) => {
        const severityMap: Record<string, any> = {
          passed: 'success',
          failed: 'error',
          flaky: 'warning',
          skipped: 'info',
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
      label: 'Duration (ms)',
      width: '20%',
      sortable: true,
      render: (value) => `${value}ms`,
    },
    { key: 'file', label: 'File', width: '25%', sortable: true },
  ];

  const handleRunTests = async () => {
    const path = testDiscoveryTarget || projectPath || getConfig('tools.verdict.projectPath') || 'd:\\playground\\argos';

    const newLogs: LogEntry[] = [
      {
        timestamp: new Date().toLocaleTimeString(),
        level: 'info',
        message: 'Starting test suite execution...',
      },
      {
        timestamp: new Date().toLocaleTimeString(),
        level: 'info',
        message: `Project: ${path}`,
      },
    ];

    setLogs(newLogs);

    try {
      await execute({ projectPath: path });
      setLogs((prev) => [
        ...prev,
        {
          timestamp: new Date().toLocaleTimeString(),
          level: 'info',
          message: 'Test execution complete',
        },
      ]);
    } catch (err) {
      setLogs((prev) => [
        ...prev,
        {
          timestamp: new Date().toLocaleTimeString(),
          level: 'error',
          message: `Tests failed: ${err instanceof Error ? err.message : 'Unknown error'}`,
        },
      ]);
    }
  };

  // Get stats from data
  const passedCount = data?.summary.passed || 0;
  const failedCount = data?.summary.failed || 0;
  const flakyCount = data?.summary.flaky || 0;
  const totalTime = data?.summary.duration || 0;

  if (!isFeatureEnabled('localTests')) {
    return (
      <div className="p-6">
        <div className="bg-yellow-50 dark:bg-yellow-900/30 border border-yellow-200 dark:border-yellow-700 rounded-lg p-4">
          <AlertTriangle className="inline mr-2 text-yellow-600" size={20} />
          <span className="text-yellow-800 dark:text-yellow-200">
            Local Tests feature is disabled in configuration
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2">Local Tests</h1>
        <p className="text-gray-600 dark:text-gray-400">
          Discover, execute, and analyze test suite execution results
        </p>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700 rounded-lg p-4 flex items-start gap-3">
          <XCircle className="text-red-600 flex-shrink-0 mt-0.5" size={20} />
          <div>
            <p className="font-semibold text-red-800 dark:text-red-200">Test execution failed</p>
            <p className="text-sm text-red-700 dark:text-red-300">{error.message}</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Test Discovery Tree */}
        <div className="lg:col-span-1 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-bold text-lg flex items-center gap-2">
              <FileText size={20} />
              Tests
            </h2>
            <button
              onClick={() => {
                const path = projectPath || getConfig('tools.verdict.projectPath') || 'd:\\playground\\argos';
                setProjectPath(path);
              }}
              disabled={loadingTests}
              className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
              title="Refresh tests"
            >
              <RefreshCw size={16} className={loadingTests ? 'animate-spin' : ''} />
            </button>
          </div>
          <TestTree
            nodes={testTree}
            onSelectTest={setSelectedTest}
            selectedTestId={selectedTest ?? undefined}
          />
        </div>

        {/* Results Panel */}
        <div className="lg:col-span-3 space-y-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="font-bold text-lg">Test Results</h2>
              <button
                onClick={handleRunTests}
                disabled={loading}
                className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 flex items-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader size={16} className="animate-spin" />
                    Running...
                  </>
                ) : (
                  <>
                    <Play size={16} />
                    Run Tests
                  </>
                )}
              </button>
            </div>

            {/* Summary Stats */}
            <div className="grid grid-cols-5 gap-3">
              <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded">
                <div className="text-xs font-semibold text-blue-700 dark:text-blue-300 mb-1">
                  Total
                </div>
                <div className="text-2xl font-bold text-blue-700 dark:text-blue-300">
                  {data?.summary.total || 0}
                </div>
              </div>
              <div className="bg-green-50 dark:bg-green-900/20 p-3 rounded">
                <SeverityBadge severity="success" size="sm" />
                <div className="text-2xl font-bold mt-1 text-green-700 dark:text-green-300">
                  {passedCount}
                </div>
              </div>
              <div className="bg-red-50 dark:bg-red-900/20 p-3 rounded">
                <SeverityBadge severity="error" size="sm" />
                <div className="text-2xl font-bold mt-1 text-red-700 dark:text-red-300">
                  {failedCount}
                </div>
              </div>
              <div className="bg-yellow-50 dark:bg-yellow-900/20 p-3 rounded">
                <SeverityBadge severity="warning" size="sm" />
                <div className="text-2xl font-bold mt-1 text-yellow-700 dark:text-yellow-300">
                  {flakyCount}
                </div>
              </div>
              <div className="bg-purple-50 dark:bg-purple-900/20 p-3 rounded">
                <div className="text-xs font-semibold text-purple-700 dark:text-purple-300 mb-1">
                  Time
                </div>
                <div className="text-2xl font-bold text-purple-700 dark:text-purple-300">
                  {(totalTime / 1000).toFixed(1)}s
                </div>
              </div>
            </div>

            {/* Filter Controls */}
            {results.length > 0 && (
              <div className="flex gap-2 pb-4 border-b border-gray-200 dark:border-gray-700">
                <span className="text-sm text-gray-600 dark:text-gray-400 self-center">Filter:</span>
                {(['all', 'passed', 'failed', 'flaky', 'skipped'] as const).map((status) => (
                  <button
                    key={status}
                    onClick={() => setFilterStatus(status)}
                    className={`px-3 py-1 text-sm rounded ${
                      filterStatus === status
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                    }`}
                  >
                    {status.charAt(0).toUpperCase() + status.slice(1)}
                  </button>
                ))}
              </div>
            )}

            {/* Results Table */}
            {results.length > 0 ? (
              <ResultsTable
                columns={columns}
                rows={results}
                pageSize={10}
              />
            ) : (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                {data ? 'No test results available' : 'Run tests to see results'}
              </div>
            )}
          </div>

          {/* Output Panel */}
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
            <h3 className="font-bold text-lg mb-3">Execution Output</h3>
            <OutputPanel logs={logs} maxHeight="300px" />
          </div>

          {/* Configuration */}
          <CollapsibleSection title="Configuration" icon={<Settings size={20} />}>
            <div className="space-y-3 font-mono text-sm">
              <div className="flex flex-col gap-2">
                <span className="text-gray-600 dark:text-gray-400">
                  Root Project Path:
                </span>
                <input
                  type="text"
                  value={projectPath || getConfig('tools.verdict.projectPath') || 'd:\\playground\\argos'}
                  onChange={(e) => setProjectPath(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      const path = e.currentTarget.value;
                      const loadTests = async () => {
                        setLoadingTests(true);
                        try {
                          const response = await fetch(`/api/anvil/list-files?root=${encodeURIComponent(path)}`);
                          if (response.ok) {
                            const result = await response.json();
                            setTestTree([result.tree]);
                          }
                        } catch (err) {
                          console.error('Failed to load project structure:', err);
                        } finally {
                          setLoadingTests(false);
                        }
                      };
                      loadTests();
                    }
                  }}
                  className="text-gray-900 dark:text-gray-100 bg-gray-100 dark:bg-gray-700 px-3 py-2 rounded text-xs font-mono w-full"
                  placeholder="Enter project root path"
                />
                <span className="text-gray-500 text-xs">Press Enter to reload project structure</span>
              </div>
              <div className="flex flex-col gap-2 border-t border-gray-200 dark:border-gray-700 pt-3">
                <span className="text-gray-600 dark:text-gray-400">
                  Test Target:
                </span>
                <div className="bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-700 rounded p-3">
                  {testDiscoveryTarget ? (
                    <div className="flex items-center justify-between">
                      <span className="text-gray-900 dark:text-gray-100 font-mono truncate text-xs">
                        {testDiscoveryTarget}
                      </span>
                      <button
                        onClick={() => setTestDiscoveryTarget(null)}
                        className="ml-2 text-xs text-green-600 dark:text-green-400 hover:text-green-800 dark:hover:text-green-200 font-semibold"
                      >
                        Clear
                      </button>
                    </div>
                  ) : (
                    <span className="text-gray-500 dark:text-gray-400 text-xs">
                      Double-click a folder in the project tree to select
                    </span>
                  )}
                </div>
              </div>
            </div>
          </CollapsibleSection>
        </div>
      </div>
    </div>
  );
}
