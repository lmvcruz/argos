/**
 * Local Code Inspection scenario page
 * Analyzes code quality, coverage, and style issues in local projects
 */

import {
  FileText,
  Play,
  Settings,
  AlertCircle,
  Loader,
  XCircle,
} from 'lucide-react';
import { useState, useEffect } from 'react';
import {
  FileTree,
  ResultsTable,
  CollapsibleSection,
  SeverityBadge,
  OutputPanel,
  type FileTreeNode,
  type TableColumn,
  type TableRow,
  type LogEntry,
} from '../components';
import { useConfig } from '../config/ConfigContext';
import { useAnvilAnalysis } from '../hooks';

/**
 * LocalInspection page - Analyze code quality and style issues
 */
export default function LocalInspection() {
  const { isFeatureEnabled, getConfig } = useConfig();
  const { data, loading, error, analyze } = useAnvilAnalysis();
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [analysisTarget, setAnalysisTarget] = useState<string | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [projectPath, setProjectPath] = useState<string>('');
  const [fileTree, setFileTree] = useState<FileTreeNode[]>([]);
  const [loadingFiles, setLoadingFiles] = useState(false);

  // Load file tree on mount or when project path changes
  useEffect(() => {
    const loadFiles = async () => {
      const path = projectPath || getConfig('tools.anvil.projectPath') || 'd:\\playground\\argos';
      setProjectPath(path);

      setLoadingFiles(true);
      try {
        const response = await fetch(`http://localhost:8000/api/anvil/list-files?root=${encodeURIComponent(path)}`);
        if (response.ok) {
          const result = await response.json();
          setFileTree([result.tree]);
        } else {
          // Fallback to mock tree if API fails
          setFileTree([
            {
              id: 'root',
              name: 'project',
              type: 'folder',
              children: [],
            },
          ]);
        }
      } catch (err) {
        console.error('Failed to load files:', err);
        // Fallback to mock tree
        setFileTree([
          {
            id: 'root',
            name: 'project',
            type: 'folder',
            children: [],
          },
        ]);
      } finally {
        setLoadingFiles(false);
      }
    };

    loadFiles();
  }, [getConfig]);

  // Convert Anvil issues to table rows
  const results: TableRow[] = (data?.issues || []).map((issue) => ({
    id: issue.id,
    file: issue.file,
    line: issue.line,
    severity: issue.severity,
    rule: issue.rule,
    message: issue.message,
  }));

  const columns: TableColumn[] = [
    { key: 'file', label: 'File', width: '30%', sortable: true },
    { key: 'line', label: 'Line', width: '10%', sortable: true },
    {
      key: 'severity',
      label: 'Severity',
      width: '15%',
      sortable: true,
      render: (value) => (
        <SeverityBadge
          severity={value as any}
          size="sm"
        />
      ),
    },
    { key: 'rule', label: 'Rule', width: '20%', sortable: true },
    { key: 'message', label: 'Message', width: '25%' },
  ];

  const handleRunAnalysis = async () => {
    // Use analysis target if set, otherwise use project path
    let analyzeTarget = analysisTarget || projectPath || getConfig('tools.anvil.projectPath') || 'd:\\playground\\argos';
    setLogs([
      {
        timestamp: new Date().toLocaleTimeString(),
        level: 'info',
        message: 'Starting code analysis...',
      },
      {
        timestamp: new Date().toLocaleTimeString(),
        level: 'info',
        message: `Scanning project: ${analyzeTarget}`,
      },
    ]);

    try {
      await analyze({ projectPath: analyzeTarget });
      setLogs((prev) => [
        ...prev,
        {
          timestamp: new Date().toLocaleTimeString(),
          level: 'info',
          message: 'Analysis complete',
        },
      ]);
    } catch (err) {
      setLogs((prev) => [
        ...prev,
        {
          timestamp: new Date().toLocaleTimeString(),
          level: 'error',
          message: `Analysis failed: ${err instanceof Error ? err.message : 'Unknown error'}`,
        },
      ]);
    }
  };

  // Get stats from data
  const errorCount = results.filter((r) => r.severity === 'error').length;
  const warningCount = results.filter((r) => r.severity === 'warning').length;
  const infoCount = results.filter((r) => r.severity === 'info').length;

  if (!isFeatureEnabled('localInspection')) {
    return (
      <div className="p-6">
        <div className="bg-yellow-50 dark:bg-yellow-900/30 border border-yellow-200 dark:border-yellow-700 rounded-lg p-4">
          <AlertCircle className="inline mr-2 text-yellow-600" size={20} />
          <span className="text-yellow-800 dark:text-yellow-200">
            Local Inspection feature is disabled in configuration
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2">Local Code Inspection</h1>
        <p className="text-gray-600 dark:text-gray-400">
          Analyze code quality, style, and coverage issues in your local project
        </p>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700 rounded-lg p-4 flex items-start gap-3">
          <XCircle className="text-red-600 flex-shrink-0 mt-0.5" size={20} />
          <div>
            <p className="font-semibold text-red-800 dark:text-red-200">Analysis failed</p>
            <p className="text-sm text-red-700 dark:text-red-300">{error.message}</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* File Explorer */}
        <div className="lg:col-span-1 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <h2 className="font-bold text-lg mb-2 flex items-center gap-2">
            <FileText size={20} />
            Files
          </h2>
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-4">
            Double-click a folder to set it as analysis target
          </p>
          <FileTree
            nodes={fileTree}
            onSelectNode={setSelectedFile}
            selectedNodeId={selectedFile ?? undefined}
            onSetAnalysisTarget={setAnalysisTarget}
            analysisTargetId={analysisTarget ?? undefined}
          />
        </div>

        {/* Results and Controls */}
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-bold text-lg">Analysis Results</h2>
              <button
                onClick={handleRunAnalysis}
                disabled={loading}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader size={16} className="animate-spin" />
                    Running...
                  </>
                ) : (
                  <>
                    <Play size={16} />
                    Run Analysis
                  </>
                )}
              </button>
            </div>

            {/* Summary Stats */}
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="bg-red-50 dark:bg-red-900/20 p-4 rounded">
                <SeverityBadge severity="error" />
                <div className="text-2xl font-bold mt-2 text-red-700 dark:text-red-300">
                  {errorCount}
                </div>
              </div>
              <div className="bg-yellow-50 dark:bg-yellow-900/20 p-4 rounded">
                <SeverityBadge severity="warning" />
                <div className="text-2xl font-bold mt-2 text-yellow-700 dark:text-yellow-300">
                  {warningCount}
                </div>
              </div>
              <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded">
                <SeverityBadge severity="info" />
                <div className="text-2xl font-bold mt-2 text-blue-700 dark:text-blue-300">
                  {infoCount}
                </div>
              </div>
            </div>

            {/* Results Table */}
            {results.length > 0 ? (
              <ResultsTable
                columns={columns}
                rows={results}
                selectedRowId={selectedFile ?? undefined}
              />
            ) : (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                {data ? 'No issues found' : 'Run analysis to see results'}
              </div>
            )}
          </div>

          {/* Output Panel */}
          <div>
            <h3 className="font-bold text-lg mb-2">Output</h3>
            <OutputPanel logs={logs} maxHeight="300px" />
          </div>

          {/* Detailed Info */}
          <CollapsibleSection
            title="Configuration"
            icon={<Settings size={20} />}
          >
            <div className="space-y-3 font-mono text-sm">
              <div className="flex flex-col gap-2">
                <span className="text-gray-600 dark:text-gray-400">
                  Root Project Path:
                </span>
                <input
                  type="text"
                  value={projectPath || getConfig('tools.anvil.projectPath') || 'd:\\playground\\argos'}
                  onChange={(e) => {
                    setProjectPath(e.target.value);
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      // Reload file tree when pressing Enter
                      const path = e.currentTarget.value;
                      const loadFiles = async () => {
                        setLoadingFiles(true);
                        try {
                          const response = await fetch(`http://localhost:8000/api/anvil/list-files?root=${encodeURIComponent(path)}`);
                          if (response.ok) {
                            const result = await response.json();
                            setFileTree([result.tree]);
                          }
                        } catch (err) {
                          console.error('Failed to load files:', err);
                        } finally {
                          setLoadingFiles(false);
                        }
                      };
                      loadFiles();
                    }
                  }}
                  className="text-gray-900 dark:text-gray-100 bg-gray-100 dark:bg-gray-700 px-3 py-2 rounded text-xs font-mono w-full"
                  placeholder="Enter project root path"
                />
                <span className="text-gray-500 dark:text-gray-500 text-xs">Press Enter to reload files</span>
              </div>
              <div className="flex flex-col gap-2 border-t border-gray-200 dark:border-gray-700 pt-3">
                <span className="text-gray-600 dark:text-gray-400">
                  Analysis Target:
                </span>
                <div className="bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-700 rounded p-3">
                  {analysisTarget ? (
                    <div className="flex items-center justify-between">
                      <span className="text-gray-900 dark:text-gray-100 font-mono truncate">
                        {analysisTarget}
                      </span>
                      <button
                        onClick={() => setAnalysisTarget(null)}
                        className="ml-2 text-xs text-green-600 dark:text-green-400 hover:text-green-800 dark:hover:text-green-200 font-semibold"
                      >
                        Clear
                      </button>
                    </div>
                  ) : (
                    <span className="text-gray-500 dark:text-gray-400 text-xs">
                      Double-click a folder in the file tree to select
                    </span>
                  )}
                </div>
              </div>
              <div className="flex justify-between pt-3 border-t border-gray-200 dark:border-gray-700">
                <span className="text-gray-600 dark:text-gray-400">
                  Backend:
                </span>
                <span className="text-gray-900 dark:text-gray-100">
                  http://localhost:8000
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">
                  Status:
                </span>
                <span className="text-gray-900 dark:text-gray-100">
                  {loading ? 'Analyzing...' : data ? 'Ready' : 'Idle'}
                </span>
              </div>
            </div>
          </CollapsibleSection>
        </div>
      </div>
    </div>
  );
}
