import React, { useEffect, useState } from 'react';
import { Zap, AlertCircle, TrendingDown, TrendingUp } from 'lucide-react';
import { useScout } from '../../contexts/ScoutContext';

/**
 * HealthDashboard
 *
 * Detect and monitor flaky tests.
 * Shows test reliability metrics and trends.
 */

const HealthDashboard: React.FC = () => {
  const { flakyTests, flakyTestsLoading, fetchFlakyTests } = useScout();

  const [threshold, setThreshold] = useState(0.5);
  const [sortBy, setSortBy] = useState<'pass_rate' | 'last_failed'>('pass_rate');

  // Load flaky tests on mount
  useEffect(() => {
    fetchFlakyTests(threshold);
  }, [threshold, fetchFlakyTests]);

  const sortedTests = [...flakyTests].sort((a, b) => {
    if (sortBy === 'pass_rate') {
      return a.pass_rate - b.pass_rate; // Most flaky first
    } else {
      // Sort by most recently failed
      const aDate = a.last_failed ? new Date(a.last_failed).getTime() : 0;
      const bDate = b.last_failed ? new Date(b.last_failed).getTime() : 0;
      return bDate - aDate;
    }
  });

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'improving':
        return <TrendingDown className="w-4 h-4 text-green-500" />;
      case 'degrading':
        return <TrendingUp className="w-4 h-4 text-red-500" />;
      default:
        return <TrendingDown className="w-4 h-4 text-gray-400" />;
    }
  };

  const getTrendLabel = (trend: string) => {
    switch (trend) {
      case 'improving':
        return 'Getting better';
      case 'degrading':
        return 'Getting worse';
      default:
        return 'Stable';
    }
  };

  const getFlakySeverity = (passRate: number) => {
    if (passRate < 0.3) return { level: 'Critical', color: 'text-red-700', bg: 'bg-red-50' };
    if (passRate < 0.5) return { level: 'High', color: 'text-orange-700', bg: 'bg-orange-50' };
    if (passRate < 0.7) return { level: 'Medium', color: 'text-yellow-700', bg: 'bg-yellow-50' };
    return { level: 'Low', color: 'text-green-700', bg: 'bg-green-50' };
  };

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="px-8 py-6 border-b border-gray-200 bg-gradient-to-r from-yellow-50 to-amber-50">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <Zap className="w-6 h-6 text-amber-500" />
              Health & Reliability
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              Monitor flaky and unreliable tests
            </p>
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="px-8 py-4 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            <span className="text-sm font-medium text-gray-700">Flakiness Threshold:</span>
            <div className="flex items-center gap-2">
              <input
                type="range"
                min="0.1"
                max="0.9"
                step="0.1"
                value={threshold}
                onChange={(e) => setThreshold(parseFloat(e.target.value))}
                className="w-32"
              />
              <span className="text-sm font-semibold text-gray-900 w-12">
                {Math.round(threshold * 100)}%
              </span>
            </div>
            <span className="text-xs text-gray-600">
              Tests with pass rate below this are considered flaky
            </span>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-gray-700">Sort by:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
            >
              <option value="pass_rate">Flakiness (Worst First)</option>
              <option value="last_failed">Recently Failed</option>
            </select>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {flakyTestsLoading ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
              <p className="text-gray-600">Analyzing test reliability...</p>
            </div>
          </div>
        ) : sortedTests.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-4">
                <Zap className="w-6 h-6 text-green-600" />
              </div>
              <p className="text-lg font-semibold text-gray-900">All Tests Reliable!</p>
              <p className="text-sm text-gray-600 mt-1">
                No flaky tests detected with current threshold
              </p>
            </div>
          </div>
        ) : (
          <div className="p-8 space-y-4">
            {/* Summary */}
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="text-2xl font-bold text-red-900">
                  {sortedTests.filter((t) => t.pass_rate < 0.3).length}
                </div>
                <div className="text-sm text-red-700">Critical</div>
              </div>

              <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                <div className="text-2xl font-bold text-orange-900">
                  {sortedTests.filter((t) => t.pass_rate >= 0.3 && t.pass_rate < 0.7).length}
                </div>
                <div className="text-sm text-orange-700">High/Medium</div>
              </div>

              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <div className="text-2xl font-bold text-yellow-900">
                  {sortedTests.filter((t) => t.pass_rate >= 0.7).length}
                </div>
                <div className="text-sm text-yellow-700">Low Flakiness</div>
              </div>
            </div>

            {/* Flaky Tests List */}
            <div className="space-y-3">
              {sortedTests.map((test) => {
                const severity = getFlakySeverity(test.pass_rate);

                return (
                  <div
                    key={test.test_nodeid}
                    className={`${severity.bg} border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow`}
                  >
                    {/* Test Header */}
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <AlertCircle className={`w-5 h-5 ${severity.color}`} />
                          <h3 className={`font-semibold ${severity.color}`}>
                            {test.test_nodeid}
                          </h3>
                        </div>

                        {/* Metrics */}
                        <div className="mt-3 grid grid-cols-5 gap-4">
                          {/* Pass Rate */}
                          <div>
                            <div className="text-2xl font-bold text-gray-900">
                              {Math.round(test.pass_rate * 100)}%
                            </div>
                            <div className="text-xs text-gray-600">Pass Rate</div>
                          </div>

                          {/* Fail Rate */}
                          <div>
                            <div className="text-2xl font-bold text-red-600">
                              {Math.round(test.fail_rate * 100)}%
                            </div>
                            <div className="text-xs text-gray-600">Fail Rate</div>
                          </div>

                          {/* Total Runs */}
                          <div>
                            <div className="text-2xl font-bold text-gray-900">
                              {test.total_runs}
                            </div>
                            <div className="text-xs text-gray-600">Total Runs</div>
                          </div>

                          {/* Severity */}
                          <div>
                            <div className={`text-sm font-semibold ${severity.color}`}>
                              {severity.level}
                            </div>
                            <div className="text-xs text-gray-600">Severity</div>
                          </div>

                          {/* Trend */}
                          <div>
                            <div className="flex items-center gap-1">
                              {getTrendIcon(test.trend)}
                              <span className="text-sm font-medium text-gray-900">
                                {getTrendLabel(test.trend)}
                              </span>
                            </div>
                            <div className="text-xs text-gray-600">Trend</div>
                          </div>
                        </div>

                        {/* Last Failed */}
                        {test.last_failed && (
                          <div className="mt-3 text-xs text-gray-600">
                            Last failed:{' '}
                            {new Date(test.last_failed).toLocaleDateString('en-US', {
                              month: 'short',
                              day: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </div>
                        )}
                      </div>

                      {/* Action Button */}
                      <button className="px-3 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors flex-shrink-0">
                        Investigate
                      </button>
                    </div>

                    {/* Pass Rate Bar */}
                    <div className="mt-4 h-2 bg-white/50 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-red-500 to-green-500 transition-all"
                        style={{ width: `${test.pass_rate * 100}%` }}
                      ></div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Recommendations */}
            <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
              <h4 className="font-semibold text-blue-900 mb-2">Recommendations</h4>
              <ul className="text-blue-800 text-sm space-y-2">
                <li>
                  ✓ Review test implementation for timing/race conditions
                </li>
                <li>
                  ✓ Increase timeouts or add retries for flaky tests
                </li>
                <li>
                  ✓ Check for environment-specific issues (OS, Python version)
                </li>
                <li>
                  ✓ Consider splitting large tests into smaller units
                </li>
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default HealthDashboard;
