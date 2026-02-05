/**
 * Workflow Timeline Component
 * Displays CI workflow runs in a timeline view
 */

import { Clock, AlertCircle, CheckCircle, PlayCircle, Calendar } from 'lucide-react';
import { useState } from 'react';
import { SeverityBadge } from './index';

interface WorkflowRun {
  id: number;
  run_id: number;
  name: string;
  run_number: number;
  branch: string;
  status: string;
  conclusion: 'success' | 'failure' | 'neutral' | 'cancelled' | null;
  started_at: string;
  completed_at: string | null;
  duration_seconds: number | null;
  url: string;
}

interface Props {
  workflows: WorkflowRun[];
  onSelectWorkflow?: (workflow: WorkflowRun) => void;
  loading?: boolean;
}

/**
 * WorkflowTimeline - Display workflow runs in chronological order
 */
export function WorkflowTimeline({
  workflows,
  onSelectWorkflow,
  loading = false,
}: Props) {
  const [selectedId, setSelectedId] = useState<number | null>(null);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin text-blue-600">
          <Clock size={32} />
        </div>
      </div>
    );
  }

  if (workflows.length === 0) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="mx-auto text-gray-400 mb-2" size={32} />
        <p className="text-gray-600 dark:text-gray-400">
          No workflow runs found. Sync CI data to view runs.
        </p>
      </div>
    );
  }

  // Sort by date (newest first)
  const sorted = [...workflows].sort(
    (a, b) =>
      new Date(b.started_at).getTime() - new Date(a.started_at).getTime()
  );

  return (
    <div className="space-y-4">
      {sorted.map((workflow, index) => (
        <TimelineEntry
          key={workflow.id}
          workflow={workflow}
          isFirst={index === 0}
          isLast={index === sorted.length - 1}
          isSelected={selectedId === workflow.id}
          onSelect={() => {
            setSelectedId(workflow.id);
            onSelectWorkflow?.(workflow);
          }}
        />
      ))}
    </div>
  );
}

interface TimelineEntryProps {
  workflow: WorkflowRun;
  isFirst: boolean;
  isLast: boolean;
  isSelected: boolean;
  onSelect: () => void;
}

/**
 * TimelineEntry - Individual workflow run in timeline
 */
function TimelineEntry({
  workflow,
  isFirst,
  isLast,
  isSelected,
  onSelect,
}: TimelineEntryProps) {
  const isSuccess = workflow.conclusion === 'success';
  const isFailed = workflow.conclusion === 'failure';
  const isCancelled = workflow.conclusion === 'cancelled';
  const isRunning = workflow.status === 'in_progress';

  const statusColor = isSuccess
    ? 'bg-green-500 dark:bg-green-600'
    : isFailed
      ? 'bg-red-500 dark:bg-red-600'
      : isCancelled
        ? 'bg-gray-500 dark:bg-gray-600'
        : 'bg-blue-500 dark:bg-blue-600';

  const statusIcon = isSuccess ? (
    <CheckCircle size={20} />
  ) : isFailed ? (
    <AlertCircle size={20} />
  ) : isRunning ? (
    <PlayCircle size={20} className="animate-pulse" />
  ) : (
    <Circle size={20} />
  );

  const startDate = new Date(workflow.started_at);
  const timeStr = startDate.toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  });
  const dateStr = startDate.toLocaleDateString([], {
    month: 'short',
    day: 'numeric',
  });

  const duration = workflow.duration_seconds
    ? `${Math.round(workflow.duration_seconds / 60)}m ${workflow.duration_seconds % 60}s`
    : 'running';

  return (
    <div
      className={`
        relative p-4 rounded-lg border-2 cursor-pointer transition-all
        ${
          isSelected
            ? 'bg-blue-50 dark:bg-blue-900/30 border-blue-400 dark:border-blue-600'
            : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-500'
        }
      `}
      onClick={onSelect}
    >
      <div className="flex gap-4">
        {/* Timeline dot and line */}
        <div className="flex flex-col items-center pt-1">
          <div className={`w-5 h-5 rounded-full ${statusColor} flex items-center justify-center text-white`}>
            {statusIcon}
          </div>
          {!isLast && (
            <div className="w-1 h-16 bg-gradient-to-b from-current to-gray-300 dark:to-gray-700 mt-2" />
          )}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2 mb-2">
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white truncate">
                {workflow.name} #{workflow.run_number}
              </h3>
              <div className="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-400 mt-1">
                <Calendar size={12} />
                <span>{dateStr} {timeStr}</span>
                {isRunning && (
                  <span className="ml-2 inline-block px-2 py-1 rounded bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-xs">
                    Running
                  </span>
                )}
              </div>
            </div>
            <SeverityBadge
              severity={
                isSuccess
                  ? 'success'
                  : isFailed
                    ? 'error'
                    : isCancelled
                      ? 'warning'
                      : 'info'
              }
              label={workflow.conclusion || workflow.status}
              size="sm"
            />
          </div>

          {/* Details row */}
          <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400">
            <div className="flex gap-4">
              <span>
                <strong>Branch:</strong> {workflow.branch}
              </span>
              <span>
                <strong>Duration:</strong> {duration}
              </span>
            </div>
            <a
              href={workflow.url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="text-blue-600 dark:text-blue-400 hover:underline"
            >
              View on GitHub →
            </a>
          </div>
        </div>
      </div>

      {/* Expansion indicator */}
      {isSelected && (
        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <p className="text-xs text-gray-500 dark:text-gray-500">
            Click to view job details and test results
          </p>
        </div>
      )}
    </div>
  );
}

/**
 * Fallback circle icon
 */
function Circle({ size }: { size: number }) {
  return <div className="w-5 h-5 border-2 border-gray-400 rounded-full" />;
}

export default WorkflowTimeline;
