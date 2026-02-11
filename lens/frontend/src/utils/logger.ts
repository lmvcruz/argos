/**
 * Centralized logging utility for frontend.
 *
 * Logs messages to:
 * 1. Browser console (immediate)
 * 2. Local storage (for offline support)
 * 3. Backend API (batched every 5 seconds to prevent flooding)
 *
 * Key features:
 * - Batching: Collects logs and sends them in batches (1 HTTP request per batch)
 * - Deduplication: Prevents React Strict Mode from creating duplicate logs
 * - Rate limiting: Max 50 logs per batch to prevent overload
 */

export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogMessage {
  level: LogLevel;
  message: string;
  timestamp: string;
  data?: any;
}

interface BatchedLog extends LogMessage {
  hash: string; // For deduplication
}

class FrontendLogger {
  private readonly backendUrl: string;
  private readonly logKey: string = 'lens:logs';
  private readonly maxLocalLogs: number = 100;

  // Batching configuration
  private readonly batchIntervalMs: number = 5000; // Send batch every 5 seconds
  private readonly maxBatchSize: number = 50; // Max logs per batch
  private readonly dedupeWindowMs: number = 1000; // Dedupe logs within 1 second

  // Batch state
  private logQueue: BatchedLog[] = [];
  private recentHashes: Map<string, number> = new Map(); // hash -> timestamp
  private batchTimer: ReturnType<typeof setInterval> | null = null;
  private isSending: boolean = false;

  constructor(backendUrl: string = '') {
    this.backendUrl = backendUrl || '';
    this.startBatchTimer();

    // Flush remaining logs when page unloads
    if (typeof window !== 'undefined') {
      window.addEventListener('beforeunload', () => this.flushBatch());
    }
  }

  /**
   * Start the batch timer to send logs periodically.
   */
  private startBatchTimer(): void {
    if (this.batchTimer) return;

    this.batchTimer = setInterval(() => {
      this.flushBatch();
    }, this.batchIntervalMs);
  }

  /**
   * Generate a hash for deduplication (message + level, ignoring timestamp).
   */
  private generateHash(level: LogLevel, message: string, data?: any): string {
    const dataStr = data ? JSON.stringify(data) : '';
    return `${level}:${message}:${dataStr}`;
  }

  /**
   * Check if a log is a duplicate (same message within deduplication window).
   */
  private isDuplicate(hash: string): boolean {
    const now = Date.now();
    const lastSeen = this.recentHashes.get(hash);

    if (lastSeen && now - lastSeen < this.dedupeWindowMs) {
      return true; // Duplicate within window
    }

    // Update the hash timestamp
    this.recentHashes.set(hash, now);

    // Clean up old hashes (older than 10 seconds)
    for (const [h, ts] of this.recentHashes.entries()) {
      if (now - ts > 10000) {
        this.recentHashes.delete(h);
      }
    }

    return false;
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
   * Central log method with batching and deduplication.
   */
  private log(level: LogLevel, message: string, data?: any): void {
    const timestamp = new Date().toISOString();
    const hash = this.generateHash(level, message, data);

    // Log to console immediately (always)
    const consoleMethod = level === 'warn' ? 'warn' : level === 'error' ? 'error' : 'log';
    console[consoleMethod as 'log' | 'warn' | 'error'](
      `[${timestamp}] [${level.toUpperCase()}] ${message}`,
      data || ''
    );

    // Check for duplicates (prevents React Strict Mode double-logging)
    if (this.isDuplicate(hash)) {
      return; // Skip duplicate log
    }

    const logMessage: BatchedLog = {
      level,
      message,
      timestamp,
      data,
      hash,
    };

    // Save to local storage
    this.saveToLocalStorage(logMessage);

    // Add to batch queue (for backend)
    this.addToBatch(logMessage);
  }

  /**
   * Add log to batch queue.
   */
  private addToBatch(logMessage: BatchedLog): void {
    this.logQueue.push(logMessage);

    // If queue is full, flush immediately
    if (this.logQueue.length >= this.maxBatchSize) {
      this.flushBatch();
    }
  }

  /**
   * Flush the batch queue to backend.
   */
  private async flushBatch(): Promise<void> {
    if (this.logQueue.length === 0 || this.isSending) return;

    // Take current queue and reset
    const batch = this.logQueue.splice(0, this.maxBatchSize);
    this.isSending = true;

    try {
      await this.sendBatchToBackend(batch);
    } catch (err) {
      // On failure, logs are already in localStorage, so we don't lose them
      console.error('Failed to send log batch to backend:', err);
    } finally {
      this.isSending = false;
    }
  }

  /**
   * Send a batch of logs to backend in a single request.
   */
  private async sendBatchToBackend(batch: BatchedLog[]): Promise<void> {
    if (batch.length === 0) return;

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);

      // Remove hash before sending (internal use only)
      const logsToSend = batch.map(({ hash, ...log }) => log);

      const response = await fetch('/api/logs/frontend/batch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ logs: logsToSend }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        console.error(`Failed to send log batch: ${response.status}`);
      }
    } catch (err) {
      if ((err as Error).name === 'AbortError') {
        console.warn('Log batch request timed out');
      } else {
        throw err;
      }
    }
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
   * Force flush any pending logs (for testing or cleanup).
   */
  async flush(): Promise<void> {
    await this.flushBatch();
  }

  /**
   * Get pending log count (for debugging).
   */
  getPendingCount(): number {
    return this.logQueue.length;
  }

  /**
   * Get log file from backend.
   */
  async getBackendLogs(logName: string = 'backend.log', lines: number = 100): Promise<string> {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout

      const response = await fetch(
        `/api/logs/read/${encodeURIComponent(logName)}?lines=${lines}`,
        { signal: controller.signal }
      );

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`Failed to fetch logs: ${response.status}`);
      }

      const data = await response.json();
      return data.content;
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        throw new Error('Backend not responding - is the server running?');
      }
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
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout

      const response = await fetch('/api/logs/config', {
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`Failed to fetch logs config: ${response.status}`);
      }

      return await response.json();
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        throw new Error('Backend not responding - is the server running?');
      }
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
