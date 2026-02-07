/**
 * Verdict API Client
 * Handles test execution requests and responses
 */

import type { TestExecutionRequest, TestExecutionResponse } from '../types';

interface DiscoveredTest {
  file: string;
  name: string;
  id: string;
  status: 'not-run' | 'passed' | 'failed' | 'skipped';
}

export class VerdictClient {
  private baseUrl: string;
  private timeout: number;

  constructor(baseUrl: string = 'http://localhost:8000', timeout: number = 600000) {
    this.baseUrl = baseUrl;
    this.timeout = timeout;
  }

  /**
   * Discover tests in project without executing
   */
  async discover(projectPath: string): Promise<{ tests: DiscoveredTest[]; total: number; timestamp: string }> {
    try {
      const params = new URLSearchParams();
      params.append('project_path', projectPath);

      const response = await fetch(`${this.baseUrl}/api/verdict/discover?${params.toString()}`);
      if (!response.ok) {
        throw new Error(`Test discovery failed: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      throw error;
    }
  }

  /**
   * Execute test suite
   */
  async execute(request: TestExecutionRequest): Promise<TestExecutionResponse> {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);

      const response = await fetch(`${this.baseUrl}/api/verdict/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`Test execution failed: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error(`Test execution timeout (${this.timeout}ms)`);
      }
      throw error;
    }
  }

  /**
   * Get test execution status
   */
  async getStatus(): Promise<{ status: string; progress?: number; passed?: number; failed?: number }> {
    const response = await fetch(`${this.baseUrl}/api/verdict/status`);
    if (!response.ok) {
      throw new Error(`Failed to get test status: ${response.statusText}`);
    }
    return await response.json();
  }

  /**
   * Cancel ongoing test execution
   */
  async cancel(): Promise<void> {
    const response = await fetch(`${this.baseUrl}/api/verdict/cancel`, {
      method: 'POST',
    });
    if (!response.ok) {
      throw new Error(`Failed to cancel test execution: ${response.statusText}`);
    }
  }

  /**
   * Get code coverage
   */
  async getCoverage(): Promise<{ coverage: number; lines: number; covered: number }> {
    const response = await fetch(`${this.baseUrl}/api/verdict/coverage`);
    if (!response.ok) {
      throw new Error(`Failed to get coverage: ${response.statusText}`);
    }
    return await response.json();
  }

  /**
   * Get test results by status
   */
  getByStatus(
    results: TestExecutionResponse,
    status: 'passed' | 'failed' | 'flaky' | 'skipped'
  ) {
    return results.tests.filter((t) => t.status === status);
  }

  /**
   * Calculate pass rate
   */
  getPassRate(results: TestExecutionResponse): number {
    if (results.summary.total === 0) return 100;
    return Math.round(
      (results.summary.passed / results.summary.total) * 100
    );
  }

  /**
   * Get flaky test percentage
   */
  getFlakyRate(results: TestExecutionResponse): number {
    if (results.summary.total === 0) return 0;
    return Math.round(
      (results.summary.flaky / results.summary.total) * 100
    );
  }
}

export const verdictClient = new VerdictClient();
