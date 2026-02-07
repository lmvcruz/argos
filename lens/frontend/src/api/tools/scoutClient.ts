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
   * Get workflow history from CI executions
   */
  async getWorkflows(filter?: WorkflowFilter): Promise<WorkflowsResponse> {
    try {
      const params = new URLSearchParams();
      if (filter?.status) params.append('status', filter.status);
      if (filter?.limit) params.append('limit', filter.limit.toString());

      const url = `${this.baseUrl}/api/ci/executions${params.toString() ? `?${params.toString()}` : ''}`;

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);

      const response = await fetch(url, {
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`Failed to fetch workflows: ${response.statusText}`);
      }

      const data = await response.json();
      
      // Map CI executions to Workflow format
      const workflows: Workflow[] = (data.executions || []).map((exec: any) => ({
        id: exec.id?.toString() || '',
        name: exec.workflow || 'Unknown Workflow',
        run_number: exec.id || 0,
        branch: 'main',
        status: 'completed' as const,
        result: (exec.failed === 0 ? 'passed' : 'failed') as const,
        duration: exec.duration || 0,
        started_at: exec.timestamp || new Date().toISOString(),
        url: '',
        jobs: [],
      }));

      return {
        workflows,
        sync_status: {
          last_sync: new Date().toISOString(),
          is_syncing: false,
          next_sync: new Date(Date.now() + 3600000).toISOString(),
        },
        total: workflows.length,
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error(`Workflow fetch timeout (${this.timeout}ms)`);
      }
      throw error;
    }
  }

  /**
   * Get workflow details (mock - use CI executions data)
   */
  async getWorkflow(workflowId: string): Promise<Workflow> {
    const response = await fetch(`${this.baseUrl}/api/ci/executions`);
    if (!response.ok) {
      throw new Error(`Failed to get workflow: ${response.statusText}`);
    }
    const data = await response.json();
    const execution = (data.executions || []).find((e: any) => e.id?.toString() === workflowId);
    
    if (!execution) {
      throw new Error(`Workflow ${workflowId} not found`);
    }

    return {
      id: execution.id?.toString() || '',
      name: execution.workflow || 'Unknown',
      run_number: execution.id || 0,
      branch: 'main',
      status: 'completed',
      result: (execution.failed === 0 ? 'passed' : 'failed') as const,
      duration: execution.duration || 0,
      started_at: execution.timestamp || new Date().toISOString(),
      url: '',
      jobs: [],
    };
  }

  /**
   * Get workflow logs (placeholder - Scout logs not yet integrated)
   */
  async getWorkflowLogs(workflowId: string): Promise<string> {
    // This would require Scout integration to fetch actual logs
    return `Logs for workflow ${workflowId} not yet available. Run 'scout ci sync' to populate data.`;
  }

  /**
   * Trigger workflow re-run (placeholder)
   */
  async triggerWorkflow(workflowId: string): Promise<Workflow> {
    throw new Error('Workflow trigger not yet implemented. Use Scout CLI instead.');
  }

  /**
   * Get sync status from CI sync endpoint
   */
  async getSyncStatus(): Promise<{ last_sync: string; is_syncing: boolean; next_sync: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/api/ci/statistics`);
      if (!response.ok) {
        return {
          last_sync: 'Never',
          is_syncing: false,
          next_sync: new Date(Date.now() + 3600000).toISOString(),
        };
      }
      // Return default sync status
      return {
        last_sync: new Date().toISOString(),
        is_syncing: false,
        next_sync: new Date(Date.now() + 3600000).toISOString(),
      };
    } catch {
      return {
        last_sync: 'Never',
        is_syncing: false,
        next_sync: new Date(Date.now() + 3600000).toISOString(),
      };
    }
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
