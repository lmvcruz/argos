import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';

/**
 * Scout CI Inspection Context
 *
 * Manages global state for Scout CI data:
 * - Workflow lists and filtering
 * - Selected workflows and jobs
 * - Analysis results
 * - Health metrics
 * - Sync status
 */

// Types for Scout data
export interface WorkflowRun {
  run_id: number;
  run_number: number;
  workflow_name: string;
  status: string;
  conclusion: string;
  started_at: string;
  completed_at?: string;
  duration_seconds?: number;
  branch: string;
  commit_sha: string;
  url?: string;
}

export interface WorkflowJob {
  job_id: string;
  job_name: string;
  status: string;
  conclusion: string;
  runner_os?: string;
  python_version?: string;
  duration_seconds?: number;
  started_at?: string;
  completed_at?: string;
  test_count?: number;
  passed_count?: number;
  failed_count?: number;
}

export interface TestResult {
  test_nodeid: string;
  outcome: 'passed' | 'failed' | 'skipped' | 'error';
  duration?: number;
  error_message?: string;
  error_traceback?: string;
  timestamp?: string;
}

export interface AnalysisData {
  total_runs: number;
  successful_runs: number;
  failed_runs: number;
  success_rate: number;
  window_days: number;
  patterns: Record<string, any[]>;
}

export interface FlakyTest {
  test_nodeid: string;
  pass_rate: number;
  fail_rate: number;
  total_runs: number;
  last_failed?: string;
  trend: 'stable' | 'improving' | 'degrading';
}

export interface SyncStatus {
  last_sync?: string;
  total_workflows: number;
  total_jobs: number;
  total_test_results: number;
  is_syncing: boolean;
  sync_progress?: number;
}

// Context state
export interface ScoutState {
  // Workflows
  workflows: WorkflowRun[];
  selectedWorkflow: WorkflowRun | null;
  workflowsLoading: boolean;
  workflowsError: string | null;

  // Jobs
  jobs: WorkflowJob[];
  selectedJob: WorkflowJob | null;
  jobsLoading: boolean;

  // Tests
  tests: TestResult[];
  testsLoading: boolean;

  // Analysis
  analysis: AnalysisData | null;
  analysisLoading: boolean;
  analysisError: string | null;

  // Health
  flakyTests: FlakyTest[];
  flakyTestsLoading: boolean;

  // Sync
  syncStatus: SyncStatus | null;
  syncStatusLoading: boolean;

  // Filters
  filters: {
    workflowLimit: number;
    workflowStatus?: string;
    workflowName?: string;
    branch?: string;
    analysisWindow: number;
  };
}

// Actions
export interface ScoutActions {
  fetchWorkflows: (params?: any) => Promise<void>;
  selectWorkflow: (workflow: WorkflowRun) => Promise<void>;
  fetchAnalysis: (params?: any) => Promise<void>;
  fetchFlakyTests: (threshold?: number) => Promise<void>;
  fetchSyncStatus: () => Promise<void>;
  setFilters: (filters: Partial<ScoutState['filters']>) => void;
  clearSelection: () => void;
}

export type ScoutContextType = ScoutState & ScoutActions;

const ScoutContext = createContext<ScoutContextType | undefined>(undefined);

// Provider component
export const ScoutProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, setState] = useState<ScoutState>({
    workflows: [],
    selectedWorkflow: null,
    workflowsLoading: false,
    workflowsError: null,
    jobs: [],
    selectedJob: null,
    jobsLoading: false,
    tests: [],
    testsLoading: false,
    analysis: null,
    analysisLoading: false,
    analysisError: null,
    flakyTests: [],
    flakyTestsLoading: false,
    syncStatus: null,
    syncStatusLoading: false,
    filters: {
      workflowLimit: 20,
      analysisWindow: 30,
    },
  });

  const fetchWorkflows = useCallback(async (params?: any) => {
    setState((prev) => ({ ...prev, workflowsLoading: true, workflowsError: null }));

    try {
      const queryParams = new URLSearchParams({
        limit: String(state.filters.workflowLimit),
        ...(state.filters.workflowStatus && { status: state.filters.workflowStatus }),
        ...(state.filters.workflowName && { workflow_name: state.filters.workflowName }),
        ...(state.filters.branch && { branch: state.filters.branch }),
      });

      const response = await fetch(`/api/scout/workflows?${queryParams}`);
      if (!response.ok) throw new Error('Failed to fetch workflows');

      const data = await response.json();
      setState((prev) => ({
        ...prev,
        workflows: data.workflows,
        workflowsLoading: false,
      }));
    } catch (error) {
      setState((prev) => ({
        ...prev,
        workflowsLoading: false,
        workflowsError: error instanceof Error ? error.message : 'Unknown error',
      }));
    }
  }, [state.filters]);

  const selectWorkflow = useCallback(async (workflow: WorkflowRun) => {
    setState((prev) => ({ ...prev, selectedWorkflow: workflow, jobsLoading: true, jobs: [] }));

    try {
      const response = await fetch(`/api/scout/workflows/${workflow.run_id}`);
      if (!response.ok) throw new Error('Failed to fetch workflow details');

      const data = await response.json();
      setState((prev) => ({
        ...prev,
        jobs: data.jobs || [],
        jobsLoading: false,
      }));
    } catch (error) {
      setState((prev) => ({
        ...prev,
        jobsLoading: false,
      }));
    }
  }, []);

  const fetchAnalysis = useCallback(async (params?: any) => {
    setState((prev) => ({ ...prev, analysisLoading: true, analysisError: null }));

    try {
      const queryParams = new URLSearchParams({
        window_days: String(state.filters.analysisWindow),
        ...params,
      });

      const response = await fetch(`/api/scout/analyze?${queryParams}`, { method: 'POST' });
      if (!response.ok) throw new Error('Failed to fetch analysis');

      const data = await response.json();
      setState((prev) => ({
        ...prev,
        analysis: data,
        analysisLoading: false,
      }));
    } catch (error) {
      setState((prev) => ({
        ...prev,
        analysisLoading: false,
        analysisError: error instanceof Error ? error.message : 'Unknown error',
      }));
    }
  }, [state.filters]);

  const fetchFlakyTests = useCallback(async (threshold = 0.5) => {
    setState((prev) => ({ ...prev, flakyTestsLoading: true }));

    try {
      const response = await fetch(
        `/api/scout/health/flaky-tests?threshold=${threshold}&min_runs=5`
      );
      if (!response.ok) throw new Error('Failed to fetch flaky tests');

      const data = await response.json();
      setState((prev) => ({
        ...prev,
        flakyTests: data.flaky_tests || [],
        flakyTestsLoading: false,
      }));
    } catch (error) {
      setState((prev) => ({
        ...prev,
        flakyTestsLoading: false,
      }));
    }
  }, []);

  const fetchSyncStatus = useCallback(async () => {
    setState((prev) => ({ ...prev, syncStatusLoading: true }));

    try {
      const response = await fetch('/api/scout/sync-status');
      if (!response.ok) throw new Error('Failed to fetch sync status');

      const data = await response.json();
      setState((prev) => ({
        ...prev,
        syncStatus: data,
        syncStatusLoading: false,
      }));
    } catch (error) {
      setState((prev) => ({
        ...prev,
        syncStatusLoading: false,
      }));
    }
  }, []);

  const setFilters = useCallback((newFilters: Partial<ScoutState['filters']>) => {
    setState((prev) => ({
      ...prev,
      filters: { ...prev.filters, ...newFilters },
    }));
  }, []);

  const clearSelection = useCallback(() => {
    setState((prev) => ({
      ...prev,
      selectedWorkflow: null,
      selectedJob: null,
      jobs: [],
      tests: [],
    }));
  }, []);

  const value: ScoutContextType = {
    ...state,
    fetchWorkflows,
    selectWorkflow,
    fetchAnalysis,
    fetchFlakyTests,
    fetchSyncStatus,
    setFilters,
    clearSelection,
  };

  return <ScoutContext.Provider value={value}>{children}</ScoutContext.Provider>;
};

// Hook to use Scout context
export const useScout = (): ScoutContextType => {
  const context = useContext(ScoutContext);
  if (!context) {
    throw new Error('useScout must be used within a ScoutProvider');
  }
  return context;
};
