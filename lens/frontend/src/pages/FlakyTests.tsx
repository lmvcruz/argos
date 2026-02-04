import React, { useEffect, useState } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import api from '../api/client';

/**
 * Flaky Tests Analysis Page
 *
 * Displays:
 * - List of flaky tests with failure rates
 * - Failure patterns and trends
 * - Recommendations for stabilization
 */
export default function FlakyTests() {
  const [flakyTests, setFlakyTests] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [threshold, setThreshold] = useState(3);
  const [lookbackRuns, setLookbackRuns] = useState(10);

  useEffect(() => {
    fetchFlakyTests();
  }, [threshold, lookbackRuns]);

  const fetchFlakyTests = async () => {
    try {
      setLoading(true);
      const result = await api.getFlakyTests(threshold, lookbackRuns);
      setFlakyTests(result.flaky_tests || []);
    } catch (error) {
      console.error('Failed to fetch flaky tests:', error);
    } finally {
      setLoading(false);
    }
  };

  const failureRateColor = (rate: number): string => {
    if (rate >= 50) return 'text-red-500';
    if (rate >= 25) return 'text-yellow-500';
    return 'text-orange-500';
  };

  const failureBgColor = (rate: number): string => {
    if (rate >= 50) return 'bg-red-900';
    if (rate >= 25) return 'bg-yellow-900';
    return 'bg-orange-900';
  };

  return (
    <div className="p-8 space-y-8">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-4xl font-bold mb-2">Flaky Tests Analysis</h1>
          <p className="text-gray-400">Identify tests with inconsistent results</p>
        </div>
        <button
          onClick={fetchFlakyTests}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50"
        >
          <RefreshCw size={20} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {/* Filter Controls */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">Failure Count Threshold</label>
            <input
              type="number"
              value={threshold}
              onChange={(e) => setThreshold(parseInt(e.target.value) || 3)}
              min="1"
              className="w-full bg-gray-700 border border-gray-600 rounded px-4 py-2 focus:outline-none focus:border-blue-500"
            />
            <p className="text-xs text-gray-500 mt-1">Tests failing at least this many times</p>
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Lookback Runs</label>
            <input
              type="number"
              value={lookbackRuns}
              onChange={(e) => setLookbackRuns(parseInt(e.target.value) || 10)}
              min="1"
              className="w-full bg-gray-700 border border-gray-600 rounded px-4 py-2 focus:outline-none focus:border-blue-500"
            />
            <p className="text-xs text-gray-500 mt-1">Number of runs to analyze</p>
          </div>
        </div>
      </div>

      {/* Stats Card */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <div className="flex items-center gap-3">
          <AlertTriangle className="text-yellow-500" size={32} />
          <div>
            <p className="text-gray-400 text-sm">Total Flaky Tests</p>
            <p className="text-4xl font-bold">{flakyTests.length}</p>
          </div>
        </div>
      </div>

      {/* Flaky Tests List */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h2 className="text-xl font-semibold mb-4">Flaky Tests</h2>
        {flakyTests.length === 0 ? (
          <div className="text-center py-8 text-gray-400">
            <p>No flaky tests found with current settings</p>
          </div>
        ) : (
          <div className="space-y-3">
            {flakyTests
              .sort((a, b) => b.failure_rate - a.failure_rate)
              .map((test) => (
                <div
                  key={test.test_id}
                  className={`p-4 rounded-lg border border-gray-600 hover:bg-gray-700 transition-colors`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <p className="font-mono text-sm break-all mb-1">{test.test_id}</p>
                      <p className="text-xs text-gray-500">
                        Failed in {test.failure_count} out of {test.lookback_runs} runs
                      </p>
                    </div>
                    <span
                      className={`px-3 py-1 rounded font-semibold text-sm ${failureBgColor(
                        test.failure_rate
                      )} ${failureRateColor(test.failure_rate)}`}
                    >
                      {test.failure_rate.toFixed(1)}%
                    </span>
                  </div>

                  {/* Failure Rate Progress Bar */}
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all ${
                        test.failure_rate >= 50
                          ? 'bg-red-500'
                          : test.failure_rate >= 25
                          ? 'bg-yellow-500'
                          : 'bg-orange-500'
                      }`}
                      style={{ width: `${test.failure_rate}%` }}
                    />
                  </div>

                  {/* Recommendation */}
                  <div className="mt-3 text-xs text-gray-400 bg-gray-900 p-3 rounded">
                    {test.failure_rate >= 50 && (
                      <p>
                        🔴 <strong>High flakiness:</strong> Consider isolating this test or
                        investigating environment dependencies.
                      </p>
                    )}
                    {test.failure_rate >= 25 && test.failure_rate < 50 && (
                      <p>
                        🟡 <strong>Moderate flakiness:</strong> Review test for race conditions or
                        timing issues.
                      </p>
                    )}
                    {test.failure_rate < 25 && (
                      <p>
                        🟠 <strong>Minor flakiness:</strong> Monitor this test for stability
                        improvements.
                      </p>
                    )}
                  </div>
                </div>
              ))}
          </div>
        )}
      </div>

      {/* Recommendations */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h2 className="text-xl font-semibold mb-4">Recommendations</h2>
        <div className="space-y-3 text-sm text-gray-300">
          <p>
            ✓ <strong>Increase timeouts:</strong> Add explicit waits or increase default timeouts
            for network/IO operations
          </p>
          <p>
            ✓ <strong>Isolate dependencies:</strong> Use mocks for external services (network,
            filesystem)
          </p>
          <p>
            ✓ <strong>Fix race conditions:</strong> Ensure proper synchronization between async
            operations
          </p>
          <p>
            ✓ <strong>Resource cleanup:</strong> Ensure tests properly clean up resources (files,
            connections)
          </p>
          <p>
            ✓ <strong>Platform-specific fixes:</strong> Check for platform-specific issues
            (Windows vs Unix)
          </p>
        </div>
      </div>
    </div>
  );
}
