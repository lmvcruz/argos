/**
 * TestStatistics - Historical test statistics and trends.
 *
 * Displays historical test execution data from database including
 * pass rates, failure trends, and execution time statistics.
 */

import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Calendar, BarChart3, Loader } from 'lucide-react';

export interface TestStats {
  date: string;
  totalTests: number;
  passedTests: number;
  failedTests: number;
  skippedTests: number;
  averageDuration: number;
  totalDuration: number;
  passRate: number;
}

export interface TestStatisticsProps {
  onLoadStats?: () => Promise<TestStats[]>;
  isLoading?: boolean;
}

/**
 * TestStatistics component - Historical test data and trends.
 *
 * Shows test execution statistics from the database including:
 * - Pass rates over time
 * - Failure trends
 * - Average execution duration
 * - Test count evolution
 *
 * Args:
 *   onLoadStats: Async callback to fetch statistics from database
 *   isLoading: External loading state
 */
export const TestStatistics: React.FC<TestStatisticsProps> = ({
  onLoadStats,
  isLoading = false,
}) => {
  const [stats, setStats] = useState<TestStats[]>([]);
  const [loading, setLoading] = useState(false);
  const [timeframe, setTimeframe] = useState<'week' | 'month' | 'all'>('week');

  useEffect(() => {
    const loadStatistics = async () => {
      if (!onLoadStats) return;

      setLoading(true);
      try {
        const data = await onLoadStats();
        setStats(data);
      } catch (error) {
        console.error('Failed to load statistics:', error);
      } finally {
        setLoading(false);
      }
    };

    loadStatistics();
  }, [onLoadStats]);

  if (loading || isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader size={20} className="animate-spin text-gray-400" />
      </div>
    );
  }

  // Calculate aggregate stats
  const latestStats = stats[stats.length - 1];
  const previousStats = stats.length > 1 ? stats[stats.length - 2] : null;

  const passRateTrend =
    previousStats && latestStats
      ? latestStats.passRate - previousStats.passRate
      : 0;

  const failuresTrend =
    previousStats && latestStats
      ? latestStats.failedTests - previousStats.failedTests
      : 0;

  const durationTrend =
    previousStats && latestStats
      ? latestStats.averageDuration - previousStats.averageDuration
      : 0;

  return (
    <div className="space-y-4">
      {/* Timeframe Selector */}
      <div className="flex gap-2 pb-3 border-b border-gray-200 dark:border-gray-700">
        {(['week', 'month', 'all'] as const).map((tf) => (
          <button
            key={tf}
            onClick={() => setTimeframe(tf)}
            className={`px-3 py-1 text-sm rounded transition-colors ${
              timeframe === tf
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
            }`}
          >
            {tf === 'week' ? 'This Week' : tf === 'month' ? 'This Month' : 'All Time'}
          </button>
        ))}
      </div>

      {stats.length > 0 && latestStats ? (
        <>
          {/* Key Metrics */}
          <div className="grid grid-cols-2 gap-3">
            {/* Pass Rate */}
            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-green-700 dark:text-green-300">
                  Pass Rate
                </span>
                {passRateTrend !== 0 && (
                  <div className="flex items-center gap-1">
                    {passRateTrend > 0 ? (
                      <TrendingUp size={12} className="text-green-600 dark:text-green-400" />
                    ) : (
                      <TrendingDown size={12} className="text-red-600 dark:text-red-400" />
                    )}
                    <span className={`text-xs font-medium ${passRateTrend > 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                      {passRateTrend > 0 ? '+' : ''}{passRateTrend.toFixed(1)}%
                    </span>
                  </div>
                )}
              </div>
              <div className="text-2xl font-bold text-green-700 dark:text-green-300">
                {latestStats.passRate.toFixed(1)}%
              </div>
              <div className="text-xs text-green-600 dark:text-green-400 mt-1">
                {latestStats.passedTests} passed
              </div>
            </div>

            {/* Failed Tests */}
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-red-700 dark:text-red-300">
                  Failed Tests
                </span>
                {failuresTrend !== 0 && (
                  <div className="flex items-center gap-1">
                    {failuresTrend < 0 ? (
                      <TrendingDown size={12} className="text-green-600 dark:text-green-400" />
                    ) : (
                      <TrendingUp size={12} className="text-red-600 dark:text-red-400" />
                    )}
                    <span className={`text-xs font-medium ${failuresTrend < 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                      {failuresTrend > 0 ? '+' : ''}{failuresTrend}
                    </span>
                  </div>
                )}
              </div>
              <div className="text-2xl font-bold text-red-700 dark:text-red-300">
                {latestStats.failedTests}
              </div>
              <div className="text-xs text-red-600 dark:text-red-400 mt-1">
                of {latestStats.totalTests} total
              </div>
            </div>

            {/* Avg Duration */}
            <div className="bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-purple-700 dark:text-purple-300">
                  Avg Duration
                </span>
                {durationTrend !== 0 && (
                  <div className="flex items-center gap-1">
                    {durationTrend < 0 ? (
                      <TrendingDown size={12} className="text-green-600 dark:text-green-400" />
                    ) : (
                      <TrendingUp size={12} className="text-red-600 dark:text-red-400" />
                    )}
                    <span className={`text-xs font-medium ${durationTrend < 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                      {durationTrend > 0 ? '+' : ''}{durationTrend.toFixed(0)}ms
                    </span>
                  </div>
                )}
              </div>
              <div className="text-2xl font-bold text-purple-700 dark:text-purple-300">
                {latestStats.averageDuration.toFixed(0)}ms
              </div>
              <div className="text-xs text-purple-600 dark:text-purple-400 mt-1">
                per test
              </div>
            </div>

            {/* Total Tests */}
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-blue-700 dark:text-blue-300">
                  Total Tests
                </span>
                <BarChart3 size={14} className="text-blue-600 dark:text-blue-400" />
              </div>
              <div className="text-2xl font-bold text-blue-700 dark:text-blue-300">
                {latestStats.totalTests}
              </div>
              <div className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                {latestStats.skippedTests} skipped
              </div>
            </div>
          </div>

          {/* Historical Data Table */}
          {stats.length > 1 && (
            <div className="mt-4">
              <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-2 flex items-center gap-2">
                <Calendar size={14} />
                History
              </h4>
              <div className="max-h-48 overflow-y-auto border border-gray-200 dark:border-gray-700 rounded">
                <table className="w-full text-xs">
                  <thead className="bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0">
                    <tr>
                      <th className="text-left px-3 py-2 font-semibold text-gray-700 dark:text-gray-300">
                        Date
                      </th>
                      <th className="text-right px-3 py-2 font-semibold text-gray-700 dark:text-gray-300">
                        Pass %
                      </th>
                      <th className="text-right px-3 py-2 font-semibold text-gray-700 dark:text-gray-300">
                        Failed
                      </th>
                      <th className="text-right px-3 py-2 font-semibold text-gray-700 dark:text-gray-300">
                        Avg (ms)
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {stats.slice(-10).reverse().map((stat, idx) => (
                      <tr
                        key={idx}
                        className="border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800"
                      >
                        <td className="px-3 py-2 text-gray-700 dark:text-gray-300">
                          {stat.date}
                        </td>
                        <td className="px-3 py-2 text-right font-medium">
                          <span className={stat.passRate > 80 ? 'text-green-700 dark:text-green-300' : stat.passRate > 50 ? 'text-yellow-700 dark:text-yellow-300' : 'text-red-700 dark:text-red-300'}>
                            {stat.passRate.toFixed(1)}%
                          </span>
                        </td>
                        <td className="px-3 py-2 text-right text-gray-700 dark:text-gray-300">
                          {stat.failedTests}
                        </td>
                        <td className="px-3 py-2 text-right text-gray-700 dark:text-gray-300">
                          {stat.averageDuration.toFixed(0)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="text-center py-8 text-gray-500 dark:text-gray-400">
          <p className="text-sm">No statistics available yet</p>
          <p className="text-xs">Run tests to populate statistics</p>
        </div>
      )}
    </div>
  );
};
