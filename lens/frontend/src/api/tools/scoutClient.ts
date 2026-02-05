/**
 * Scout API Client
 * Handles CI workflow requests and responses
 */

import type { WorkflowsResponse, Workflow } from '../types';

export interface WorkflowFilter {
  branch?: string;
  status?: 'completed' | 'in_progress' | 'queued';
  limit?: number;
  offset?: number;
}

export class ScoutClient {
  private baseUrl: string;
  private timeout: number;

  constructor(baseUrl: string = 'http://localhost:8000', timeout: number = 30000) {
    this.baseUrl = baseUrl;
    this.timeout = timeout;
  }

  /**
   * Get workflow history
   */
  async getWorkflows(filter?: WorkflowFilter): Promise<WorkflowsResponse> {
    try {
      const params = new URLSearchParams();
      if (filter?.branch) params.append('branch', filter.branch);
      if (filter?.status) params.append('status', filter.status);
      if (filter?.limit) params.append('limit', filter.limit.toString());
      if (filter?.offset) params.append('offset', filter.offset.toString());

      const url = `${this.baseUrl}/api/scout/workflows${params.toString() ? `?${params.toString()}` : ''}`;

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);

      const response = await fetch(url, {
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`Failed to fetch workflows: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error(`Workflow fetch timeout (${this.timeout}ms)`);
      }
      throw error;
    }
  }

  /**
   * Get workflow details
   */
  async getWorkflow(workflowId: string): Promise<Workflow> {
    const response = await fetch(`${this.baseUrl}/api/scout/workflows/${workflowId}`);
    if (!response.ok) {
      throw new Error(`Failed to get workflow: ${response.statusText}`);
    }
    return await response.json();
  }

  /**
   * Get workflow logs
   */
  async getWorkflowLogs(workflowId: string): Promise<string> {
    const response = await fetch(`${this.baseUrl}/api/scout/workflows/${workflowId}/logs`);
    if (!response.ok) {
      throw new Error(`Failed to get workflow logs: ${response.statusText}`);
    }
    return await response.text();
  }

  /**
   * Trigger workflow re-run
   */
  async triggerWorkflow(workflowId: string): Promise<Workflow> {
    const response = await fetch(`${this.baseUrl}/api/scout/workflows/${workflowId}/trigger`, {
      method: 'POST',
    });
    if (!response.ok) {
      throw new Error(`Failed to trigger workflow: ${response.statusText}`);
    }
    return await response.json();
  }

  /**
   * Get sync status
   */
  async getSyncStatus(): Promise<{ last_sync: string; is_syncing: boolean; next_sync: string }> {
    const response = await fetch(`${this.baseUrl}/api/scout/sync-status`);
    if (!response.ok) {
      throw new Error(`Failed to get sync status: ${response.statusText}`);
    }
    return await response.json();
  }

  /**
   * Calculate success rate
   */
  getSuccessRate(workflows: Workflow[]): number {
    if (workflows.length === 0) return 100;
    const passed = workflows.filter((w) => w.result === 'passed').length;
    return Math.round((passed / workflows.length) * 100);
  }

  /**
   * Get workflows by status
   */
  getByStatus(workflows: Workflow[], status: 'completed' | 'in_progress' | 'queued') {
    return workflows.filter((w) => w.status === status);
  }

  /**
   * Get workflows by result
   */
  getByResult(workflows: Workflow[], result: 'passed' | 'failed' | 'pending') {
    return workflows.filter((w) => w.result === result);
  }
}

export const scoutClient = new ScoutClient();
