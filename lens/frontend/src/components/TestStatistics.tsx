/**
 * TestStatistics - Historical test statistics and trends.
 *
 * Displays historical test execution data from database including
 * pass rates, failure trends, and execution time statistics.
 */

import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Calendar, BarChart3, Loader } from 'lucide-react';
import './TestStatistics.css';

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
      <div className="stats-loading">
        <Loader size={20} className="spinner" />
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
    <div className="test-statistics">
      {/* Timeframe Selector */}
      <div className="timeframe-selector">
        {(['week', 'month', 'all'] as const).map((tf) => (
          <button
            key={tf}
            onClick={() => setTimeframe(tf)}
            className={`timeframe-btn ${timeframe === tf ? 'active' : ''}`}
          >
            {tf === 'week' ? 'This Week' : tf === 'month' ? 'This Month' : 'All Time'}
          </button>
        ))}
      </div>

      {stats.length > 0 && latestStats ? (
        <>
          {/* Key Metrics */}
          <div className="metrics-grid">
            {/* Pass Rate */}
            <div className="metric-card metric-success">
              <div className="metric-header">
                <span className="metric-label">Pass Rate</span>
                {passRateTrend !== 0 && (
                  <div className="trend">
                    {passRateTrend > 0 ? (
                      <TrendingUp size={12} className="trend-up" />
                    ) : (
                      <TrendingDown size={12} className="trend-down" />
                    )}
                    <span className={passRateTrend > 0 ? 'trend-up' : 'trend-down'}>
                      {passRateTrend > 0 ? '+' : ''}{passRateTrend.toFixed(1)}%
                    </span>
                  </div>
                )}
              </div>
              <div className="metric-value">
                {latestStats.passRate.toFixed(1)}%
              </div>
              <div className="metric-detail">
                {latestStats.passedTests} passed
              </div>
            </div>

            {/* Failed Tests */}
            <div className="metric-card metric-failed">
              <div className="metric-header">
                <span className="metric-label">Failed Tests</span>
                {failuresTrend !== 0 && (
                  <div className="trend">
                    {failuresTrend < 0 ? (
                      <TrendingDown size={12} className="trend-up" />
                    ) : (
                      <TrendingUp size={12} className="trend-down" />
                    )}
                    <span className={failuresTrend < 0 ? 'trend-up' : 'trend-down'}>
                      {failuresTrend > 0 ? '+' : ''}{failuresTrend}
                    </span>
                  </div>
                )}
              </div>
              <div className="metric-value">
                {latestStats.failedTests}
              </div>
              <div className="metric-detail">
                of {latestStats.totalTests} total
              </div>
            </div>

            {/* Avg Duration */}
            <div className="metric-card metric-duration">
              <div className="metric-header">
                <span className="metric-label">Avg Duration</span>
                {durationTrend !== 0 && (
                  <div className="trend">
                    {durationTrend < 0 ? (
                      <TrendingDown size={12} className="trend-up" />
                    ) : (
                      <TrendingUp size={12} className="trend-down" />
                    )}
                    <span className={durationTrend < 0 ? 'trend-up' : 'trend-down'}>
                      {durationTrend > 0 ? '+' : ''}{durationTrend.toFixed(0)}ms
                    </span>
                  </div>
                )}
              </div>
              <div className="metric-value">
                {latestStats.averageDuration.toFixed(0)}ms
              </div>
              <div className="metric-detail">
                per test
              </div>
            </div>

            {/* Total Tests */}
            <div className="metric-card metric-total">
              <div className="metric-header">
                <span className="metric-label">Total Tests</span>
                <BarChart3 size={14} />
              </div>
              <div className="metric-value">
                {latestStats.totalTests}
              </div>
              <div className="metric-detail">
                {latestStats.skippedTests} skipped
              </div>
            </div>
          </div>

          {/* Historical Data Table */}
          {stats.length > 1 && (
            <div className="history-section">
              <h4 className="history-title">
                <Calendar size={14} />
                History
              </h4>
              <div className="history-table-container">
                <table className="history-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th className="text-right">Pass %</th>
                      <th className="text-right">Failed</th>
                      <th className="text-right">Avg (ms)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stats.slice(-10).reverse().map((stat, idx) => (
                      <tr key={idx}>
                        <td>{stat.date}</td>
                        <td className="text-right">
                          <span className={`pass-rate ${stat.passRate > 80 ? 'high' : stat.passRate > 50 ? 'medium' : 'low'}`}>
                            {stat.passRate.toFixed(1)}%
                          </span>
                        </td>
                        <td className="text-right">{stat.failedTests}</td>
                        <td className="text-right">{stat.averageDuration.toFixed(0)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="stats-empty">
          <p>No statistics available yet</p>
          <p className="hint">Run tests to populate statistics</p>
        </div>
      )}
    </div>
  );
};
