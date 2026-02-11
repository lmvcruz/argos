/**
 * API types and interfaces for Phase 2 integration
 * Defines contracts for tool backends (Anvil, Verdict, Scout)
 */

// ============================================================================
// ANVIL - Code Analysis
// ============================================================================

export interface AnvilIssue {
  id: string;
  file: string;
  line: number;
  column: number;
  severity: 'error' | 'warning' | 'info';
  rule: string;
  message: string;
  code?: string;
}

export interface AnvilAnalysisRequest {
  projectPath: string;
  toolOptions?: {
    ignorePatterns?: string[];
    checkTypes?: string[];
  };
}

export interface AnvilAnalysisResponse {
  issues: AnvilIssue[];
  summary: {
    total: number;
    errors: number;
    warnings: number;
    info: number;
  };
  duration: number;
  timestamp: string;
}

// ============================================================================
// VERDICT - Test Execution
// ============================================================================

export interface TestResult {
  id: string;
  name: string;
  status: 'passed' | 'failed' | 'flaky' | 'skipped';
  file: string;
  duration: number;
  error?: string;
  stackTrace?: string;
}

export interface TestExecutionRequest {
  projectPath: string;
  testPattern?: string;
  framework?: 'jest' | 'pytest' | 'mocha' | 'go test';
}

export interface TestExecutionResponse {
  tests: TestResult[];
  summary: {
    total: number;
    passed: number;
    failed: number;
    flaky: number;
    skipped: number;
    duration: number;
    coverage?: number;
  };
  timestamp: string;
}

// ============================================================================
// SCOUT - CI Workflows
// ============================================================================

export interface WorkflowJob {
  id: string;
  name: string;
  status: string;
  duration: number;
  logs?: string;
}

export interface Workflow {
  id: string;
  name: string;
  run_number: number;
  branch: string;
  status: 'completed' | 'in_progress' | 'queued';
  result: 'passed' | 'failed' | 'pending';
  duration: number;
  started_at: string;
  completed_at?: string;
  url: string;
  jobs: WorkflowJob[];
  // Additional Scout data
  platform?: string;
  python_version?: string;
  commit_sha?: string;
  total_jobs?: number;
  // Data availability flags
  has_logs?: boolean;
  has_parsed_data?: boolean;
  logs_downloaded_at?: string;
  data_parsed_at?: string;
}

export interface WorkflowsResponse {
  workflows: Workflow[];
  sync_status: {
    last_sync: string;
    is_syncing: boolean;
    next_sync: string;
  };
  total: number;
  timestamp: string;
}

// ============================================================================
// GAZE - Performance Monitoring (Phase 3)
// ============================================================================

export interface PerformanceMetric {
  name: string;
  value: number;
  unit: string;
  threshold?: number;
}

export interface PerformanceProfile {
  metrics: PerformanceMetric[];
  duration: number;
}

// ============================================================================
// FORGE - Build Management (Phase 3)
// ============================================================================

export interface BuildConfig {
  name: string;
  target: string;
  environment: string;
}

export interface BuildResult {
  id: string;
  status: 'success' | 'failed' | 'in_progress';
  duration: number;
  artifacts: string[];
  logs: string;
}

// ============================================================================
// Common Response Types
// ============================================================================

export interface ErrorResponse {
  error: string;
  message: string;
  code: string;
  timestamp: string;
}

export interface StatusResponse {
  status: 'healthy' | 'unhealthy';
  timestamp: string;
  version?: string;
}
