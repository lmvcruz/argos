/**
 * ScoutDataViewer component for displaying Scout parse results
 * Shows comprehensive CI analysis including summary, job details, and common failures
 */

import { AlertCircle, CheckCircle, XCircle, ChevronDown, ChevronRight } from 'lucide-react';
import React, { useState } from 'react';

interface ScoutSummary {
  total_jobs: number;
  failed_jobs: number;
  total_tests: number;
  total_test_failures: number;
}

interface TestSummary {
  passed: number;
  failed: number;
  skipped: number;
  errors: number;
}

interface FailedTest {
  test_name: string;
  error_message: string;
}

interface FlakeIssue {
  file: string;
  line: number;
  code: string;
  message: string;
}

interface FailurePattern {
  pattern: string;
  count: number;
}

interface JobResult {
  job_name: string;
  platform?: string;
  python_version?: string;
  status: string;
  test_summary?: TestSummary;
  failed_tests?: FailedTest[];
  coverage?: {
    total_coverage: number;
    line_coverage?: number;
    branch_coverage?: number;
  };
  flake8_issues?: FlakeIssue[];
  failure_patterns?: FailurePattern[];
}

interface CommonTestFailure {
  test_name: string;
  failure_count: number;
  failed_in_jobs: string[];
}

interface ScoutParseData {
  status: string;
  run_id: number;
  workflow_name: string;
  summary: ScoutSummary;
  jobs: JobResult[];
  common_test_failures?: CommonTestFailure[];
}

export interface ScoutDataViewerProps {
  data: ScoutParseData | null;
  loading?: boolean;
  height?: string;
}

export const ScoutDataViewer: React.FC<ScoutDataViewerProps> = ({
  data = null,
  loading = false,
  height = '600px',
}) => {
  const [expandedJobs, setExpandedJobs] = useState<Set<number>>(new Set());
  const [activeTab, setActiveTab] = useState<'summary' | 'jobs' | 'failures'>('summary');

  const toggleJob = (index: number) => {
    const newExpanded = new Set(expandedJobs);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedJobs(newExpanded);
  };

  if (loading) {
    return (
      <div
        className="flex items-center justify-center bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
        style={{ height }}
      >
        <span className="text-gray-500 dark:text-gray-400">Loading Scout analysis...</span>
      </div>
    );
  }

  if (!data) {
    return (
      <div
        className="flex items-center justify-center bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
        style={{ height }}
      >
        <span className="text-gray-500 dark:text-gray-400">No Scout data available</span>
      </div>
    );
  }

  const { summary, jobs, common_test_failures } = data;

  return (
    <div
      className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden flex flex-col"
      style={{ height }}
    >
      {/* Header */}
      <div className="bg-gray-50 dark:bg-gray-900 px-4 py-3 border-b border-gray-200 dark:border-gray-700">
        <h3 className="font-semibold text-gray-700 dark:text-gray-300">
          Scout Analysis: {data.workflow_name}
        </h3>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
        <button
          onClick={() => setActiveTab('summary')}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === 'summary'
              ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
          }`}
        >
          Summary
        </button>
        <button
          onClick={() => setActiveTab('jobs')}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === 'jobs'
              ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
          }`}
        >
          Jobs ({jobs.length})
        </button>
        <button
          onClick={() => setActiveTab('failures')}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === 'failures'
              ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
          }`}
        >
          Common Failures ({common_test_failures?.length || 0})
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-4">
        {/* Summary Tab */}
        {activeTab === 'summary' && (
          <div className="space-y-4">
            {/* Stats Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-blue-50 dark:bg-blue-950 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
                <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                  {summary.total_jobs}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Total Jobs</div>
              </div>
              <div className="bg-red-50 dark:bg-red-950 rounded-lg p-4 border border-red-200 dark:border-red-800">
                <div className="text-2xl font-bold text-red-600 dark:text-red-400">
                  {summary.failed_jobs}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Failed Jobs</div>
              </div>
              <div className="bg-green-50 dark:bg-green-950 rounded-lg p-4 border border-green-200 dark:border-green-800">
                <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                  {summary.total_tests.toLocaleString()}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Total Tests</div>
              </div>
              <div className="bg-orange-50 dark:bg-orange-950 rounded-lg p-4 border border-orange-200 dark:border-orange-800">
                <div className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                  {summary.total_test_failures}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Test Failures</div>
              </div>
            </div>

            {/* Success Rate */}
            <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Success Rate
                </span>
                <span className="text-sm font-bold text-gray-900 dark:text-gray-100">
                  {(
                    ((summary.total_tests - summary.total_test_failures) /
                      summary.total_tests) *
                    100
                  ).toFixed(2)}
                  %
                </span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  className="bg-green-500 h-2 rounded-full transition-all"
                  style={{
                    width: `${
                      ((summary.total_tests - summary.total_test_failures) /
                        summary.total_tests) *
                      100
                    }%`,
                  }}
                />
              </div>
            </div>
          </div>
        )}

        {/* Jobs Tab */}
        {activeTab === 'jobs' && (
          <div className="space-y-2">
            {jobs.map((job, index) => {
              const isExpanded = expandedJobs.has(index);
              const hasFailed = job.status !== 'success';

              return (
                <div
                  key={index}
                  className={`border rounded-lg overflow-hidden ${
                    hasFailed
                      ? 'border-red-300 dark:border-red-700'
                      : 'border-green-300 dark:border-green-700'
                  }`}
                >
                  {/* Job Header */}
                  <button
                    onClick={() => toggleJob(index)}
                    className={`w-full px-4 py-3 flex items-center justify-between ${
                      hasFailed
                        ? 'bg-red-50 dark:bg-red-950 hover:bg-red-100 dark:hover:bg-red-900'
                        : 'bg-green-50 dark:bg-green-950 hover:bg-green-100 dark:hover:bg-green-900'
                    } transition-colors`}
                  >
                    <div className="flex items-center gap-3">
                      {hasFailed ? (
                        <XCircle className="text-red-600 dark:text-red-400" size={20} />
                      ) : (
                        <CheckCircle className="text-green-600 dark:text-green-400" size={20} />
                      )}
                      <div className="text-left">
                        <div className="font-semibold text-gray-900 dark:text-gray-100 text-sm">
                          {job.job_name}
                        </div>
                        {(job.platform || job.python_version) && (
                          <div className="text-xs text-gray-600 dark:text-gray-400">
                            {job.platform && <span>{job.platform}</span>}
                            {job.python_version && (
                              <span className="ml-2">Python {job.python_version}</span>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      {job.test_summary && (
                        <div className="text-xs text-gray-600 dark:text-gray-400">
                          {job.test_summary.passed} passed, {job.test_summary.failed} failed
                        </div>
                      )}
                      {isExpanded ? (
                        <ChevronDown size={16} className="text-gray-500" />
                      ) : (
                        <ChevronRight size={16} className="text-gray-500" />
                      )}
                    </div>
                  </button>

                  {/* Job Details */}
                  {isExpanded && (
                    <div className="bg-white dark:bg-gray-800 p-4 space-y-4">
                      {/* Test Summary */}
                      {job.test_summary && (
                        <div>
                          <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-2 text-sm">
                            Test Summary
                          </h4>
                          <div className="grid grid-cols-4 gap-2">
                            <div className="bg-green-50 dark:bg-green-950 rounded p-2">
                              <div className="text-lg font-bold text-green-600 dark:text-green-400">
                                {job.test_summary.passed}
                              </div>
                              <div className="text-xs text-gray-600 dark:text-gray-400">
                                Passed
                              </div>
                            </div>
                            <div className="bg-red-50 dark:bg-red-950 rounded p-2">
                              <div className="text-lg font-bold text-red-600 dark:text-red-400">
                                {job.test_summary.failed}
                              </div>
                              <div className="text-xs text-gray-600 dark:text-gray-400">
                                Failed
                              </div>
                            </div>
                            <div className="bg-yellow-50 dark:bg-yellow-950 rounded p-2">
                              <div className="text-lg font-bold text-yellow-600 dark:text-yellow-400">
                                {job.test_summary.skipped}
                              </div>
                              <div className="text-xs text-gray-600 dark:text-gray-400">
                                Skipped
                              </div>
                            </div>
                            <div className="bg-orange-50 dark:bg-orange-950 rounded p-2">
                              <div className="text-lg font-bold text-orange-600 dark:text-orange-400">
                                {job.test_summary.errors}
                              </div>
                              <div className="text-xs text-gray-600 dark:text-gray-400">
                                Errors
                              </div>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Coverage */}
                      {job.coverage && (
                        <div>
                          <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-2 text-sm">
                            Coverage
                          </h4>
                          <div className="bg-gray-50 dark:bg-gray-900 rounded p-3">
                            <div className="flex items-center justify-between">
                              <span className="text-sm text-gray-600 dark:text-gray-400">
                                Total Coverage
                              </span>
                              <span className="text-sm font-bold text-gray-900 dark:text-gray-100">
                                {job.coverage.total_coverage}%
                              </span>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Failed Tests */}
                      {job.failed_tests && job.failed_tests.length > 0 && (
                        <div>
                          <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-2 text-sm">
                            Failed Tests ({job.failed_tests.length})
                          </h4>
                          <div className="space-y-2 max-h-60 overflow-auto">
                            {job.failed_tests.map((test, testIdx) => (
                              <div
                                key={testIdx}
                                className="bg-red-50 dark:bg-red-950 rounded p-2 border border-red-200 dark:border-red-800"
                              >
                                <div className="font-mono text-xs text-red-700 dark:text-red-300 mb-1">
                                  {test.test_name}
                                </div>
                                {test.error_message && (
                                  <div className="bg-gray-900 dark:bg-gray-950 text-gray-100 p-2 rounded font-mono text-xs whitespace-pre-wrap break-words max-h-32 overflow-auto">
                                    {test.error_message}
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Flake8 Issues */}
                      {job.flake8_issues && job.flake8_issues.length > 0 && (
                        <div>
                          <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-2 text-sm">
                            Flake8 Issues ({job.flake8_issues.length})
                          </h4>
                          <div className="space-y-1 max-h-40 overflow-auto">
                            {job.flake8_issues.map((issue, issueIdx) => (
                              <div
                                key={issueIdx}
                                className="bg-yellow-50 dark:bg-yellow-950 rounded p-2 text-xs"
                              >
                                <div className="font-mono text-yellow-700 dark:text-yellow-300">
                                  {issue.file}:{issue.line} - {issue.code}
                                </div>
                                <div className="text-gray-600 dark:text-gray-400">
                                  {issue.message}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Common Failures Tab */}
        {activeTab === 'failures' && (
          <div className="space-y-3">
            {common_test_failures && common_test_failures.length > 0 ? (
              common_test_failures.map((failure, index) => (
                <div
                  key={index}
                  className="bg-red-50 dark:bg-red-950 rounded-lg p-4 border border-red-200 dark:border-red-800"
                >
                  <div className="flex items-start gap-3">
                    <AlertCircle className="text-red-600 dark:text-red-400 mt-0.5" size={20} />
                    <div className="flex-1">
                      <div className="font-mono text-sm text-red-700 dark:text-red-300 mb-2">
                        {failure.test_name}
                      </div>
                      <div className="text-xs text-gray-600 dark:text-gray-400 mb-2">
                        Failed in {failure.failure_count} job{failure.failure_count > 1 ? 's' : ''}
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {failure.failed_in_jobs.map((jobName, jobIdx) => (
                          <span
                            key={jobIdx}
                            className="px-2 py-1 bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300 rounded text-xs"
                          >
                            {jobName}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                No common test failures detected
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ScoutDataViewer;
