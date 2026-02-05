/**
 * Performance Trending Chart Component
 * Displays workflow performance metrics and trends over time
 */

import { TrendingUp, TrendingDown, Clock, AlertCircle, BarChart3 } from 'lucide-react';
import { useState, useEffect } from 'react';

interface PerformanceData {
  period_days: number;
  workflow_count: number;
  avg_duration: number;
  min_duration: number;
  max_duration: number;
  durations: number[];
  trend: 'increasing' | 'decreasing' | 'stable' | 'no_data' | 'insufficient_data';
  trend_percentage: number;
}

/**
 * PerformanceTrendingChart - Display performance metrics and trends
 */
export function PerformanceTrendingChart() {
  const [data, setData] = useState<PerformanceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState(30);

  useEffect(() => {
    fetchPerformanceData();
  }, [period]);

  const fetchPerformanceData = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/scout/analytics/performance?days=${period}`);
      if (!response.ok) throw new Error('Failed to fetch performance data');
      const data = await response.json();
      setData(data);
    } catch (error) {
      console.error('Failed to fetch performance data:', error);
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin text-blue-600 mb-2">
            <BarChart3 size={32} />
          </div>
          <p className="text-gray-600 dark:text-gray-400">Loading performance data...</p>
        </div>
      </div>
    );
  }

  if (!data || data.workflow_count === 0) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="mx-auto text-gray-400 mb-2" size={32} />
        <p className="text-gray-600 dark:text-gray-400">
          No performance data available
        </p>
      </div>
    );
  }

  const getTrendIcon = () => {
    switch (data.trend) {
      case 'increasing':
        return <TrendingUp className="text-red-600" size={24} />;
      case 'decreasing':
        return <TrendingDown className="text-green-600" size={24} />;
      default:
        return <BarChart3 className="text-blue-600" size={24} />;
    }
  };

  const getTrendColor = () => {
    switch (data.trend) {
      case 'increasing':
        return 'red';
      case 'decreasing':
        return 'green';
      default:
        return 'blue';
    }
  };

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex items-center gap-4">
        <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
          Period:
        </label>
        <select
          value={period}
          onChange={(e) => setPeriod(parseInt(e.target.value))}
          className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
        >
          <option value={7}>Last 7 days</option>
          <option value={14}>Last 14 days</option>
          <option value={30}>Last 30 days</option>
          <option value={60}>Last 60 days</option>
        </select>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          icon={<Clock className="text-blue-600" size={24} />}
          label="Average Duration"
          value={`${Math.round(data.avg_duration)}s`}
          subtext="Avg across all runs"
          color="blue"
        />
        <MetricCard
          icon={<TrendingDown className="text-green-600" size={24} />}
          label="Fastest Run"
          value={`${Math.round(data.min_duration)}s`}
          subtext="Best performance"
          color="green"
        />
        <MetricCard
          icon={<TrendingUp className="text-orange-600" size={24} />}
          label="Slowest Run"
          value={`${Math.round(data.max_duration)}s`}
          subtext="Worst performance"
          color="orange"
        />
        <MetricCard
          icon={getTrendIcon()}
          label="Trend"
          value={getTrendValue(data.trend)}
          subtext={`${data.trend_percentage > 0 ? '+' : ''}${data.trend_percentage}% change`}
          color={getTrendColor() as 'red' | 'green' | 'blue' | 'orange'}
        />
      </div>

      {/* Performance Distribution Chart */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="font-semibold text-lg mb-4">Duration Distribution</h3>

        {data.durations && data.durations.length > 0 ? (
          <div className="space-y-4">
            {/* Simple histogram using bars */}
            <PerformanceHistogram durations={data.durations} />

            {/* Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
              <div>
                <p className="text-xs text-gray-600 dark:text-gray-400">Min</p>
                <p className="text-lg font-semibold text-gray-900 dark:text-white">
                  {Math.round(data.min_duration)}s
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-600 dark:text-gray-400">25th %ile</p>
                <p className="text-lg font-semibold text-gray-900 dark:text-white">
                  {Math.round(percentile(data.durations, 25))}s
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-600 dark:text-gray-400">Median</p>
                <p className="text-lg font-semibold text-gray-900 dark:text-white">
                  {Math.round(percentile(data.durations, 50))}s
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-600 dark:text-gray-400">Max</p>
                <p className="text-lg font-semibold text-gray-900 dark:text-white">
                  {Math.round(data.max_duration)}s
                </p>
              </div>
            </div>
          </div>
        ) : (
          <p className="text-gray-600 dark:text-gray-400">No duration data available</p>
        )}
      </div>

      {/* Insights & Recommendations */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <h4 className="font-semibold text-blue-900 dark:text-blue-200 mb-2">
          Performance Insights
        </h4>
        <ul className="space-y-1 text-sm text-blue-800 dark:text-blue-300">
          {data.trend === 'increasing' && (
            <li>
              ⚠️ Performance is degrading - workflows are getting slower{' '}
              <strong>({data.trend_percentage}%)</strong>. Investigate recent changes.
            </li>
          )}
          {data.trend === 'decreasing' && (
            <li>
              ✓ Performance is improving - workflows are getting faster{' '}
              <strong>({Math.abs(data.trend_percentage)}%)</strong>. Great optimization!
            </li>
          )}
          {data.trend === 'stable' && (
            <li>
              ✓ Performance is stable - no significant changes detected in workflow duration.
            </li>
          )}

          <li>
            • Workflow duration ranges from <strong>{Math.round(data.min_duration)}s</strong> to{' '}
            <strong>{Math.round(data.max_duration)}s</strong>
          </li>

          {data.max_duration > data.avg_duration * 1.5 && (
            <li>
              • Performance variance is high. Investigate outliers causing slowdowns.
            </li>
          )}

          <li>• Analysis based on {data.workflow_count} workflow runs</li>
        </ul>
      </div>
    </div>
  );
}

/**
 * PerformanceHistogram - Visual histogram of durations
 */
function PerformanceHistogram({ durations }: { durations: number[] }) {
  const buckets = 10;
  const min = Math.min(...durations);
  const max = Math.max(...durations);
  const bucketSize = (max - min) / buckets || 1;

  // Create histogram buckets
  const histogram = Array(buckets).fill(0);
  durations.forEach((duration) => {
    const bucketIndex = Math.min(
      Math.floor((duration - min) / bucketSize),
      buckets - 1
    );
    histogram[bucketIndex]++;
  });

  const maxCount = Math.max(...histogram);

  return (
    <div className="space-y-2">
      {histogram.map((count, idx) => {
        const bucketMin = Math.round(min + idx * bucketSize);
        const bucketMax = Math.round(min + (idx + 1) * bucketSize);
        const percentage = (count / maxCount) * 100;

        return (
          <div key={idx}>
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="text-gray-600 dark:text-gray-400">
                {bucketMin}s - {bucketMax}s
              </span>
              <span className="text-gray-600 dark:text-gray-400">{count} runs</span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div
                className="bg-blue-500 dark:bg-blue-600 h-2 rounded-full transition-all"
                style={{ width: `${percentage}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

/**
 * MetricCard - Performance metric display
 */
function MetricCard({
  icon,
  label,
  value,
  subtext,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  subtext: string;
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
          <p className="text-xl font-bold text-gray-900 dark:text-white">{value}</p>
          <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">{subtext}</p>
        </div>
      </div>
    </div>
  );
}

/**
 * Calculate percentile of an array
 */
function percentile(arr: number[], p: number): number {
  if (arr.length === 0) return 0;
  const sorted = [...arr].sort((a, b) => a - b);
  const index = Math.ceil((p / 100) * sorted.length) - 1;
  return sorted[Math.max(0, index)];
}

/**
 * Get human-readable trend value
 */
function getTrendValue(trend: string): string {
  switch (trend) {
    case 'increasing':
      return 'Getting Slower';
    case 'decreasing':
      return 'Getting Faster';
    case 'stable':
      return 'Stable';
    case 'no_data':
      return 'No Data';
    case 'insufficient_data':
      return 'Insufficient Data';
    default:
      return 'Unknown';
  }
}

export default PerformanceTrendingChart;
