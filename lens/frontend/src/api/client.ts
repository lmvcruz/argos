/**
 * API Integration Layer for Lens Frontend
 *
 * Provides typed methods for communicating with the Lens backend server.
 */

import axios, { AxiosInstance } from 'axios';

interface ActionRequest {
  action_type: string;
  project_path: string;
  parameters: Record<string, any>;
}

interface ActionResponse {
  action_id: string;
  action_type: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  result: Record<string, any>;
  error?: string;
  stdout?: string;
  stderr?: string;
}

interface CIExecution {
  id: string;
  workflow: string;
  platform: string;
  python_version: string;
  total_tests: number;
  passed: number;
  failed: number;
  skipped: number;
  duration: number;
  timestamp: string;
}

interface CIStatistics {
  workflow?: string;
  total_runs: number;
  passed: number;
  failed: number;
  pass_rate: number;
  average_duration: number;
}

interface ComparisonResult {
  entity_id: string;
  entity_type: string;
  local_status: string | null;
  ci_status: string | null;
  platforms: string[];
  platform_specific: boolean;
}

interface FlakyTest {
  test_id: string;
  failure_rate: number;
  failure_count: number;
  lookback_runs: number;
}

class LensAPI {
  private client: AxiosInstance;
  private baseURL: string;

  constructor(baseURL: string = '/api') {
    this.baseURL = baseURL;
    this.client = axios.create({
      baseURL: baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  /**
   * Execute an action from Lens UI
   */
  async executeAction(request: ActionRequest): Promise<ActionResponse> {
    const response = await this.client.post('/actions', request);
    return response.data;
  }

  /**
   * Get status of a running action
   */
  async getActionStatus(actionId: string): Promise<ActionResponse> {
    const response = await this.client.get(`/actions/${actionId}`);
    return response.data;
  }

  /**
   * Cancel a running action
   */
  async cancelAction(actionId: string): Promise<{ action_id: string; status: string }> {
    const response = await this.client.delete(`/actions/${actionId}`);
    return response.data;
  }

  /**
   * Get CI execution results
   */
  async getCIExecutions(
    workflow?: string,
    limit: number = 10,
    status?: string
  ): Promise<{ executions: CIExecution[]; total: number }> {
    const params = new URLSearchParams();
    if (workflow) params.append('workflow', workflow);
    params.append('limit', limit.toString());
    if (status) params.append('status', status);

    const response = await this.client.get(`/ci/executions?${params}`);
    return response.data;
  }

  /**
   * Get CI health statistics
   */
  async getCIStatistics(workflow?: string): Promise<CIStatistics> {
    const params = new URLSearchParams();
    if (workflow) params.append('workflow', workflow);

    const response = await this.client.get(`/ci/statistics?${params}`);
    return response.data;
  }

  /**
   * Compare entity (test/file) results between CI and local
   */
  async compareEntity(
    entityId: string,
    entityType: string = 'test'
  ): Promise<ComparisonResult> {
    const params = new URLSearchParams();
    params.append('entity_type', entityType);

    const response = await this.client.get(`/comparison/entity/${entityId}?${params}`);
    return response.data;
  }

  /**
   * Get flaky tests detected from CI runs
   */
  async getFlakyTests(
    threshold: number = 3,
    lookbackRuns: number = 10
  ): Promise<{ flaky_tests: FlakyTest[]; total_flaky: number }> {
    const params = new URLSearchParams();
    params.append('threshold', threshold.toString());
    params.append('lookback_runs', lookbackRuns.toString());

    const response = await this.client.get(`/comparison/flaky?${params}`);
    return response.data;
  }

  /**
   * Get failures that only occur on specific platforms
   */
  async getPlatformSpecificFailures(): Promise<{
    failures: any[];
    total: number;
    windows_only: string[];
    linux_only: string[];
    macos_only: string[];
  }> {
    const response = await this.client.get('/comparison/platform-specific-failures');
    return response.data;
  }

  /**
   * Generate reproduction script for CI-specific failure
   */
  async generateReproductionScript(failureRequest: {
    test_id: string;
    platform?: string;
    python_version?: string;
  }): Promise<{
    test_id: string;
    platform: string;
    python_version: string;
    docker_command: string;
    reproduction_steps: string[];
  }> {
    const response = await this.client.post('/reproduction/ci-failure', failureRequest);
    return response.data;
  }

  /**
   * Connect to WebSocket for real-time updates
   */
  connectWebSocket(onMessage: (data: any) => void, onError?: (error: any) => void): WebSocket {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/ws`;

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      if (onError) onError(error);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
    };

    return ws;
  }

  /**
   * Check server health
   */
  async checkHealth(): Promise<{
    status: string;
    timestamp: string;
    version: string;
  }> {
    const response = await this.client.get('/health');
    return response.data;
  }
}

export default new LensAPI();
export type { ActionRequest, ActionResponse, CIExecution, CIStatistics, ComparisonResult, FlakyTest };
