/**
 * ValidationReport component - Display comprehensive validation report.
 *
 * Shows:
 * - Report summary (timestamp, target, language, validator)
 * - Issue statistics with charts
 * - Quality score
 * - Detailed results list
 */

import React from 'react';
import './ValidationReport.css';

/**
 * Validation report structure
 */
export interface ValidationReport {
  timestamp: string;
  target: string;
  language: string;
  validator: string;
  total_issues: number;
  errors: number;
  warnings: number;
  infos: number;
  status: string;
}

/**
 * Validation result structure
 */
export interface ValidationResult {
  file: string;
  line: number;
  column: number;
  severity: 'error' | 'warning' | 'info';
  message: string;
  rule?: string;
  diff?: string;
}

/**
 * ValidationReport props
 */
interface ValidationReportProps {
  report?: ValidationReport;
  results?: ValidationResult[];
  onExport?: () => void;
}

/**
 * ValidationReport - Display comprehensive validation report
 *
 * Args:
 *   report: Validation report summary with statistics
 *   results: List of validation results with detailed issues
 *   onExport: Callback when export button clicked
 */
export const ValidationReport: React.FC<ValidationReportProps> = ({
  report,
  results = [],
  onExport,
}) => {
  const [expandedDiffs, setExpandedDiffs] = React.useState<Set<number>>(new Set());

  if (!report) {
    return null;
  }

  /**
   * Toggle diff visibility for an issue
   */
  const toggleDiff = (index: number) => {
    const newSet = new Set(expandedDiffs);
    if (newSet.has(index)) {
      newSet.delete(index);
    } else {
      newSet.add(index);
    }
    setExpandedDiffs(newSet);
  };

  /**
   * Format timestamp to readable date
   */
  const formatTimestamp = (iso: string): string => {
    const date = new Date(iso);
    return date.toLocaleString();
  };

  /**
   * Calculate quality score (100% - issues percentage)
   */
  const qualityScore = report.total_issues === 0
    ? 100
    : Math.max(0, 100 - (report.total_issues * 5)); // Rough scoring

  /**
   * Get quality score color
   */
  const getQualityColor = (score: number): string => {
    if (score >= 80) return '#4caf50'; // Green
    if (score >= 60) return '#ff9800'; // Orange
    return '#f44336'; // Red
  };

  /**
   * Calculate issue percentages
   */
  const errorPercent = report.total_issues === 0
    ? 0
    : Math.round((report.errors / report.total_issues) * 100);
  const warningPercent = report.total_issues === 0
    ? 0
    : Math.round((report.warnings / report.total_issues) * 100);
  const infoPercent = report.total_issues === 0
    ? 0
    : Math.round((report.infos / report.total_issues) * 100);

  return (
    <div className="validation-report">
      {/* Report Header */}
      <div className="report-header">
        <h2>Validation Report</h2>
        <button
          className="export-btn"
          onClick={onExport}
          title="Export report"
          aria-label="Export report"
        >
          ⬇️ Export
        </button>
      </div>

      {/* Report Info */}
      <div className="report-info">
        <div className="info-row">
          <span className="label">Target:</span>
          <span className="value" title={report.target}>{report.target}</span>
        </div>
        <div className="info-row">
          <span className="label">Language:</span>
          <span className="value">{report.language}</span>
        </div>
        <div className="info-row">
          <span className="label">Validator:</span>
          <span className="value">{report.validator}</span>
        </div>
        <div className="info-row">
          <span className="label">Scanned:</span>
          <span className="value">{formatTimestamp(report.timestamp)}</span>
        </div>
      </div>

      {/* Quality Score */}
      <div className="quality-section">
        <div className="quality-score">
          <div
            className="score-circle"
            style={{
              background: `conic-gradient(${getQualityColor(qualityScore)} 0deg ${(qualityScore / 100) * 360}deg, #e0e0e0 ${(qualityScore / 100) * 360}deg 360deg)`
            }}
          >
            <div className="score-text">
              <span className="score-value">{Math.round(qualityScore)}</span>
              <span className="score-label">Score</span>
            </div>
          </div>
          <p className="quality-message">
            {qualityScore >= 80 && '✅ Good code quality'}
            {qualityScore >= 60 && qualityScore < 80 && '⚠️ Some issues found'}
            {qualityScore < 60 && '❌ Multiple issues to fix'}
          </p>
        </div>
      </div>

      {/* Statistics */}
      <div className="statistics-section">
        <h3>Issue Summary</h3>

        <div className="stat-cards">
          <div className="stat-card error">
            <div className="stat-number">{report.errors}</div>
            <div className="stat-label">Errors</div>
            <div className="stat-bar">
              <div className="stat-bar-fill" style={{ width: `${Math.min(100, (report.errors / Math.max(report.total_issues, 1)) * 100)}%` }} />
            </div>
          </div>

          <div className="stat-card warning">
            <div className="stat-number">{report.warnings}</div>
            <div className="stat-label">Warnings</div>
            <div className="stat-bar">
              <div className="stat-bar-fill" style={{ width: `${Math.min(100, (report.warnings / Math.max(report.total_issues, 1)) * 100)}%` }} />
            </div>
          </div>

          <div className="stat-card info">
            <div className="stat-number">{report.infos}</div>
            <div className="stat-label">Info</div>
            <div className="stat-bar">
              <div className="stat-bar-fill" style={{ width: `${Math.min(100, (report.infos / Math.max(report.total_issues, 1)) * 100)}%` }} />
            </div>
          </div>
        </div>

        {/* Total Issues */}
        <div className="total-issues">
          <span className="total-label">Total Issues:</span>
          <span className="total-value">{report.total_issues}</span>
        </div>
      </div>

      {/* Distribution Chart */}
      {report.total_issues > 0 && (
        <div className="distribution-section">
          <h3>Issue Distribution</h3>
          <div className="pie-chart">
            <svg viewBox="0 0 100 100" className="pie">
              {/* Error segment */}
              {report.errors > 0 && (
                <circle
                  cx="50"
                  cy="50"
                  r="40"
                  fill="none"
                  stroke="#f44336"
                  strokeWidth="10"
                  strokeDasharray={`${(report.errors / report.total_issues) * 251.2} 251.2`}
                  transform="rotate(-90 50 50)"
                  className="pie-segment"
                />
              )}
              {/* Warning segment */}
              {report.warnings > 0 && (
                <circle
                  cx="50"
                  cy="50"
                  r="40"
                  fill="none"
                  stroke="#ff9800"
                  strokeWidth="10"
                  strokeDasharray={`${(report.warnings / report.total_issues) * 251.2} 251.2`}
                  strokeDashoffset={`-${(report.errors / report.total_issues) * 251.2}`}
                  transform="rotate(-90 50 50)"
                  className="pie-segment"
                />
              )}
              {/* Info segment */}
              {report.infos > 0 && (
                <circle
                  cx="50"
                  cy="50"
                  r="40"
                  fill="none"
                  stroke="#2196f3"
                  strokeWidth="10"
                  strokeDasharray={`${(report.infos / report.total_issues) * 251.2} 251.2`}
                  strokeDashoffset={`-${((report.errors + report.warnings) / report.total_issues) * 251.2}`}
                  transform="rotate(-90 50 50)"
                  className="pie-segment"
                />
              )}
            </svg>
            <div className="chart-legend">
              <div className="legend-item">
                <span className="legend-color" style={{ backgroundColor: '#f44336' }} />
                <span>{report.errors} Errors ({errorPercent}%)</span>
              </div>
              <div className="legend-item">
                <span className="legend-color" style={{ backgroundColor: '#ff9800' }} />
                <span>{report.warnings} Warnings ({warningPercent}%)</span>
              </div>
              <div className="legend-item">
                <span className="legend-color" style={{ backgroundColor: '#2196f3' }} />
                <span>{report.infos} Info ({infoPercent}%)</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Empty State */}
      {report.total_issues === 0 && (
        <div className="no-issues">
          <p>✅ No issues found!</p>
          <p>Your code meets all validation criteria.</p>
        </div>
      )}

      {/* Detailed Issues List */}
      {results.length > 0 && (
        <div className="detailed-issues-section">
          <h3>Detailed Issues</h3>
          <div className="issues-list">
            {results.map((result, index) => (
              <div key={index} className={`issue-item severity-${result.severity}`}>
                <div className="issue-header">
                  <span className={`severity-badge severity-${result.severity}`}>
                    {result.severity === 'error' && '❌ ERROR'}
                    {result.severity === 'warning' && '⚠️ WARNING'}
                    {result.severity === 'info' && 'ℹ️ INFO'}
                  </span>
                  {result.rule && (
                    <span className="rule-badge">{result.rule}</span>
                  )}
                  {result.diff && (
                    <button
                      className="diff-toggle-btn"
                      onClick={() => toggleDiff(index)}
                      title={expandedDiffs.has(index) ? 'Hide changes' : 'Show changes'}
                    >
                      {expandedDiffs.has(index) ? '▼' : '▶'} Changes
                    </button>
                  )}
                </div>
                <div className="issue-location">
                  <span className="file">{result.file}</span>
                  <span className="line-col">
                    {result.line}:{result.column}
                  </span>
                </div>
                <div className="issue-message">{result.message}</div>
                {result.diff && expandedDiffs.has(index) && (
                  <div className="issue-diff">
                    <pre className="diff-content">{result.diff}</pre>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ValidationReport;
