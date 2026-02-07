/**
 * StatsCard component - Display validation statistics and metadata.
 *
 * Shows:
 * - Number of files analyzed
 * - Issue count by severity
 * - Last updated timestamp
 * - Refresh button
 */

import React from 'react';
import './StatsCard.css';

/**
 * StatsCard props
 */
interface StatsCardProps {
  filesAnalyzed?: number;
  errorCount?: number;
  warningCount?: number;
  infoCount?: number;
  lastUpdated?: Date;
  isLoading?: boolean;
  onRefresh?: () => void;
  language?: string;
  validator?: string;
}

/**
 * StatsCard - Display validation statistics
 *
 * Args:
 *   filesAnalyzed: Number of files analyzed
 *   errorCount: Number of errors found
 *   warningCount: Number of warnings found
 *   infoCount: Number of info messages
 *   lastUpdated: When validation was last run
 *   isLoading: Show loading state
 *   onRefresh: Callback when refresh button clicked
 *   language: Selected language
 *   validator: Selected validator name
 */
export const StatsCard: React.FC<StatsCardProps> = ({
  filesAnalyzed = 0,
  errorCount = 0,
  warningCount = 0,
  infoCount = 0,
  lastUpdated,
  isLoading = false,
  onRefresh,
  language,
  validator,
}) => {
  /**
   * Format timestamp to relative time
   */
  const formatTime = (date: Date | undefined): string => {
    if (!date) return 'Never';

    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (seconds < 60) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return `${days}d ago`;
  };

  /**
   * Calculate total issues
   */
  const totalIssues = errorCount + warningCount + infoCount;

  /**
   * Calculate issue distribution percentage
   */
  const getPercentage = (count: number): number => {
    if (totalIssues === 0) return 0;
    return Math.round((count / totalIssues) * 100);
  };

  return (
    <div className="stats-card">
      {/* Header */}
      <div className="stats-header">
        <h3>Statistics</h3>
        {onRefresh && (
          <button
            className="refresh-btn"
            onClick={onRefresh}
            disabled={isLoading}
            aria-label="Refresh statistics"
            title="Refresh statistics"
          >
            {isLoading ? '⟳' : '🔄'}
          </button>
        )}
      </div>

      {/* Validator Info */}
      {(language || validator) && (
        <div className="validator-info">
          {language && (
            <div className="info-item">
              <span className="label">Language:</span>
              <span className="value">{language}</span>
            </div>
          )}
          {validator && (
            <div className="info-item">
              <span className="label">Validator:</span>
              <span className="value">{validator}</span>
            </div>
          )}
        </div>
      )}

      {/* Stats Grid */}
      <div className="stats-grid">
        {/* Files Analyzed */}
        <div className="stat-box">
          <div className="stat-icon">📊</div>
          <div className="stat-content">
            <div className="stat-value">{filesAnalyzed}</div>
            <div className="stat-label">Files Analyzed</div>
          </div>
        </div>

        {/* Total Issues */}
        <div className="stat-box">
          <div className="stat-icon">📈</div>
          <div className="stat-content">
            <div className="stat-value">{totalIssues}</div>
            <div className="stat-label">Total Issues</div>
          </div>
        </div>

        {/* Errors */}
        <div className="stat-box severity-error">
          <div className="stat-icon">❌</div>
          <div className="stat-content">
            <div className="stat-value">{errorCount}</div>
            <div className="stat-label">Errors {totalIssues > 0 && `(${getPercentage(errorCount)}%)`}</div>
          </div>
        </div>

        {/* Warnings */}
        <div className="stat-box severity-warning">
          <div className="stat-icon">⚠️</div>
          <div className="stat-content">
            <div className="stat-value">{warningCount}</div>
            <div className="stat-label">Warnings {totalIssues > 0 && `(${getPercentage(warningCount)}%)`}</div>
          </div>
        </div>

        {/* Info */}
        <div className="stat-box severity-info">
          <div className="stat-icon">ℹ️</div>
          <div className="stat-content">
            <div className="stat-value">{infoCount}</div>
            <div className="stat-label">Info {totalIssues > 0 && `(${getPercentage(infoCount)}%)`}</div>
          </div>
        </div>
      </div>

      {/* Issue Distribution Bar */}
      {totalIssues > 0 && (
        <div className="distribution-bar">
          <div className="bar-label">Distribution:</div>
          <div className="bar-container">
            {errorCount > 0 && (
              <div
                className="bar-segment severity-error"
                style={{ width: `${getPercentage(errorCount)}%` }}
                title={`${errorCount} errors (${getPercentage(errorCount)}%)`}
              />
            )}
            {warningCount > 0 && (
              <div
                className="bar-segment severity-warning"
                style={{ width: `${getPercentage(warningCount)}%` }}
                title={`${warningCount} warnings (${getPercentage(warningCount)}%)`}
              />
            )}
            {infoCount > 0 && (
              <div
                className="bar-segment severity-info"
                style={{ width: `${getPercentage(infoCount)}%` }}
                title={`${infoCount} info (${getPercentage(infoCount)}%)`}
              />
            )}
          </div>
        </div>
      )}

      {/* Last Updated */}
      <div className="last-updated">
        <small>Last updated: {formatTime(lastUpdated)}</small>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="loading-overlay">
          <div className="spinner" />
        </div>
      )}
    </div>
  );
};

export default StatsCard;
