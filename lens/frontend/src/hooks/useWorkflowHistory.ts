/**
 * useWorkflowHistory Hook
 * Manages CI workflow history state and requests
 */

import { useState, useCallback } from 'react';
import type { WorkflowsResponse } from '../api/types';
import { scoutClient, type WorkflowFilter } from '../api/tools';

interface UseWorkflowHistoryState {
  data: WorkflowsResponse | null;
  loading: boolean;
  error: Error | null;
}

export function useWorkflowHistory() {
  const [state, setState] = useState<UseWorkflowHistoryState>({
    data: null,
    loading: false,
    error: null,
  });

  const fetch = useCallback(async (filter?: WorkflowFilter) => {
    setState({ data: null, loading: true, error: null });
    try {
      const response = await scoutClient.getWorkflows(filter);
      setState({ data: response, loading: false, error: null });
      return response;
    } catch (error) {
      const err = error instanceof Error ? error : new Error('Unknown error');
      setState({ data: null, loading: false, error: err });
      throw err;
    }
  }, []);

  const refresh = useCallback(async (filter?: WorkflowFilter) => {
    return fetch(filter);
  }, [fetch]);

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null });
  }, []);

  return {
    ...state,
    fetch,
    refresh,
    reset,
  };
}
