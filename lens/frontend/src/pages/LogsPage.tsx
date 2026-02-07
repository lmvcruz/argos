/**
 * LogsPage - Display centralized logs from backend and frontend.
 *
 * Features:
 * - View backend logs
 * - View frontend logs
 * - Search and filter logs
 * - Download logs
 * - Configure log directory
 */

import React, { useState, useEffect } from 'react';
import { LogsViewer } from '../components/LogsViewer';
import logger from '../utils/logger';
import './LogsPage.css';

interface LogsConfig {
  log_dir: string;
  backend_log: string;
  frontend_log: string;
}

/**
 * LogsPage - Main page for viewing and managing logs
 */
export const LogsPage: React.FC = () => {
  const [logsConfig, setLogsConfig] = useState<LogsConfig | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadLogsConfig();
    logger.info('Opened logs page');
  }, []);

  async function loadLogsConfig() {
    setIsLoading(true);
    try {
      const config = await logger.getLogsConfig();
      setLogsConfig(config);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load logs config');
      logger.error('Failed to load logs config', err);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="logs-page">
      <div className="page-container">
        {isLoading && (
          <div className="loading-spinner">
            <div className="spinner"></div>
            Loading logs configuration...
          </div>
        )}

        {error && (
          <div className="error-banner">
            <strong>Error:</strong> {error}
            <button onClick={loadLogsConfig} className="retry-btn">
              Retry
            </button>
          </div>
        )}

        {logsConfig && (
          <>
            <div className="logs-info-section">
              <h2>📋 Logs & Diagnostics</h2>
              <div className="info-card">
                <p>
                  <strong>Log Directory:</strong>{' '}
                  <code className="log-path">{logsConfig.log_dir}</code>
                </p>
                <p className="info-text">
                  All backend and frontend logs are centralized in this directory for easy
                  monitoring and debugging.
                </p>
              </div>
            </div>

            <LogsViewer autoRefresh={true} refreshInterval={5000} />
          </>
        )}
      </div>
    </div>
  );
};

export default LogsPage;
