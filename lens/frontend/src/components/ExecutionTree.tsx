/**
 * ExecutionTree component for displaying CI workflow execution hierarchy
 * Supports expanding runs with jobs and status indicators
 */

import { ChevronDown, ChevronRight, Workflow, Zap, CheckCircle, XCircle, Clock } from 'lucide-react';
import { useState } from 'react';

export interface ExecutionJob {
  id: string;
  name: string;
  status: 'completed' | 'in_progress' | 'queued';
  duration: number;
}

export interface WorkflowExecution {
  id: string;
  name: string;
  status: 'completed' | 'in_progress' | 'queued';
  result: 'passed' | 'failed' | 'pending';
  duration: number;
  started_at: string;
  jobs: ExecutionJob[];
}

interface ExecutionTreeProps {
  executions: WorkflowExecution[];
  onSelectExecution?: (executionId: string) => void;
  selectedExecutionId?: string;
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

function getStatusColor(status: string): string {
  switch (status) {
    case 'completed':
      return 'text-gray-600';
    case 'in_progress':
      return 'text-blue-600 animate-pulse';
    case 'queued':
      return 'text-gray-400';
    default:
      return 'text-gray-400';
  }
}

export function ExecutionTree({
  executions,
  onSelectExecution,
  selectedExecutionId,
  onSelectJob,
}: ExecutionTreeProps) {
  const [expandedExecutions, setExpandedExecutions] = useState<Set<string>>(new Set());

  const toggleExecution = (executionId: string) => {
    const newExpanded = new Set(expandedExecutions);
    if (newExpanded.has(executionId)) {
      newExpanded.delete(executionId);
    } else {
      newExpanded.add(executionId);
    }
    setExpandedExecutions(newExpanded);
  };

  const handleSelectExecution = (executionId: string) => {
    onSelectExecution?.(executionId);
  };

  return (
    <div className="font-mono text-sm space-y-1">
      {executions.map((execution) => (
        <div key={execution.id}>
          {/* Execution Row */}
          <div
            className={`flex items-center gap-2 py-2 px-2 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 rounded ${
              selectedExecutionId === execution.id
                ? 'bg-blue-100 dark:bg-blue-900'
                : ''
            }`}
            onClick={() => {
              toggleExecution(execution.id);
              handleSelectExecution(execution.id);
            }}
          >
            {expandedExecutions.has(execution.id) ? (
              <ChevronDown size={16} className="text-gray-600" />
            ) : (
              <ChevronRight size={16} className="text-gray-600" />
            )}
            {getResultIcon(execution.result)}
            <Workflow size={16} className="text-purple-600" />
            <span className="truncate flex-1 font-semibold">{execution.name}</span>
            <span className="ml-auto text-xs text-gray-500">#{execution.id}</span>
            <span className={`text-xs font-semibold ${getStatusColor(execution.status)}`}>
              {execution.status === 'in_progress' ? '⊙' : '●'}
            </span>
          </div>

          {/* Jobs (when expanded) */}
          {expandedExecutions.has(execution.id) && execution.jobs.length > 0 && (
            <div className="pl-4 space-y-1">
              {execution.jobs.map((job) => (
                <div
                  key={job.id}
                  className="flex items-center gap-2 py-1 px-2 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 rounded"
                  onClick={() => onSelectJob?.(execution.id, job.id)}
                >
                  <Zap size={12} className="text-yellow-600" />
                  <span className="truncate flex-1 text-xs">{job.name}</span>
                  <span className="text-xs text-gray-500">{job.duration.toFixed(1)}s</span>
                  <span className={`text-xs font-semibold ${getStatusColor(job.status)}`}>
                    {job.status === 'in_progress' ? '▶' : '■'}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      ))}

      {executions.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <Workflow size={32} className="mx-auto mb-2 opacity-50" />
          <p>No executions found</p>
          <p className="text-xs">Run &quot;scout ci sync&quot; to populate data</p>
        </div>
      )}
    </div>
  );
}
