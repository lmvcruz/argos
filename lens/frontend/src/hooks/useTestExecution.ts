/**
 * useTestExecution Hook
 * Manages test execution state and requests
 */

import { useState, useCallback } from 'react';
import type { TestExecutionRequest, TestExecutionResponse } from '../api/types';
import { verdictClient } from '../api/tools';

interface UseTestExecutionState {
  data: TestExecutionResponse | null;
  loading: boolean;
  error: Error | null;
}

export function useTestExecution() {
  const [state, setState] = useState<UseTestExecutionState>({
    data: null,
    loading: false,
    error: null,
  });

  const execute = useCallback(async (request: TestExecutionRequest) => {
    setState({ data: null, loading: true, error: null });
    try {
      const response = await verdictClient.execute(request);
      setState({ data: response, loading: false, error: null });
      return response;
    } catch (error) {
      const err = error instanceof Error ? error : new Error('Unknown error');
      setState({ data: null, loading: false, error: err });
      throw err;
    }
  }, []);

  const cancel = useCallback(async () => {
    try {
      await verdictClient.cancel();
      setState({ data: null, loading: false, error: null });
    } catch (error) {
      const err = error instanceof Error ? error : new Error('Unknown error');
      setState((prev) => ({ ...prev, error: err }));
    }
  }, []);

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null });
  }, []);

  return {
    ...state,
    execute,
    cancel,
    reset,
  };
}
