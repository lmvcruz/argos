/**
 * Centralized logging utility for frontend.
 *
 * Logs messages to:
 * 1. Browser console
 * 2. Backend API (persisted to frontend.log)
 * 3. Local storage (for offline support)
 */

export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogMessage {
  level: LogLevel;
  message: string;
  timestamp: string;
  data?: any;
}

class FrontendLogger {
  private readonly backendUrl: string;
  private readonly logKey: string = 'lens:logs';
  private readonly maxLocalLogs: number = 100;

  constructor(backendUrl: string = '') {
    this.backendUrl = backendUrl || '';
  }

  /**
   * Log a debug message.
   */
  debug(message: string, data?: any): void {
    this.log('debug', message, data);
  }

  /**
   * Log an info message.
   */
  info(message: string, data?: any): void {
    this.log('info', message, data);
  }

  /**
   * Log a warning message.
   */
  warn(message: string, data?: any): void {
    this.log('warn', message, data);
  }

  /**
   * Log an error message.
   */
  error(message: string, data?: any): void {
    this.log('error', message, data);
  }

  /**
   * Central log method.
   */
  private log(level: LogLevel, message: string, data?: any): void {
    const timestamp = new Date().toISOString();
    const logMessage: LogMessage = {
      level,
      message,
      timestamp,
      data,
    };

    // Log to console
    const consoleMethod = level === 'warn' ? 'warn' : level === 'error' ? 'error' : 'log';
    console[consoleMethod as any](
      `[${timestamp}] [${level.toUpperCase()}] ${message}`,
      data || ''
    );

    // Save to local storage
    this.saveToLocalStorage(logMessage);

    // Send to backend (async, don't wait)
    this.sendToBackend(logMessage).catch((err) => {
      console.error('Failed to send log to backend:', err);
    });
  }

  /**
   * Save log to local storage.
   */
  private saveToLocalStorage(logMessage: LogMessage): void {
    try {
      const storedLogs = this.getLocalLogs();
      storedLogs.push(logMessage);

      // Keep only the last N logs
      const trimmedLogs = storedLogs.slice(-this.maxLocalLogs);
      localStorage.setItem(this.logKey, JSON.stringify(trimmedLogs));
    } catch (err) {
      console.error('Failed to save log to local storage:', err);
    }
  }

  /**
   * Get all logs from local storage.
   */
  getLocalLogs(): LogMessage[] {
    try {
      const stored = localStorage.getItem(this.logKey);
      return stored ? JSON.parse(stored) : [];
    } catch (err) {
      console.error('Failed to read logs from local storage:', err);
      return [];
    }
  }

  /**
   * Clear local storage logs.
   */
  clearLocalLogs(): void {
    try {
      localStorage.removeItem(this.logKey);
    } catch (err) {
      console.error('Failed to clear local logs:', err);
    }
  }

  /**
   * Send log to backend.
   */
  private async sendToBackend(logMessage: LogMessage): Promise<void> {
    try {
      const response = await fetch('/api/logs/frontend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(logMessage),
      });

      if (!response.ok) {
        console.error(`Failed to log to backend: ${response.status}`);
      }
    } catch (err) {
      // Silently fail - don't want logging to break the app
      console.error('Failed to send log to backend:', err);
    }
  }

  /**
   * Get log file from backend.
   */
  async getBackendLogs(logName: string = 'backend.log', lines: number = 100): Promise<string> {
    try {
      const response = await fetch(
        `/api/logs/read/${encodeURIComponent(logName)}?lines=${lines}`
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch logs: ${response.status}`);
      }

      const data = await response.json();
      return data.content;
    } catch (err) {
      console.error('Failed to fetch backend logs:', err);
      throw err;
    }
  }

  /**
   * Get list of available logs from backend.
   */
  async getLogsList(): Promise<
    Array<{ name: string; path: string; size: number; modified: string }>
  > {
    try {
      const response = await fetch('/api/logs/list');

      if (!response.ok) {
        throw new Error(`Failed to fetch logs list: ${response.status}`);
      }

      const data = await response.json();
      return data.logs || [];
    } catch (err) {
      console.error('Failed to fetch logs list:', err);
      throw err;
    }
  }

  /**
   * Get logs configuration from backend.
   */
  async getLogsConfig(): Promise<{ log_dir: string; backend_log: string; frontend_log: string }> {
    try {
      const response = await fetch('/api/logs/config');

      if (!response.ok) {
        throw new Error(`Failed to fetch logs config: ${response.status}`);
      }

      return await response.json();
    } catch (err) {
      console.error('Failed to fetch logs config:', err);
      throw err;
    }
  }

  /**
   * Delete a log file from backend.
   */
  async deleteLog(logName: string): Promise<void> {
    try {
      const response = await fetch(`/api/logs/${encodeURIComponent(logName)}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`Failed to delete log: ${response.status}`);
      }

      this.info(`Deleted log file: ${logName}`);
    } catch (err) {
      console.error('Failed to delete log:', err);
      throw err;
    }
  }

  /**
   * Clear (truncate) a backend log file.
   */
  async clearBackendLog(logName: string = 'backend.log'): Promise<void> {
    try {
      const response = await fetch(`/api/logs/clear/${encodeURIComponent(logName)}`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error(`Failed to clear log: ${response.status}`);
      }

      this.info(`Cleared log file: ${logName}`);
    } catch (err) {
      console.error('Failed to clear backend log:', err);
      throw err;
    }
  }
}

// Create singleton instance
const logger = new FrontendLogger();

export default logger;
