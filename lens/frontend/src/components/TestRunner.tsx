/**
 * TestRunner - Test execution and results display component.
 *
 * Provides interface for running selected tests and displaying results
 * with pass/fail status, duration, and error details.
 */

import React, { useState } from 'react';
import { Play, Loader, CheckCircle, AlertCircle, Zap } from 'lucide-react';
import './TestRunner.css';

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
  const [filter, setFilter] = useState<'all' | 'passed' | 'failed'>('all');

  const handleRunTests = async () => {
    if (selectedTests.size === 0) {
      return;
    }

    setIsRunning(true);
    setResults([]);
    setExpandedResults(new Set());
    setFilter('all');
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

  // Filter results based on selected filter
  const filteredResults = results.filter((result) => {
    if (filter === 'passed') return result.status === 'passed';
    if (filter === 'failed') return result.status === 'failed';
    return true; // 'all'
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'passed':
        return <CheckCircle size={14} />;
      case 'failed':
        return <AlertCircle size={14} />;
      case 'skipped':
        return <Zap size={14} />;
      default:
        return null;
    }
  };

  return (
    <div className="test-runner">
      {/* Run Button Section */}
      <div className="runner-toolbar">
        <button
          onClick={handleRunTests}
          disabled={selectedTests.size === 0 || isRunning || loading}
          className={`run-button ${selectedTests.size === 0 ? 'disabled' : ''} ${isRunning ? 'running' : ''}`}
        >
          {isRunning ? (
            <>
              <Loader size={16} className="spinner" />
              Running...
            </>
          ) : (
            <>
              <Play size={16} />
              Run Tests
            </>
          )}
        </button>

        <div className="selection-info">
          {selectedTests.size > 0 ? (
            <span>
              {selectedTests.size} of {testCount} test{selectedTests.size !== 1 ? 's' : ''} selected
            </span>
          ) : (
            <span className="hint">Select tests to run</span>
          )}
        </div>
      </div>

      {/* Results Summary */}
      {results.length > 0 && (
        <div className="results-summary">
          <div
            className={`stat-card stat-clickable ${filter === 'all' ? 'active' : ''}`}
            onClick={() => setFilter('all')}
            title="Show all tests"
          >
            <div className="stat-label">Total</div>
            <div className="stat-value">{results.length}</div>
          </div>

          <div
            className={`stat-card stat-passed stat-clickable ${filter === 'passed' ? 'active' : ''}`}
            onClick={() => setFilter('passed')}
            title="Show only passed tests"
          >
            <div className="stat-label">Passed</div>
            <div className="stat-value">{passedCount}</div>
          </div>

          <div
            className={`stat-card stat-failed stat-clickable ${filter === 'failed' ? 'active' : ''}`}
            onClick={() => setFilter('failed')}
            title="Show only failed tests"
          >
            <div className="stat-label">Failed</div>
            <div className="stat-value">{failedCount}</div>
          </div>

          <div className="stat-card stat-time">
            <div className="stat-label">Time</div>
            <div className="stat-value">{(totalDuration / 1000).toFixed(1)}s</div>
          </div>
        </div>
      )}

      {/* Results Table */}
      {results.length > 0 && (
        <div className="results-table-container">
          <table className="results-table">
            <thead>
              <tr>
                <th>Test Name</th>
                <th>Status</th>
                <th className="text-right">Duration</th>
              </tr>
            </thead>
            <tbody>
              {filteredResults.map((result) => {
                const isExpanded = expandedResults.has(result.id);
                return (
                  <React.Fragment key={result.id}>
                    <tr
                      className={`result-row ${isExpanded ? 'expanded' : ''} ${result.error || result.output ? 'clickable' : ''}`}
                      onClick={() => {
                        if (result.error || result.output) {
                          toggleResultExpand(result.id);
                        }
                      }}
                    >
                      <td className="test-name">{result.name}</td>
                      <td>
                        <div className={`status-badge status-${result.status}`}>
                          {getStatusIcon(result.status)}
                          {result.status}
                        </div>
                      </td>
                      <td className="text-right duration">{result.duration}ms</td>
                    </tr>

                    {/* Error Details */}
                    {isExpanded && (result.error || result.output) && (
                      <tr className="details-row">
                        <td colSpan={3}>
                          {result.error && (
                            <div className="error-details">
                              <div className="details-label">Error:</div>
                              <pre className="error-content">{result.error}</pre>
                            </div>
                          )}
                          {result.output && (
                            <div className="output-details">
                              <div className="details-label">Output:</div>
                              <pre className="output-content">{result.output}</pre>
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
        <div className="empty-state">
          <p>
            {selectedTests.size === 0
              ? 'Select tests from the left panel to run them'
              : 'Click "Run Tests" to execute selected tests'}
          </p>
        </div>
      )}
    </div>
  );
};
