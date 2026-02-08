/**
 * TestRunner - Test execution and results display component.
 *
 * Provides interface for running selected tests and displaying results
 * with pass/fail status, duration, and error details.
 */

import React, { useState } from 'react';
import { Play, Loader, CheckCircle, AlertCircle, Zap } from 'lucide-react';

export interface TestResult {
  id: string;
  name: string;
  status: 'passed' | 'failed' | 'skipped';
  duration: number;
  error?: string;
  output?: string;
}

export interface TestRunnerProps {
  selectedTests: Set<string>;
  testCount: number;
  onRun: (selectedIds: Set<string>) => Promise<TestResult[]>;
  loading?: boolean;
}

/**
 * TestRunner component - Execute tests and display results.
 *
 * Shows a run button, progress indicator, and results table with
 * expandable error details. Tracks execution time and provides
 * clear status visualization.
 *
 * Args:
 *   selectedTests: Set of test IDs to run
 *   testCount: Total number of available tests
 *   onRun: Async callback to execute tests, returns results
 *   loading: External loading state
 */
export const TestRunner: React.FC<TestRunnerProps> = ({
  selectedTests,
  testCount,
  onRun,
  loading = false,
}) => {
  const [results, setResults] = useState<TestResult[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [expandedResults, setExpandedResults] = useState<Set<string>>(new Set());
  const [executionTime, setExecutionTime] = useState<number>(0);

  const handleRunTests = async () => {
    if (selectedTests.size === 0) {
      return;
    }

    setIsRunning(true);
    setResults([]);
    setExpandedResults(new Set());
    const startTime = Date.now();

    try {
      const testResults = await onRun(selectedTests);
      setResults(testResults);
      setExecutionTime(Date.now() - startTime);
    } catch (error) {
      console.error('Test execution failed:', error);
    } finally {
      setIsRunning(false);
    }
  };

  const toggleResultExpand = (id: string) => {
    const newExpanded = new Set(expandedResults);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedResults(newExpanded);
  };

  // Calculate stats
  const passedCount = results.filter((r) => r.status === 'passed').length;
  const failedCount = results.filter((r) => r.status === 'failed').length;
  const skippedCount = results.filter((r) => r.status === 'skipped').length;
  const totalDuration = results.reduce((sum, r) => sum + r.duration, 0);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'passed':
        return 'text-green-700 dark:text-green-300 bg-green-50 dark:bg-green-900/20';
      case 'failed':
        return 'text-red-700 dark:text-red-300 bg-red-50 dark:bg-red-900/20';
      case 'skipped':
        return 'text-yellow-700 dark:text-yellow-300 bg-yellow-50 dark:bg-yellow-900/20';
      default:
        return 'text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-900/20';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'passed':
        return <CheckCircle size={16} className="text-green-600 dark:text-green-400" />;
      case 'failed':
        return <AlertCircle size={16} className="text-red-600 dark:text-red-400" />;
      case 'skipped':
        return <Zap size={16} className="text-yellow-600 dark:text-yellow-400" />;
      default:
        return null;
    }
  };

  return (
    <div className="space-y-4">
      {/* Run Button */}
      <div className="flex gap-3 items-center">
        <button
          onClick={handleRunTests}
          disabled={selectedTests.size === 0 || isRunning || loading}
          className={`px-4 py-2 rounded font-medium flex items-center gap-2 transition-colors ${
            selectedTests.size === 0
              ? 'bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed'
              : 'bg-green-600 hover:bg-green-700 text-white disabled:opacity-50'
          }`}
        >
          {isRunning ? (
            <>
              <Loader size={16} className="animate-spin" />
              Running...
            </>
          ) : (
            <>
              <Play size={16} />
              Run Tests
            </>
          )}
        </button>

        {selectedTests.size > 0 && (
          <span className="text-sm text-gray-600 dark:text-gray-400">
            {selectedTests.size} of {testCount} test{selectedTests.size !== 1 ? 's' : ''} selected
          </span>
        )}

        {selectedTests.size === 0 && (
          <span className="text-sm text-gray-500 dark:text-gray-400 italic">
            Select tests to run
          </span>
        )}
      </div>

      {/* Results Summary */}
      {results.length > 0 && (
        <div className="grid grid-cols-4 gap-3 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <div>
            <div className="text-xs font-semibold text-gray-600 dark:text-gray-400 mb-1">
              Total
            </div>
            <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {results.length}
            </div>
          </div>

          <div>
            <div className="text-xs font-semibold text-green-700 dark:text-green-300 mb-1">
              Passed
            </div>
            <div className="text-2xl font-bold text-green-700 dark:text-green-300">
              {passedCount}
            </div>
          </div>

          <div>
            <div className="text-xs font-semibold text-red-700 dark:text-red-300 mb-1">
              Failed
            </div>
            <div className="text-2xl font-bold text-red-700 dark:text-red-300">
              {failedCount}
            </div>
          </div>

          <div>
            <div className="text-xs font-semibold text-purple-700 dark:text-purple-300 mb-1">
              Time
            </div>
            <div className="text-2xl font-bold text-purple-700 dark:text-purple-300">
              {(totalDuration / 1000).toFixed(1)}s
            </div>
          </div>
        </div>
      )}

      {/* Results Table */}
      {results.length > 0 && (
        <div className="max-h-96 overflow-y-auto border border-gray-200 dark:border-gray-700 rounded-lg">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0">
              <tr>
                <th className="text-left px-4 py-2 font-semibold text-gray-700 dark:text-gray-300">
                  Test Name
                </th>
                <th className="text-left px-4 py-2 font-semibold text-gray-700 dark:text-gray-300 w-20">
                  Status
                </th>
                <th className="text-right px-4 py-2 font-semibold text-gray-700 dark:text-gray-300 w-24">
                  Duration
                </th>
              </tr>
            </thead>
            <tbody>
              {results.map((result, idx) => {
                const isExpanded = expandedResults.has(result.id);
                return (
                  <React.Fragment key={result.id}>
                    <tr
                      className={`border-b border-gray-100 dark:border-gray-700 cursor-pointer transition-colors ${
                        isExpanded
                          ? 'bg-gray-50 dark:bg-gray-800'
                          : 'hover:bg-gray-50 dark:hover:bg-gray-800'
                      }`}
                      onClick={() => {
                        if (result.error || result.output) {
                          toggleResultExpand(result.id);
                        }
                      }}
                    >
                      <td className="px-4 py-3 font-mono text-xs text-gray-900 dark:text-gray-100">
                        {result.name}
                      </td>
                      <td className="px-4 py-3">
                        <div className={`inline-flex items-center gap-1.5 px-2 py-1 rounded text-xs font-medium ${getStatusColor(result.status)}`}>
                          {getStatusIcon(result.status)}
                          {result.status}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-right text-gray-600 dark:text-gray-400">
                        {result.duration}ms
                      </td>
                    </tr>

                    {/* Error Details */}
                    {isExpanded && (result.error || result.output) && (
                      <tr className="bg-gray-50 dark:bg-gray-900/50 border-b border-gray-200 dark:border-gray-700">
                        <td colSpan={3} className="px-4 py-3">
                          {result.error && (
                            <div className="mb-3">
                              <div className="text-xs font-semibold text-red-700 dark:text-red-300 mb-1">
                                Error:
                              </div>
                              <pre className="text-xs bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 p-2 rounded overflow-x-auto max-h-32 overflow-y-auto border border-red-200 dark:border-red-800">
                                {result.error}
                              </pre>
                            </div>
                          )}
                          {result.output && (
                            <div>
                              <div className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                                Output:
                              </div>
                              <pre className="text-xs bg-gray-100 dark:bg-gray-900 text-gray-700 dark:text-gray-300 p-2 rounded overflow-x-auto max-h-32 overflow-y-auto border border-gray-300 dark:border-gray-700 font-mono">
                                {result.output}
                              </pre>
                            </div>
                          )}
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Empty State */}
      {results.length === 0 && !isRunning && (
        <div className="text-center py-12 text-gray-500 dark:text-gray-400">
          <p className="text-sm">
            {selectedTests.size === 0
              ? 'Select tests from the left panel to run them'
              : 'Click "Run Tests" to execute selected tests'}
          </p>
        </div>
      )}
    </div>
  );
};
