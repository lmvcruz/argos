/**
 * ExecutionTree component for displaying CI workflow execution hierarchy
 * Supports expanding runs with jobs and status indicators
 */

import { ChevronDown, ChevronRight, Workflow, Zap, CheckCircle, XCircle, Clock } from 'lucide-react';
import { useState } from 'react';
import { scoutClient } from '../api/tools';

export interface ExecutionJob {
  id: string;
  name: string;
  status: 'completed' | 'in_progress' | 'queued';
  result?: 'passed' | 'failed' | 'pending';
  duration: number;
  runner_os?: string;
  python_version?: string;
}

export interface WorkflowExecution {
  id: string;
  name: string;
  status: 'completed' | 'in_progress' | 'queued';
  result: 'passed' | 'failed' | 'pending';
  duration: number;
  started_at: string;
  jobs: ExecutionJob[];
  has_logs?: boolean;
  has_parsed_data?: boolean;
}

interface ExecutionTreeProps {
  executions: WorkflowExecution[];
  onSelectExecution?: (executionId: string) => void;
  selectedExecutionId?: string;
  selectedJobId?: string;
  onSelectJob?: (executionId: string, jobId: string) => void;
}

function getResultIcon(result: string) {
  switch (result) {
    case 'passed':
      return <CheckCircle size={16} className="text-green-600" />;
    case 'failed':
      return <XCircle size={16} className="text-red-600" />;
    default:
      return <Clock size={16} className="text-gray-400" />;
  }
}



export function ExecutionTree({
  executions,
  onSelectExecution,
  selectedExecutionId,
  selectedJobId,
  onSelectJob,
}: ExecutionTreeProps) {
  const [expandedExecutions, setExpandedExecutions] = useState<Set<string>>(new Set());
  const [loadingJobs, setLoadingJobs] = useState<Set<string>>(new Set());
  const [jobsCache, setJobsCache] = useState<Map<string, ExecutionJob[]>>(new Map());

  const toggleExecution = async (executionId: string) => {
    const newExpanded = new Set(expandedExecutions);

    if (newExpanded.has(executionId)) {
      // Collapse
      newExpanded.delete(executionId);
      setExpandedExecutions(newExpanded);
    } else {
      // Expand - fetch jobs if not cached
      newExpanded.add(executionId);
      setExpandedExecutions(newExpanded);

      if (!jobsCache.has(executionId)) {
        setLoadingJobs(new Set(loadingJobs).add(executionId));
        try {
          const runId = parseInt(executionId);
          const jobsData = await scoutClient.getRunJobs(runId);
          const newCache = new Map(jobsCache);
          // Map job data to ExecutionJob format with proper type casting
          const mappedJobs = jobsData.jobs.map((job): ExecutionJob => ({
            id: job.id,
            name: job.name,
            status: job.status as 'completed' | 'in_progress' | 'queued',
            result: job.result as 'passed' | 'failed' | 'pending',
            duration: job.duration,
            runner_os: job.runner_os,
            python_version: job.python_version,
          }));
          newCache.set(executionId, mappedJobs);
          setJobsCache(newCache);
        } catch (error) {
          console.error(`Failed to load jobs for execution ${executionId}:`, error);
        } finally {
          const newLoading = new Set(loadingJobs);
          newLoading.delete(executionId);
          setLoadingJobs(newLoading);
        }
      }
    }
  };

  const handleSelectExecution = (executionId: string) => {
    onSelectExecution?.(executionId);
  };

  return (
    <div className="execution-tree-modern space-y-2">
      {executions.map((execution) => {
        const isExpanded = expandedExecutions.has(execution.id);
        const jobs = jobsCache.get(execution.id) || [];
        const isLoadingJobs = loadingJobs.has(execution.id);

        return (
          <div key={execution.id} className="execution-card">
            {/* Execution Row */}
            <div
              className={`execution-row ${
                selectedExecutionId === execution.id
                  ? 'execution-row-selected'
                  : ''
              }`}
            >
              {/* Expand/Collapse Button */}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  toggleExecution(execution.id);
                }}
                className="execution-expand-button"
                title={isExpanded ? 'Collapse' : 'Expand to see jobs'}
              >
                {isExpanded ? (
                  <ChevronDown size={16} />
                ) : (
                  <ChevronRight size={16} />
                )}
              </button>

              <div
                className="execution-row-left"
                onClick={() => handleSelectExecution(execution.id)}
              >
                <div className="execution-status-icon">
                  {getResultIcon(execution.result)}
                </div>
                <Workflow size={18} className="execution-workflow-icon" />
                <div className="execution-info">
                  <span className="execution-name">{execution.name}</span>
                  <span className="execution-id">#{execution.id}</span>
                </div>
              </div>
              <div className="execution-row-right">
                <span className="execution-duration">{execution.duration.toFixed(1)}s</span>
                <span className={`execution-status-badge status-${execution.result}`}>
                  {execution.result}
                </span>
              </div>
            </div>

            {/* Jobs (when expanded) */}
            {isExpanded && (
              <div className="jobs-list">
                {isLoadingJobs ? (
                  <div className="job-row text-gray-500">
                    <span>Loading jobs...</span>
                  </div>
                ) : jobs.length > 0 ? (
                  jobs.map((job) => (
                    <div
                      key={job.id}
                      className={`job-row ${selectedJobId === job.id ? 'job-row-selected' : ''}`}
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectJob?.(execution.id, job.id);
                      }}
                    >
                      <Zap size={14} className="job-icon" />
                      <div className="job-info">
                        <span className="job-name">{job.name}</span>
                        {(job.runner_os || job.python_version) && (
                          <span className="job-details">
                            {job.runner_os && <span>{job.runner_os}</span>}
                            {job.python_version && (
                              <span className="ml-2">Python {job.python_version}</span>
                            )}
                          </span>
                        )}
                      </div>
                      <span className="job-duration">{job.duration?.toFixed(1) || '0'}s</span>
                      <span className={`job-status ${job.result ? `status-${job.result}` : ''}`}>
                        {job.result === 'passed' ? '✓' : job.result === 'failed' ? '✗' : '○'}
                      </span>
                    </div>
                  ))
                ) : (
                  <div className="job-row text-gray-500">
                    <span>No jobs found</span>
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}

      {executions.length === 0 && (
        <div className="empty-executions">
          <Workflow size={40} className="empty-icon" />
          <p className="empty-title">No executions found</p>
          <p className="empty-subtitle">Refresh to fetch workflow data from GitHub</p>
        </div>
      )}
    </div>
  );
}
