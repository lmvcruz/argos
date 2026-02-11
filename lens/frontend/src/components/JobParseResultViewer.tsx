import React from 'react';
import './JobParseResultViewer.css';

interface TestSummary {
  passed: number;
  failed: number;
  skipped: number;
  errors: number;
  total: number;
}

interface FailedTest {
  test_name: string;
  error_message: string;
  error_traceback?: string;
}

interface CoverageModule {
  name: string;
  statements: number;
  missing: number;
  coverage: number;
  missing_lines: string;
}

interface Coverage {
  total_statements: number;
  total_missing: number;
  total_coverage: number;
  modules?: CoverageModule[];
}

interface Flake8Issue {
  file: string;
  line: number;
  column: number;
  code: string;
  message: string;
}

interface JobParseResult {
  status: string;
  run_id: number;
  workflow_name: string;
  job_id: number;
  job_name: string;
  conclusion: string;
  runner_os?: string;
  python_version?: string;
  test_summary: TestSummary;
  failed_tests: FailedTest[];
  coverage: Coverage;
  flake8_issues: Flake8Issue[];
}

interface JobParseResultViewerProps {
  data: JobParseResult;
}

const JobParseResultViewer: React.FC<JobParseResultViewerProps> = ({ data }) => {
  const [expandedTest, setExpandedTest] = React.useState<number | null>(null);
  const [expandedModules, setExpandedModules] = React.useState(false);

  const getConclusionClass = (conclusion: string) => {
    switch (conclusion) {
      case 'success':
        return 'conclusion-success';
      case 'failure':
        return 'conclusion-failure';
      default:
        return 'conclusion-neutral';
    }
  };

  const getPassRate = () => {
    if (data.test_summary.total === 0) return 0;
    return ((data.test_summary.passed / data.test_summary.total) * 100).toFixed(1);
  };

  const getCoverageClass = (coverage: number) => {
    if (coverage >= 90) return 'coverage-excellent';
    if (coverage >= 75) return 'coverage-good';
    if (coverage >= 50) return 'coverage-fair';
    return 'coverage-poor';
  };

  return (
    <div className="job-parse-result-viewer">
      {/* Header Section */}
      <div className="result-header">
        <div className="job-info">
          <h2>{data.job_name}</h2>
          <div className="job-metadata">
            <span className="workflow-name">{data.workflow_name}</span>
            <span className="separator">•</span>
            <span className="run-id">Run #{data.run_id}</span>
            {data.runner_os && (
              <>
                <span className="separator">•</span>
                <span className="runner-os">{data.runner_os}</span>
              </>
            )}
            {data.python_version && (
              <>
                <span className="separator">•</span>
                <span className="python-version">Python {data.python_version}</span>
              </>
            )}
          </div>
        </div>
        <div className={`conclusion-badge ${getConclusionClass(data.conclusion)}`}>
          {data.conclusion}
        </div>
      </div>

      {/* Test Summary Section */}
      <div className="section test-summary-section">
        <h3>Test Summary</h3>
        <div className="summary-grid">
          <div className="summary-card total">
            <div className="card-value">{data.test_summary.total}</div>
            <div className="card-label">Total Tests</div>
          </div>
          <div className="summary-card passed">
            <div className="card-value">{data.test_summary.passed}</div>
            <div className="card-label">Passed</div>
          </div>
          <div className="summary-card failed">
            <div className="card-value">{data.test_summary.failed}</div>
            <div className="card-label">Failed</div>
          </div>
          <div className="summary-card skipped">
            <div className="card-value">{data.test_summary.skipped}</div>
            <div className="card-label">Skipped</div>
          </div>
          <div className="summary-card errors">
            <div className="card-value">{data.test_summary.errors}</div>
            <div className="card-label">Errors</div>
          </div>
          <div className="summary-card pass-rate">
            <div className="card-value">{getPassRate()}%</div>
            <div className="card-label">Pass Rate</div>
          </div>
        </div>
      </div>

      {/* Failed Tests Section */}
      {data.failed_tests.length > 0 && (
        <div className="section failed-tests-section">
          <h3>Failed Tests ({data.failed_tests.length})</h3>
          <div className="failed-tests-list">
            {data.failed_tests.map((test, index) => (
              <div key={index} className="failed-test-item">
                <div
                  className="test-header"
                  onClick={() => setExpandedTest(expandedTest === index ? null : index)}
                >
                  <span className="expand-icon">{expandedTest === index ? '▼' : '▶'}</span>
                  <span className="test-name">{test.test_name}</span>
                </div>
                {expandedTest === index && (
                  <div className="test-details">
                    <div className="error-message">
                      <strong>Error:</strong> {test.error_message}
                    </div>
                    {test.error_traceback && (
                      <div className="error-traceback">
                        <strong>Traceback:</strong>
                        <pre>{test.error_traceback}</pre>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Coverage Section */}
      {data.coverage && data.coverage.total_coverage !== undefined && (
        <div className="section coverage-section">
          <h3>Code Coverage</h3>
          <div className="coverage-overview">
            <div className={`coverage-badge ${getCoverageClass(data.coverage.total_coverage)}`}>
              {data.coverage.total_coverage.toFixed(1)}%
            </div>
            <div className="coverage-details">
              <div className="coverage-stat">
                <span className="label">Total Statements:</span>
                <span className="value">{data.coverage.total_statements}</span>
              </div>
              <div className="coverage-stat">
                <span className="label">Missing:</span>
                <span className="value">{data.coverage.total_missing}</span>
              </div>
              <div className="coverage-stat">
                <span className="label">Covered:</span>
                <span className="value">
                  {data.coverage.total_statements - data.coverage.total_missing}
                </span>
              </div>
            </div>
          </div>

          {/* Module Coverage Table */}
          {data.coverage.modules && data.coverage.modules.length > 0 && (
            <div className="module-coverage">
              <div className="module-header" onClick={() => setExpandedModules(!expandedModules)}>
                <span className="expand-icon">{expandedModules ? '▼' : '▶'}</span>
                <span>Module Coverage ({data.coverage.modules.length} modules)</span>
              </div>
              {expandedModules && (
                <div className="module-table-container">
                  <table className="module-table">
                    <thead>
                      <tr>
                        <th>Module</th>
                        <th>Coverage</th>
                        <th>Statements</th>
                        <th>Missing</th>
                        <th>Missing Lines</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.coverage.modules.slice(0, 20).map((module, index) => (
                        <tr key={index}>
                          <td className="module-name">{module.name}</td>
                          <td>
                            <span className={`coverage-value ${getCoverageClass(module.coverage)}`}>
                              {module.coverage.toFixed(1)}%
                            </span>
                          </td>
                          <td>{module.statements}</td>
                          <td>{module.missing}</td>
                          <td className="missing-lines">{module.missing_lines || 'None'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {data.coverage.modules.length > 20 && (
                    <div className="table-footer">
                      Showing 20 of {data.coverage.modules.length} modules
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Flake8 Issues Section */}
      {data.flake8_issues && data.flake8_issues.length > 0 && (
        <div className="section flake8-section">
          <h3>Linting Issues ({data.flake8_issues.length})</h3>
          <div className="flake8-list">
            {data.flake8_issues.map((issue, index) => (
              <div key={index} className="flake8-item">
                <span className="issue-code">{issue.code}</span>
                <span className="issue-location">
                  {issue.file}:{issue.line}:{issue.column}
                </span>
                <span className="issue-message">{issue.message}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Success Message if No Issues */}
      {data.failed_tests.length === 0 &&
        data.flake8_issues.length === 0 &&
        data.conclusion === 'success' && (
          <div className="success-message">
            <div className="success-icon">✓</div>
            <div className="success-text">All checks passed!</div>
          </div>
        )}
    </div>
  );
};

export default JobParseResultViewer;
