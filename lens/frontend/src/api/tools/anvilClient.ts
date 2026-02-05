/**
 * Anvil API Client
 * Handles code analysis requests and responses
 */

import type { AnvilAnalysisRequest, AnvilAnalysisResponse, AnvilIssue } from '../types';

export class AnvilClient {
  private baseUrl: string;
  private timeout: number;

  constructor(baseUrl: string = 'http://localhost:8000', timeout: number = 600000) {
    this.baseUrl = baseUrl;
    this.timeout = timeout;
  }

  /**
   * Analyze code quality and style issues
   */
  async analyze(request: AnvilAnalysisRequest): Promise<AnvilAnalysisResponse> {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);

      const response = await fetch(`${this.baseUrl}/api/anvil/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`Anvil analysis failed: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error(`Anvil analysis timeout (${this.timeout}ms)`);
      }
      throw error;
    }
  }

  /**
   * Get current analysis status
   */
  async getStatus(): Promise<{ status: string; progress?: number }> {
    const response = await fetch(`${this.baseUrl}/api/anvil/status`);
    if (!response.ok) {
      throw new Error(`Failed to get Anvil status: ${response.statusText}`);
    }
    return await response.json();
  }

  /**
   * List files in a directory
   */
  async listFiles(rootPath: string): Promise<any> {
    try {
      const params = new URLSearchParams({ root: rootPath });
      const response = await fetch(`${this.baseUrl}/api/anvil/list-files?${params}`);
      if (!response.ok) {
        throw new Error(`Failed to list files: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error(`File listing timeout (${this.timeout}ms)`);
      }
      throw error;
    }
  }

  /**
   * Cancel ongoing analysis
   */
  async cancel(): Promise<void> {
    const response = await fetch(`${this.baseUrl}/api/anvil/cancel`, {
      method: 'POST',
    });
    if (!response.ok) {
      throw new Error(`Failed to cancel Anvil analysis: ${response.statusText}`);
    }
  }

  /**
   * Get severity stats
   */
  getSeverityStats(issues: AnvilIssue[]) {
    return {
      errors: issues.filter((i) => i.severity === 'error').length,
      warnings: issues.filter((i) => i.severity === 'warning').length,
      info: issues.filter((i) => i.severity === 'info').length,
      total: issues.length,
    };
  }

  /**
   * Filter issues by severity
   */
  filterBySeverity(
    issues: AnvilIssue[],
    severity: 'error' | 'warning' | 'info'
  ): AnvilIssue[] {
    return issues.filter((i) => i.severity === severity);
  }

  /**
   * Filter issues by file
   */
  filterByFile(issues: AnvilIssue[], file: string): AnvilIssue[] {
    return issues.filter((i) => i.file.includes(file));
  }
}

export const anvilClient = new AnvilClient();
