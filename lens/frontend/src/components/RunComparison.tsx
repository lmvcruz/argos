/**
 * Run Comparison Component
 * Side-by-side comparison of two CI workflow runs to detect regressions
 */

import {
  ArrowRight,
  TrendingDown,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Clock,
} from 'lucide-react';
import { useState } from 'react';
import { SeverityBadge } from './index';

interface WorkflowRun {
  id: number;
  run_number: number;
  conclusion: 'success' | 'failure' | 'neutral' | 'cancelled' | null;
  duration_seconds: number | null;
  started_at: string;
}

interface JobComparison {
  job_name: string;
  duration_1: number | null;
  duration_2: number | null;
  status_1: string;
  status_2: string;
  status_changed: boolean;
  duration_improved: boolean;
  duration_delta: number;
}

interface Props {
  workflows: WorkflowRun[];
  onComparisonComplete?: (result: ComparisonResult) => void;
}

interface ComparisonResult {
  workflow_1: WorkflowRun;
  workflow_2: WorkflowRun;
  jobs: JobComparison[];
  duration_delta: number;
  regressions_detected: boolean;
}

/**
 * RunComparison - Compare two workflow runs side-by-side
 */
export function RunComparison({ workflows, onComparisonComplete }: Props) {
  const [selectedRun1, setSelectedRun1] = useState<number | null>(null);
  const [selectedRun2, setSelectedRun2] = useState<number | null>(null);
  const [comparison, setComparison] = useState<ComparisonResult | null>(null);

  const handleCompare = async () => {
    if (!selectedRun1 || !selectedRun2) return;

    const run1 = workflows.find((w) => w.id === selectedRun1);
    const run2 = workflows.find((w) => w.id === selectedRun2);

    if (!run1 || !run2) return;

    try {
      // Fetch comparison from backend
      const response = await fetch(
        `/api/scout/workflows/${selectedRun1}/compare/${selectedRun2}`
      );
      if (!response.ok) throw new Error('Failed to compare runs');

      const data = await response.json();

      // Transform backend response to our format
      const jobs: JobComparison[] = (data.job_details || []).map(
        (job: any) => ({
          job_name: `Job ${job.job_id}`,
          duration_1: job.job_1_duration,
          duration_2: job.job_2_duration,
          status_1: job.status_change[0],
          status_2: job.status_change[1],
          status_changed: job.status_change[0] !== job.status_change[1],
          duration_improved: (job.job_2_duration || 0) < (job.job_1_duration || 0),
          duration_delta: job.duration_delta,
        })
      );

      const result: ComparisonResult = {
        workflow_1: run1,
        workflow_2: run2,
        jobs,
        duration_delta: data.duration_delta || 0,
        regressions_detected: jobs.some((j) => j.status_changed && !j.duration_improved),
      };

      setComparison(result);
      onComparisonComplete?.(result);
    } catch (error) {
      console.error('Failed to compare runs:', error);
    }
  };

  if (!workflows || workflows.length < 2) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="mx-auto text-gray-400 mb-2" size={32} />
        <p className="text-gray-600 dark:text-gray-400">
          Need at least 2 workflow runs to compare
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Comparison Selector */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="font-semibold text-lg mb-4">Select Runs to Compare</h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
          {/* Run 1 Selector */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              First Run
            </label>
            <select
              value={selectedRun1 || ''}
              onChange={(e) => setSelectedRun1(parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="">Select a run...</option>
              {workflows.map((w) => (
                <option key={w.id} value={w.id}>
                  Run #{w.run_number} ({formatDate(w.started_at)})
                </option>
              ))}
            </select>
          </div>

          {/* Arrow Icon */}
          <div className="flex justify-center">
            <ArrowRight className="text-gray-400" size={24} />
          </div>

          {/* Run 2 Selector */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Second Run
            </label>
            <select
              value={selectedRun2 || ''}
              onChange={(e) => setSelectedRun2(parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="">Select a run...</option>
              {workflows.map((w) => (
                <option key={w.id} value={w.id}>
                  Run #{w.run_number} ({formatDate(w.started_at)})
                </option>
              ))}
            </select>
          </div>
        </div>

        <button
          onClick={handleCompare}
          disabled={!selectedRun1 || !selectedRun2}
          className="mt-4 px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition-colors"
        >
          Compare Runs
        </button>
      </div>

      {/* Comparison Results */}
      {comparison && <ComparisonResults result={comparison} />}
    </div>
  );
}

/**
 * ComparisonResults - Display comparison results
 */
function ComparisonResults({ result }: { result: ComparisonResult }) {
  const regressionCount = result.jobs.filter(
    (j) => j.status_changed && j.status_2 === 'failure'
  ).length;
  const improvementCount = result.jobs.filter(
    (j) => j.status_changed && j.status_2 === 'success'
  ).length;

  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <ComparisonSummaryCard
          icon={
            result.regressions_detected ? (
              <TrendingDown className="text-red-600" size={24} />
            ) : (
              <TrendingUp className="text-green-600" size={24} />
            )
          }
          label="Status"
          value={result.regressions_detected ? 'Regression Detected' : 'No Regressions'}
          color={result.regressions_detected ? 'red' : 'green'}
        />

        <ComparisonSummaryCard
          icon={<Clock className="text-blue-600" size={24} />}
          label="Duration Change"
          value={
            result.duration_delta > 0
              ? `+${Math.round(result.duration_delta)}s slower`
              : `${Math.round(Math.abs(result.duration_delta))}s faster`
          }
          color={result.duration_delta > 0 ? 'orange' : 'green'}
        />

        <ComparisonSummaryCard
          icon={<AlertCircle className="text-blue-600" size={24} />}
          label="Job Changes"
          value={`${regressionCount} failed, ${improvementCount} fixed`}
          color="blue"
        />
      </div>

      {/* Job Comparison Table */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="font-semibold text-lg">Job Comparison</h3>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
              <tr>
                <th className="px-6 py-3 text-left font-semibold text-gray-700 dark:text-gray-300">
                  Job
                </th>
                <th className="px-6 py-3 text-left font-semibold text-gray-700 dark:text-gray-300">
                  Run 1 Status
                </th>
                <th className="px-6 py-3 text-left font-semibold text-gray-700 dark:text-gray-300">
                  Run 2 Status
                </th>
                <th className="px-6 py-3 text-left font-semibold text-gray-700 dark:text-gray-300">
                  Duration
                </th>
                <th className="px-6 py-3 text-left font-semibold text-gray-700 dark:text-gray-300">
                  Change
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {result.jobs.map((job, idx) => (
                <tr
                  key={idx}
                  className={
                    job.status_changed
                      ? 'bg-red-50 dark:bg-red-900/20'
                      : 'hover:bg-gray-50 dark:hover:bg-gray-700/50'
                  }
                >
                  <td className="px-6 py-4 font-medium text-gray-900 dark:text-white">
                    {job.job_name}
                  </td>
                  <td className="px-6 py-4">
                    <StatusBadge status={job.status_1} />
                  </td>
                  <td className="px-6 py-4">
                    <StatusBadge status={job.status_2} />
                  </td>
                  <td className="px-6 py-4 text-gray-600 dark:text-gray-400">
                    {job.duration_1 ? `${job.duration_1}s` : '-'} →{' '}
                    {job.duration_2 ? `${job.duration_2}s` : '-'}
                  </td>
                  <td className="px-6 py-4">
                    {job.status_changed ? (
                      <span className="inline-flex items-center gap-1 px-2 py-1 rounded bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 text-xs font-medium">
                        <AlertCircle size={14} />
                        Changed
                      </span>
                    ) : job.duration_improved ? (
                      <span className="inline-flex items-center gap-1 px-2 py-1 rounded bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 text-xs font-medium">
                        <TrendingDown size={14} />
                        Faster
                      </span>
                    ) : job.duration_delta > 0 ? (
                      <span className="inline-flex items-center gap-1 px-2 py-1 rounded bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300 text-xs font-medium">
                        <TrendingUp size={14} />
                        Slower
                      </span>
                    ) : (
                      <span className="text-gray-500 dark:text-gray-400 text-xs">
                        No change
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

/**
 * ComparisonSummaryCard - Summary metric card
 */
function ComparisonSummaryCard({
  icon,
  label,
  value,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  color: 'red' | 'green' | 'blue' | 'orange';
}) {
  const bgColorMap = {
    red: 'bg-red-50 dark:bg-red-900/20',
    green: 'bg-green-50 dark:bg-green-900/20',
    blue: 'bg-blue-50 dark:bg-blue-900/20',
    orange: 'bg-yellow-50 dark:bg-yellow-900/20',
  };

  return (
    <div className={`${bgColorMap[color]} rounded-lg border border-gray-200 dark:border-gray-700 p-4`}>
      <div className="flex items-start gap-3">
        <div className="mt-1">{icon}</div>
        <div>
          <p className="text-sm text-gray-600 dark:text-gray-400">{label}</p>
          <p className="text-lg font-semibold text-gray-900 dark:text-white">{value}</p>
        </div>
      </div>
    </div>
  );
}

/**
 * StatusBadge - Status indicator
 */
function StatusBadge({ status }: { status: string }) {
  const severityMap: Record<string, any> = {
    success: 'success',
    failure: 'error',
    neutral: 'warning',
    cancelled: 'warning',
  };

  return (
    <SeverityBadge
      severity={severityMap[status] || 'info'}
      label={status}
      size="sm"
    />
  );
}

/**
 * Format date for display
 */
function formatDate(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

export default RunComparison;
