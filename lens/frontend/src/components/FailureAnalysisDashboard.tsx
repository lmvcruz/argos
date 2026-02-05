/**
 * Failure Analysis Dashboard Component
 * Displays failure patterns, frequency, and trending
 */

import { AlertTriangle, TrendingUp, BarChart3, AlertCircle } from 'lucide-react';
import { useState, useEffect } from 'react';

interface FailureData {
  test: string;
  count: number;
  recent_errors: Array<{
    error_message: string;
    timestamp: string;
  }>;
}

interface FailureAnalytics {
  period_days: number;
  total_failures: number;
  unique_failing_tests: number;
  top_failures: FailureData[];
}

/**
 * FailureAnalysisDashboard - Display failure patterns and analysis
 */
export function FailureAnalysisDashboard() {
  const [analytics, setAnalytics] = useState<FailureAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState(7);
  const [selectedTest, setSelectedTest] = useState<string | null>(null);

  useEffect(() => {
    fetchFailureAnalytics();
  }, [period]);

  const fetchFailureAnalytics = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/scout/analytics/failures?days=${period}&limit=20`);
      if (!response.ok) throw new Error('Failed to fetch failure analytics');
      const data = await response.json();
      setAnalytics(data);
    } catch (error) {
      console.error('Failed to fetch failure analytics:', error);
      setAnalytics(null);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin text-blue-600 mb-2">
            <AlertTriangle size={32} />
          </div>
          <p className="text-gray-600 dark:text-gray-400">Loading failure analysis...</p>
        </div>
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="mx-auto text-gray-400 mb-2" size={32} />
        <p className="text-gray-600 dark:text-gray-400">
          Unable to load failure analytics
        </p>
      </div>
    );
  }

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
        </select>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <AnalyticsCard
          icon={<AlertTriangle className="text-red-600" size={24} />}
          label="Total Failures"
          value={analytics.total_failures}
          color="red"
        />
        <AnalyticsCard
          icon={<BarChart3 className="text-blue-600" size={24} />}
          label="Unique Failing Tests"
          value={analytics.unique_failing_tests}
          color="blue"
        />
        <AnalyticsCard
          icon={<TrendingUp className="text-orange-600" size={24} />}
          label="Analysis Period"
          value={`${analytics.period_days} days`}
          color="orange"
        />
      </div>

      {/* Failure Frequency Chart (Text-based) */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="font-semibold text-lg mb-4">Most Frequent Failures</h3>

        {analytics.top_failures.length > 0 ? (
          <div className="space-y-4">
            {analytics.top_failures.map((failure, idx) => (
              <div key={idx}>
                <div className="flex items-start justify-between gap-4 mb-2">
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-900 dark:text-white truncate">
                      {failure.test}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      Failed {failure.count} time{failure.count !== 1 ? 's' : ''}
                    </p>
                  </div>
                  <button
                    onClick={() =>
                      setSelectedTest(selectedTest === failure.test ? null : failure.test)
                    }
                    className="px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded transition-colors whitespace-nowrap"
                  >
                    {selectedTest === failure.test ? 'Hide' : 'View'} Details
                  </button>
                </div>

                {/* Progress bar showing failure frequency */}
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 mb-2">
                  <div
                    className="bg-red-500 dark:bg-red-600 h-2 rounded-full"
                    style={{
                      width: `${
                        (failure.count /
                          (analytics.top_failures[0]?.count || 1)) *
                        100
                      }%`,
                    }}
                  />
                </div>

                {/* Expanded details */}
                {selectedTest === failure.test && (
                  <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700 space-y-3">
                    <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      Recent Errors:
                    </p>
                    {failure.recent_errors.length > 0 ? (
                      <div className="space-y-2">
                        {failure.recent_errors.map((error, errIdx) => (
                          <div
                            key={errIdx}
                            className="bg-red-50 dark:bg-red-900/20 p-3 rounded text-sm"
                          >
                            <p className="text-red-900 dark:text-red-200 mb-1">
                              {error.error_message}
                            </p>
                            <p className="text-xs text-red-700 dark:text-red-400">
                              {new Date(error.timestamp).toLocaleString()}
                            </p>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        No error details available
                      </p>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <p className="text-gray-600 dark:text-gray-400">
              No failures detected in this period
            </p>
          </div>
        )}
      </div>

      {/* Insights */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <h4 className="font-semibold text-blue-900 dark:text-blue-200 mb-2">Insights</h4>
        <ul className="space-y-1 text-sm text-blue-800 dark:text-blue-300">
          {analytics.total_failures === 0 ? (
            <li>✓ No failures detected in the last {analytics.period_days} days</li>
          ) : (
            <>
              <li>
                • {analytics.unique_failing_tests} test{analytics.unique_failing_tests !== 1 ? 's' : ''} failing consistently
              </li>
              <li>
                • Average failure rate:{' '}
                {Math.round(
                  analytics.total_failures / (analytics.unique_failing_tests || 1)
                )}{' '}
                failures per test
              </li>
              {analytics.top_failures.length > 0 && (
                <li>
                  • Top failure:{' '}
                  <strong>{analytics.top_failures[0]?.test.split('::').pop()}</strong>{' '}
                  ({analytics.top_failures[0]?.count} failures)
                </li>
              )}
            </>
          )}
        </ul>
      </div>
    </div>
  );
}

/**
 * AnalyticsCard - Summary metric card
 */
function AnalyticsCard({
  icon,
  label,
  value,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  color: 'red' | 'blue' | 'orange';
}) {
  const bgColorMap = {
    red: 'bg-red-50 dark:bg-red-900/20',
    blue: 'bg-blue-50 dark:bg-blue-900/20',
    orange: 'bg-yellow-50 dark:bg-yellow-900/20',
  };

  return (
    <div className={`${bgColorMap[color]} rounded-lg border border-gray-200 dark:border-gray-700 p-4`}>
      <div className="flex items-start gap-3">
        <div className="mt-1">{icon}</div>
        <div>
          <p className="text-sm text-gray-600 dark:text-gray-400">{label}</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{value}</p>
        </div>
      </div>
    </div>
  );
}

export default FailureAnalysisDashboard;
