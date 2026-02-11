/**
 * LogsViewer component - Display backend and frontend logs.
 *
 * Features:
 * - View backend and frontend logs
 * - Search/filter logs
 * - Download logs
 * - Clear logs
 * - Real-time updates
 */

import React, { useState, useEffect } from 'react';
import logger from '../utils';
import './LogsViewer.css';

interface LogFile {
  name: string;
  path: string;
  size: number;
  modified: string;
}

interface LogsViewerProps {
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export const LogsViewer: React.FC<LogsViewerProps> = ({
  autoRefresh = true,
  refreshInterval = 5000,
}) => {
  const [logFiles, setLogFiles] = useState<LogFile[]>([]);
  const [selectedLog, setSelectedLog] = useState<string>('backend.log');
  const [logContent, setLogContent] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [logDir, setLogDir] = useState<string>('');
  const [lines, setLines] = useState<number>(100);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [logLevel, setLogLevel] = useState<string>('all');

  // Load log files list
  useEffect(() => {
    loadLogsList();

    if (autoRefresh) {
      const interval = setInterval(loadLogsList, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval]);

  // Load selected log
  useEffect(() => {
    if (selectedLog) {
      loadLogContent();
    }
  }, [selectedLog, lines]);

  async function loadLogsList() {
    try {
      const config = await logger.getLogsConfig();
      setLogDir(config.log_dir);

      const logs = await logger.getLogsList();
      setLogFiles(logs);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load logs list');
    }
  }

  async function loadLogContent() {
    setIsLoading(true);
    try {
      const content = await logger.getBackendLogs(selectedLog, lines);
      setLogContent(content);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load log content');
    } finally {
      setIsLoading(false);
    }
  }

  async function handleDeleteLog(logName: string) {
    if (!window.confirm(`Delete ${logName}?`)) {
      return;
    }

    try {
      await logger.deleteLog(logName);
      await loadLogsList();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete log');
    }
  }

  function handleDownloadLog() {
    const element = document.createElement('a');
    const file = new Blob([logContent], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = selectedLog;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  }

  async function handleClearLocalLogs() {
    if (!window.confirm('Clear frontend logs? (Backend logs require server restart to clear safely)')) {
      return;
    }

    // Show loading state
    setIsLoading(true);
    setError(null);

    try {
      // Clear frontend logs only (safe while server is running)
      await Promise.resolve(logger.clearLocalLogs());

      logger.info('Frontend logs cleared');

      // Refresh log content to reflect cleared logs
      await loadLogContent();
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error';
      setError(`Failed to clear logs: ${errorMsg}`);
      console.error('Failed to clear logs:', err);
    } finally {
      setIsLoading(false);
    }
  }

  function getFilteredContent(): string {
    let filtered = logContent;

    // Filter by log level
    if (logLevel !== 'all') {
      const lines = filtered.split('\n');
      filtered = lines.filter((line) => line.includes(`[${logLevel.toUpperCase()}]`)).join('\n');
    }

    // Filter by search term
    if (searchTerm) {
      const lines = filtered.split('\n');
      filtered = lines.filter((line) => line.toLowerCase().includes(searchTerm.toLowerCase())).join('\n');
    }

    return filtered;
  }

  const filteredContent = getFilteredContent();
  const displayLines = filteredContent.split('\n').length;

  return (
    <div className="logs-viewer">
      <div className="logs-header">
        <h2>📋 Logs</h2>
        <div className="logs-info">
          <span className="log-dir">📁 {logDir}</span>
        </div>
      </div>

      {error && <div className="logs-error">{error}</div>}

      <div className="logs-container">
        {/* Left Panel: Log Files List */}
        <div className="logs-panel left-logs-panel">
          <div className="logs-panel-header">
            <h3>Log Files</h3>
            <button onClick={loadLogsList} className="refresh-btn" title="Refresh">
              🔄
            </button>
          </div>

          <div className="logs-list">
            {logFiles.length === 0 ? (
              <p className="no-logs">No log files</p>
            ) : (
              logFiles.map((log) => (
                <div
                  key={log.name}
                  className={`log-item ${selectedLog === log.name ? 'active' : ''}`}
                  onClick={() => setSelectedLog(log.name)}
                >
                  <div className="log-name">{log.name}</div>
                  <div className="log-meta">
                    <span className="log-size">{(log.size / 1024).toFixed(1)} KB</span>
                    <span className="log-time">{new Date(log.modified).toLocaleString()}</span>
                  </div>
                  <button
                    className="delete-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteLog(log.name);
                    }}
                    title="Delete log"
                  >
                    ✕
                  </button>
                </div>
              ))
            )}
          </div>

          <div className="logs-actions">
            <button
              onClick={handleClearLocalLogs}
              className="action-btn"
              disabled={isLoading}
              title="Clear frontend logs (restart server to clear backend logs)"
            >
              {isLoading ? 'Clearing...' : 'Clear Frontend Logs'}
            </button>
          </div>
        </div>

        {/* Right Panel: Log Content */}
        <div className="logs-panel right-logs-panel">
          <div className="logs-panel-header">
            <h3>{selectedLog || 'No log selected'}</h3>
            <div className="log-controls">
              <select value={lines} onChange={(e) => setLines(Number(e.target.value))}>
                <option value={50}>Last 50 lines</option>
                <option value={100}>Last 100 lines</option>
                <option value={200}>Last 200 lines</option>
                <option value={500}>Last 500 lines</option>
                <option value={1000}>Last 1000 lines</option>
              </select>

              <button onClick={handleDownloadLog} className="download-btn" title="Download">
                ⬇️
              </button>
              <button onClick={loadLogContent} className="refresh-btn" title="Refresh">
                🔄
              </button>
            </div>
          </div>

          <div className="log-filters">
            <input
              type="text"
              placeholder="Search logs..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input"
            />
            <select value={logLevel} onChange={(e) => setLogLevel(e.target.value)}>
              <option value="all">All levels</option>
              <option value="debug">DEBUG</option>
              <option value="info">INFO</option>
              <option value="warn">WARN</option>
              <option value="error">ERROR</option>
            </select>
          </div>

          <div className="log-content">
            {isLoading ? (
              <div className="loading">Loading...</div>
            ) : (
              <>
                {selectedLog && (
                  <div className="log-meta-info">
                    Showing {displayLines} lines
                    {searchTerm && ` (filtered from ${logContent.split('\n').length})`}
                  </div>
                )}
                <pre className="log-text">{filteredContent || 'No log content'}</pre>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default LogsViewer;
