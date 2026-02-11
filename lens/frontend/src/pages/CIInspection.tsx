/**
 * CI Inspection page
 * Analyze CI/CD workflow execution and results
 */

import {
  Activity,
  AlertTriangle,
  Loader,
  XCircle,
  RefreshCw,
  CheckCircle,
  Clock,
  PlayCircle,
  Download,
  FileText,
} from 'lucide-react';
import React, { useState } from 'react';
import {
  ExecutionTree,
  LogViewer,
  type WorkflowExecution,
} from '../components';
import { ScoutDataViewer } from '../components/ScoutDataViewer';
import JobParseResultViewer from '../components/JobParseResultViewer';
import { useConfig } from '../config/ConfigContext';
import { useProjects } from '../contexts/ProjectContext';
import { useWorkflowHistory } from '../hooks';
import { scoutClient } from '../api/tools';
import './CIInspection.css';


/**
 * CIInspection page - Analyze CI/CD workflow execution
 */
export default function CIInspection() {
  const { isFeatureEnabled } = useConfig();
  const { activeProject } = useProjects();
  const { data, loading, error, fetch } = useWorkflowHistory();
  const [selectedWorkflow, setSelectedWorkflow] = useState<string | null>(null);
  const [selectedExecution, setSelectedExecution] = useState<WorkflowExecution | null>(null);
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const [logContent, setLogContent] = useState<string | null>(null);
  const [parsedData, setParsedData] = useState<any>(null);
  const [jobParseData, setJobParseData] = useState<any>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshError, setRefreshError] = useState<string | null>(null);
  const [fetchingLogs, setFetchingLogs] = useState(false);
  const [parsingData, setParsingData] = useState(false);
  const [logError, setLogError] = useState<string | null>(null);
  const [parseError, setParseError] = useState<string | null>(null);
  const [logsExpanded, setLogsExpanded] = useState(true);
  const [parsedExpanded, setParsedExpanded] = useState(true);

  // Load data from local DB on mount
  React.useEffect(() => {
    if (activeProject && !loading && !data) {
      fetch();
    }
  }, [activeProject, loading, data, fetch]);

  // Auto-load logs when execution with logs is selected
  React.useEffect(() => {
    if (selectedExecution && selectedExecution.has_logs) {
      const loadExistingLogs = async () => {
        try {
          const runId = parseInt(selectedExecution.id);
          const logsData = await scoutClient.getRunLogs(runId);

          if (logsData.jobs && logsData.jobs.length > 0) {
            const combinedLogs = logsData.jobs
              .map((job: any) => {
                if (job.raw_log) {
                  return `\n${'='.repeat(80)}\n` +
                         `Job: ${job.job_name} (ID: ${job.job_id})\n` +
                         `Status: ${job.status} / ${job.conclusion}\n` +
                         `${'='.repeat(80)}\n\n` +
                         job.raw_log;
                }
                return null;
              })
              .filter((log: string | null) => log !== null)
              .join('\n\n');

            setLogContent(combinedLogs || 'No log content available');
          }
        } catch (error) {
          console.error('Failed to load existing logs:', error);
          // Don't show error to user for auto-load, just log it
        }
      };

      loadExistingLogs();
    } else {
      // Clear logs when no execution selected or no logs available
      setLogContent(null);
    }
  }, [selectedExecution]);

  // Refresh handler - fetch latest executions from GitHub and update local DB
  const handleRefresh = async () => {
    setRefreshing(true);
    setRefreshError(null);

    try {
      if (!activeProject) {
        throw new Error('No active project. Please select a project in Config page.');
      }

      const limit = 10;

      await scoutClient.refreshExecutions({ limit });

      // Refresh the executions list after sync
      await fetch();
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to refresh executions';
      setRefreshError(errorMessage);
      console.error('Refresh failed:', error);
    } finally {
      setRefreshing(false);
    }
  };

  // Fetch logs for selected execution or job
  const handleFetchLogs = async () => {
    if (!selectedExecution) return;

    setFetchingLogs(true);
    setLogError(null);

    try {
      // If a specific job is selected, fetch only that job's logs
      if (selectedJobId) {
        const jobId = parseInt(selectedJobId);
        const jobLogsData = await scoutClient.fetchJobLogs(jobId);

        if (jobLogsData.has_log && jobLogsData.log_content) {
          const formattedLog = `\n${'='.repeat(80)}\n` +
                              `Job: ${jobLogsData.job_name} (ID: ${jobLogsData.job_id})\n` +
                              `Run ID: ${jobLogsData.run_id}\n` +
                              `${'='.repeat(80)}\n\n` +
                              jobLogsData.log_content;
          setLogContent(formattedLog);
        } else {
          setLogContent(`No log content available for job ${jobLogsData.job_name}`);
        }
      } else {
        // Fetch logs for entire run
        const runId = parseInt(selectedExecution.id);
        await scoutClient.fetchLogs(runId);

        // Load the logs
        const logsData = await scoutClient.getRunLogs(runId);

        // Extract raw log content from jobs
        if (logsData.jobs && logsData.jobs.length > 0) {
          // Combine all job logs into one text
          const combinedLogs = logsData.jobs
            .map((job: any) => {
              if (job.raw_log) {
                return `\n${'='.repeat(80)}\n` +
                       `Job: ${job.job_name} (ID: ${job.job_id})\n` +
                       `Status: ${job.status} / ${job.conclusion}\n` +
                       `${'='.repeat(80)}\n\n` +
                       job.raw_log;
              }
              return null;
            })
            .filter((log: string | null) => log !== null)
            .join('\n\n');

          setLogContent(combinedLogs || 'No log content available');
        } else {
          setLogContent('No jobs found for this run');
        }
      }

      // Refresh execution list to update availability flags
      await fetch();
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch logs';
      setLogError(errorMessage);
      console.error('Fetch logs failed:', error);
    } finally {
      setFetchingLogs(false);
    }
  };

  // Parse data for selected execution or job
  const handleParseData = async () => {
    if (!selectedExecution) return;

    setParsingData(true);
    setParseError(null);
    setJobParseData(null); // Clear previous job parse data
    setParsedData(null); // Clear previous run parse data

    try {
      // If a specific job is selected, parse only that job
      if (selectedJobId) {
        const jobId = parseInt(selectedJobId);
        const parseResponse = await scoutClient.parseJobData(jobId);

        if (parseResponse && 'data' in parseResponse) {
          // Store directly for JobParseResultViewer
          setJobParseData(parseResponse.data);
        } else {
          setParseError('No parsed data returned for job');
        }
      } else {
        // Parse entire run
        const runId = parseInt(selectedExecution.id);

        // Parse data and get response with full parsed data
        const parseResponse = await scoutClient.parseData(runId);

        // Check if response includes data field
        if (parseResponse && 'data' in parseResponse) {
          setParsedData(parseResponse.data);
        } else {
          // Fallback: try to load from show-data endpoint
          const data = await scoutClient.getParsedData(runId);
          setParsedData(data);
        }
      }

      // Refresh execution list to update availability flags
      await fetch();
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to parse data';
      setParseError(errorMessage);
      console.error('Parse data failed:', error);
    } finally {
      setParsingData(false);
    }
  };

  // Handle execution selection
  const handleSelectExecution = (executionId: string) => {
    setSelectedWorkflow(executionId);
    const execution = executions.find((e) => e.id === executionId);
    setSelectedExecution(execution || null);
    setSelectedJobId(null); // Clear job selection when run is selected

    // Clear previous data
    setLogContent(null);
    setParsedData(null);
    setLogError(null);
    setParseError(null);
  };

  // Handle job selection
  const handleSelectJob = (executionId: string, jobId: string) => {
    // First select the execution
    setSelectedWorkflow(executionId);
    const execution = executions.find((e) => e.id === executionId);
    setSelectedExecution(execution || null);
    setSelectedJobId(jobId);

    // Clear previous data
    setLogContent(null);
    setParsedData(null);
    setLogError(null);
    setParseError(null);
  };

  // Convert workflows to executions format
  const executions: WorkflowExecution[] = (data?.workflows || []).map((w) => ({
    id: w.id,
    name: w.name,
    status: w.status,
    result: w.result,
    duration: w.duration,
    started_at: w.started_at,
    jobs: (w.jobs || []).map((j) => ({
      ...j,
      status: j.status as 'completed' | 'in_progress' | 'queued',
    })),
    has_logs: w.has_logs,
    has_parsed_data: w.has_parsed_data,
  }));

  // Calculate stats
  const passedCount = data?.workflows.filter((w) => w.result === 'passed').length || 0;
  const failedCount = data?.workflows.filter((w) => w.result === 'failed').length || 0;
  const runningCount = data?.workflows.filter((w) => w.status === 'in_progress').length || 0;

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

  // Check if we have actual data (not just empty arrays)
  const hasData = data && data.workflows && data.workflows.length > 0;

  // Check project configuration issues
  const noProject = !activeProject;
  const noToken = activeProject && !activeProject.token;
  const invalidRepo = activeProject && (!activeProject.repo || !activeProject.repo.includes('/'));

  return (
    <div className="ci-inspection-page">
      {/* No project state */}
      {noProject && !loading && (
        <div className="no-project">
          <AlertTriangle size={48} />
          <h2>No Project Selected</h2>
          <p>Please select or create a project in the Config page to use CI Inspection.</p>
        </div>
      )}

      {/* Project has issues */}
      {activeProject && (noToken || invalidRepo) && !loading && !refreshing && (
        <div className="no-project">
          <AlertTriangle size={48} />
          <h2>Project Configuration Issue</h2>
          {noToken && <p>⚠️ GitHub token is not configured for this project.</p>}
          {invalidRepo && <p>⚠️ Repository format is invalid. Expected "owner/repo".</p>}
          <p>Please update the project settings in the Config page.</p>
        </div>
      )}

      {/* No data state - show when no executions exist but project is configured */}
      {activeProject && !noToken && !invalidRepo && !hasData && !loading && !refreshing && (
        <div className="no-project">
          <Activity size={48} />
          <h2>No CI Executions Found</h2>
          <p>Click "Refresh" to fetch CI/CD workflow data from GitHub and save to local database</p>
          <button onClick={handleRefresh} className="fetch-button">
            <RefreshCw size={16} />
            Refresh from GitHub
          </button>
          {refreshError && (
            <div className="sync-error">
              <XCircle size={16} />
              <span>{refreshError}</span>
            </div>
          )}
        </div>
      )}

      {/* Refreshing state */}
      {refreshing && (
        <div className="no-project">
          <Loader size={48} className="spinner" />
          <h2>Refreshing Executions...</h2>
          <p>Fetching latest CI/CD workflow data from GitHub and updating local database</p>
        </div>
      )}

      {/* Two-column layout - only show when we have actual data */}
      {(hasData || loading) && (
        <>
          {/* Left Panel - Execution Tree */}
          <div className="inspection-panel left-panel">
            <div className="panel-header">
              <h2>Executions</h2>
              <button
                onClick={handleRefresh}
                disabled={loading || refreshing}
                className="refresh-button"
                title="Refresh from GitHub and update local database"
              >
                <RefreshCw size={16} className={loading || refreshing ? 'spinning' : ''} />
              </button>
            </div>

            <div className="panel-content">
              {loading && !data ? (
                <div className="loading-state">
                  <Loader size={24} className="spinner" />
                  <span>Loading executions...</span>
                </div>
              ) : error ? (
                <div className="error-state">
                  <XCircle size={24} />
                  <span>Failed to load workflows</span>
                  <p>{error.message}</p>
                </div>
              ) : (
                <ExecutionTree
                  executions={executions}
                  onSelectExecution={handleSelectExecution}
                  selectedExecutionId={selectedWorkflow ?? undefined}
                  selectedJobId={selectedJobId ?? undefined}
                  onSelectJob={handleSelectJob}
                />
              )}
            </div>
          </div>

          {/* Right Panel - Details and Analysis */}
          <div className="inspection-panel right-panel">
            <div className="panel-header">
              <h2>Analysis</h2>
            </div>

            <div className="panel-content">
              {/* Stats Summary */}
              <div className="stats-section">
                <h3>Execution Summary</h3>
                <div className="stats-grid">
                  <div className="stat-card stat-total">
                    <div className="stat-icon">
                      <Activity size={20} />
                    </div>
                    <div className="stat-info">
                      <div className="stat-label">Total Runs</div>
                      <div className="stat-value">{data?.workflows.length || 0}</div>
                    </div>
                  </div>

                  <div className="stat-card stat-passed">
                    <div className="stat-icon">
                      <CheckCircle size={20} />
                    </div>
                    <div className="stat-info">
                      <div className="stat-label">Passed</div>
                      <div className="stat-value">{passedCount}</div>
                    </div>
                  </div>

                  <div className="stat-card stat-failed">
                    <div className="stat-icon">
                      <XCircle size={20} />
                    </div>
                    <div className="stat-info">
                      <div className="stat-label">Failed</div>
                      <div className="stat-value">{failedCount}</div>
                    </div>
                  </div>

                  <div className="stat-card stat-running">
                    <div className="stat-icon">
                      <PlayCircle size={20} />
                    </div>
                    <div className="stat-info">
                      <div className="stat-label">Running</div>
                      <div className="stat-value">{runningCount}</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Execution Details */}
              {selectedWorkflow ? (
                <div className="execution-details-section">
                  <h3>
                    {selectedJobId ? 'Job Details' : 'Execution Details'}
                  </h3>
                  <div className="details-card">
                    {(() => {
                      const execution = executions.find((e) => e.id === selectedWorkflow);
                      if (!execution) return null;

                      // If a job is selected, show job details
                      if (selectedJobId) {
                        const job = execution.jobs.find((j) => j.id === selectedJobId);
                        if (job) {
                          return (
                            <>
                              <div className="detail-row">
                                <span className="detail-label">Workflow</span>
                                <span className="detail-value">{execution.name}</span>
                              </div>
                              <div className="detail-row">
                                <span className="detail-label">Job Name</span>
                                <span className="detail-value font-mono text-sm">{job.name}</span>
                              </div>
                              <div className="detail-row">
                                <span className="detail-label">Job ID</span>
                                <span className="detail-value">{job.id}</span>
                              </div>
                              {job.runner_os && (
                                <div className="detail-row">
                                  <span className="detail-label">Platform</span>
                                  <span className="detail-value">{job.runner_os}</span>
                                </div>
                              )}
                              {job.python_version && (
                                <div className="detail-row">
                                  <span className="detail-label">Python</span>
                                  <span className="detail-value">{job.python_version}</span>
                                </div>
                              )}
                              <div className="detail-row">
                                <span className="detail-label">Status</span>
                                <span className={`status-badge status-${job.result || 'pending'}`}>
                                  {job.result === 'passed' && <CheckCircle size={14} />}
                                  {job.result === 'failed' && <XCircle size={14} />}
                                  {job.status === 'in_progress' && <Clock size={14} />}
                                  {job.result || job.status}
                                </span>
                              </div>
                              <div className="detail-row">
                                <span className="detail-label">Duration</span>
                                <span className="detail-value">{job.duration.toFixed(1)}s</span>
                              </div>
                            </>
                          );
                        }
                      }

                      // Show run details
                      return (
                        <>
                          <div className="detail-row">
                            <span className="detail-label">Workflow</span>
                            <span className="detail-value">{execution.name}</span>
                          </div>
                          <div className="detail-row">
                            <span className="detail-label">Run ID</span>
                            <span className="detail-value">{execution.id}</span>
                          </div>
                          <div className="detail-row">
                            <span className="detail-label">Status</span>
                            <span className={`status-badge status-${execution.result}`}>
                              {execution.result === 'passed' && <CheckCircle size={14} />}
                              {execution.result === 'failed' && <XCircle size={14} />}
                              {execution.status === 'in_progress' && <Clock size={14} />}
                              {execution.result || execution.status}
                            </span>
                          </div>
                          <div className="detail-row">
                            <span className="detail-label">Duration</span>
                            <span className="detail-value">{execution.duration.toFixed(1)}s</span>
                          </div>
                          <div className="detail-row">
                            <span className="detail-label">Started</span>
                            <span className="detail-value">
                              {new Date(execution.started_at).toLocaleString()}
                            </span>
                          </div>
                        </>
                      );
                    })()}
                  </div>
                </div>
              ) : (
                <div className="empty-selection">
                  <Activity size={32} />
                  <p>Select an execution from the left panel to view details</p>
                </div>
              )}

              {/* Two-Panel Layout for Logs and Parsed Data */}
              {selectedExecution && (
                <div className="data-panels-section">
                  {/* Logs Panel */}
                  <div className="data-panel logs-panel">
                    <div className="panel-header-small">
                      <div className="panel-header-left">
                        <button
                          onClick={() => setLogsExpanded(!logsExpanded)}
                          className="collapse-button"
                          title={logsExpanded ? 'Collapse' : 'Expand'}
                        >
                          {logsExpanded ? '[-]' : '[+]'}
                        </button>
                        <h4>
                          <FileText size={16} />
                          Raw Logs
                        </h4>
                      </div>
                      <button
                        onClick={handleFetchLogs}
                        disabled={fetchingLogs || !selectedExecution}
                        className="refresh-button-small"
                        title="Fetch logs from GitHub"
                      >
                        {fetchingLogs ? (
                          <Loader size={14} className="spinning" />
                        ) : (
                          <Download size={14} />
                        )}
                      </button>
                    </div>
                    {logsExpanded && (<div className="panel-body">
                      {!selectedExecution.has_logs && !logContent ? (
                        <div className="empty-panel">
                          <FileText size={32} />
                          <p>No logs available</p>
                          <button
                            onClick={handleFetchLogs}
                            disabled={fetchingLogs}
                            className="fetch-button-small"
                          >
                            {fetchingLogs ? 'Fetching...' : 'Fetch Logs'}
                          </button>
                        </div>
                      ) : fetchingLogs ? (
                        <div className="loading-panel">
                          <Loader size={24} className="spinner" />
                          <span>Fetching logs...</span>
                        </div>
                      ) : logError ? (
                        <div className="error-panel">
                          <XCircle size={24} />
                          <span>{logError}</span>
                          <button onClick={handleFetchLogs} className="retry-button">
                            Retry
                          </button>
                        </div>
                      ) : (
                        <LogViewer content={logContent} loading={false} height="300px" />
                      )}
                    </div>)}
                  </div>

                  {/* Parsed Data Panel */}
                  <div className="data-panel parsed-data-panel">
                    <div className="panel-header-small">
                      <div className="panel-header-left">
                        <button
                          onClick={() => setParsedExpanded(!parsedExpanded)}
                          className="collapse-button"
                          title={parsedExpanded ? 'Collapse' : 'Expand'}
                        >
                          {parsedExpanded ? '[-]' : '[+]'}
                        </button>
                        <h4>
                          <Activity size={16} />
                          Parsed Analysis
                        </h4>
                      </div>
                      <button
                        onClick={handleParseData}
                        disabled={parsingData || (!selectedExecution.has_logs && !logContent)}
                        className="refresh-button-small"
                        title={(selectedExecution.has_logs || logContent) ? "Parse data from logs" : "Fetch logs first"}
                      >
                        {parsingData ? (
                          <Loader size={14} className="spinning" />
                        ) : (
                          <RefreshCw size={14} />
                        )}
                      </button>
                    </div>
                    {parsedExpanded && (<div className="panel-body">
                      {!selectedExecution.has_logs && !logContent ? (
                        <div className="empty-panel disabled">
                          <Activity size={32} />
                          <p>Logs must be fetched first</p>
                          <p className="small-text">Click "Fetch Logs" above to enable parsing</p>
                        </div>
                      ) : !selectedExecution.has_parsed_data && !parsedData ? (
                        <div className="empty-panel">
                          <Activity size={32} />
                          <p>No parsed data available</p>
                          <button
                            onClick={handleParseData}
                            disabled={parsingData}
                            className="fetch-button-small"
                          >
                            {parsingData ? 'Parsing...' : 'Parse Data'}
                          </button>
                        </div>
                      ) : parsingData ? (
                        <div className="loading-panel">
                          <Loader size={24} className="spinner" />
                          <span>Parsing data...</span>
                        </div>
                      ) : parseError ? (
                        <div className="error-panel">
                          <XCircle size={24} />
                          <span>{parseError}</span>
                          <button onClick={handleParseData} className="retry-button">
                            Retry
                          </button>
                        </div>
                      ) : jobParseData ? (
                        <JobParseResultViewer data={jobParseData} />
                      ) : (
                        <ScoutDataViewer data={parsedData} loading={false} height="500px" />
                      )}
                    </div>)}
                  </div>
                </div>
              )}
            </div>
          </div>
        </>
      )}

    </div>
  );
}
