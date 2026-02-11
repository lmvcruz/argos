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

  constructor(baseUrl: string = '', timeout: number = 30000) {
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

      const url = `${this.baseUrl}/api/scout/executions${params.toString() ? `?${params.toString()}` : ''}`;

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

      // Map CI executions to Workflow format with availability data
      const workflows: Workflow[] = (data.executions || []).map((exec: any) => {
        // Map status and conclusion from GitHub Actions
        // Status: queued, in_progress, completed
        // Conclusion: success, failure, cancelled, skipped, neutral, timed_out (only when status=completed)
        let result: 'passed' | 'failed' | 'pending' = 'pending';
        let status: 'completed' | 'in_progress' | 'queued' = 'completed';

        // Check GitHub Actions status field
        if (exec.status === 'in_progress') {
          status = 'in_progress';
          result = 'pending';
        } else if (exec.status === 'queued') {
          status = 'queued';
          result = 'pending';
        } else if (exec.status === 'completed') {
          status = 'completed';
          // When completed, check conclusion field for actual result
          if (exec.conclusion === 'success') {
            result = 'passed';
          } else if (exec.conclusion === 'failure') {
            result = 'failed';
          } else if (exec.conclusion === 'cancelled' || exec.conclusion === 'timed_out') {
            result = 'failed';
          } else {
            // skipped, neutral, or other
            result = 'pending';
          }
        }

        return {
          id: exec.run_id?.toString() || exec.id?.toString() || '',
          name: exec.workflow_name || exec.workflow || 'Unknown Workflow',
          run_number: exec.run_number || exec.run_id || exec.id || 0,
          branch: exec.branch || 'main',
          status: status,
          result: result,
          duration: exec.duration_seconds || exec.duration || 0,
          started_at: exec.started_at || exec.timestamp || new Date().toISOString(),
          url: exec.url || '',
          jobs: [],
          // Extra fields from Scout
          commit_sha: exec.commit_sha,
          // Availability flags
          has_logs: exec.has_logs || false,
          has_parsed_data: exec.has_parsed_data || false,
          logs_downloaded_at: exec.logs_downloaded_at,
          data_parsed_at: exec.data_parsed_at,
        };
      });

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
    const response = await fetch(`${this.baseUrl}/api/scout/workflows/${workflowId}`);
    if (!response.ok) {
      throw new Error(`Failed to get workflow: ${response.statusText}`);
    }
    const data = await response.json();
    const execution = (data.executions || []).find((e: any) => e.id?.toString() === workflowId);

    if (!execution) {
      throw new Error(`Workflow ${workflowId} not found`);
    }

    const result = execution.failed === 0 ? 'passed' : 'failed';
    return {
      id: execution.id?.toString() || '',
      name: execution.workflow || 'Unknown',
      run_number: execution.id || 0,
      branch: 'main',
      status: 'completed',
      result: result as 'passed' | 'failed',
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
  async triggerWorkflow(_workflowId: string): Promise<Workflow> {
    throw new Error('Workflow trigger not yet implemented. Use Scout CLI instead.');
  }

  /**
   * Refresh executions from GitHub (runs 'scout list' to fetch and save metadata)
   */
  async refreshExecutions(params: {
    limit?: number;
  }): Promise<{ success: boolean; saved_count: number; updated_count: number; total_fetched: number }> {
    try {
      const queryParams = new URLSearchParams();
      if (params.limit) queryParams.append('limit', params.limit.toString());

      const response = await fetch(
        `${this.baseUrl}/api/scout/refresh?${queryParams.toString()}`,
        {
          method: 'POST',
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(errorData.detail || `Refresh failed: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('Failed to refresh executions');
    }
  }

  /**
   * Fetch logs for a specific workflow run
   */
  async fetchLogs(runId: number): Promise<{ success: boolean; run_id: number; message: string }> {
    try {
      const response = await fetch(
        `${this.baseUrl}/api/scout/fetch-log/${runId}`,
        {
          method: 'POST',
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(errorData.detail || `Fetch logs failed: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('Failed to fetch logs');
    }
  }

  /**
   * Parse data for a specific workflow run
   */
  async parseData(runId: number): Promise<{
    success: boolean;
    run_id: number;
    message: string;
    data?: any;  // Optional field containing parsed test results, coverage, etc.
    timestamp?: string;
  }> {
    try {
      const response = await fetch(
        `${this.baseUrl}/api/scout/parse-data/${runId}`,
        {
          method: 'POST',
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(errorData.detail || `Parse data failed: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('Failed to parse data');
    }
  }

  /**
   * Get all jobs for a specific workflow run
   */
  async getRunJobs(runId: number): Promise<{
    run_id: number;
    jobs: Array<{
      id: string;
      name: string;
      status: string;
      result: string;
      duration: number;
      runner_os?: string;
      python_version?: string;
      started_at?: string;
      completed_at?: string;
    }>;
    total: number;
  }> {
    try {
      const response = await fetch(
        `${this.baseUrl}/api/scout/runs/${runId}/jobs`
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(errorData.detail || `Failed to get jobs: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('Failed to get jobs for run');
    }
  }

  /**
   * Get logs for a specific workflow run
   */
  async getRunLogs(runId: number): Promise<any> {
    try {
      const response = await fetch(
        `${this.baseUrl}/api/scout/show-log/${runId}`
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(errorData.detail || `Get logs failed: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('Failed to get logs');
    }
  }

  /**
   * Get parsed data for a specific workflow run
   */
  async getParsedData(runId: number): Promise<any> {
    try {
      const response = await fetch(
        `${this.baseUrl}/api/scout/show-data/${runId}`
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(errorData.detail || `Get parsed data failed: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('Failed to get parsed data');
    }
  }

  /**
   * Get sync status from CI sync endpoint
   */
  async getSyncStatus(): Promise<{ last_sync: string; is_syncing: boolean; next_sync: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/api/scout/sync-status`);
      if (!response.ok) {
        const defaultStatus = {
          last_sync: 'Never',
          is_syncing: false,
          next_sync: new Date(Date.now() + 3600000).toISOString(),
        };
        return defaultStatus;
      }
      const data = await response.json();
      return {
        last_sync: data.last_sync || 'Never',
        is_syncing: data.is_syncing || false,
        next_sync: new Date(Date.now() + 3600000).toISOString(), // Placeholder
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
   * Fetch logs for a specific job
   */
  async fetchJobLogs(jobId: number): Promise<{
    success: boolean;
    job_id: number;
    run_id: number;
    job_name: string;
    has_log: boolean;
    log_content?: string;
    message: string;
  }> {
    try {
      const response = await fetch(
        `${this.baseUrl}/api/scout/fetch-job-log/${jobId}`,
        {
          method: 'POST',
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(errorData.detail || `Fetch job logs failed: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('Failed to fetch job logs');
    }
  }

  /**
   * Parse data for a specific job
   */
  async parseJobData(jobId: number): Promise<{
    success: boolean;
    job_id: number;
    message: string;
    data?: any;
    timestamp?: string;
  }> {
    try {
      const response = await fetch(
        `${this.baseUrl}/api/scout/parse-job-data/${jobId}`,
        {
          method: 'POST',
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(errorData.detail || `Parse job data failed: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('Failed to parse job data');
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

// Use empty baseUrl to leverage Vite proxy during development
// In production, the app is served from the same origin as the API
export const scoutClient = new ScoutClient('');
