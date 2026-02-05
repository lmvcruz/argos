/**
 * useAnvilAnalysis Hook
 * Manages code analysis state and requests
 */

import { useState, useCallback } from 'react';
import type { AnvilAnalysisRequest, AnvilAnalysisResponse } from '../api/types';
import { anvilClient } from '../api/tools';

interface UseAnvilAnalysisState {
  data: AnvilAnalysisResponse | null;
  loading: boolean;
  error: Error | null;
}

export function useAnvilAnalysis() {
  const [state, setState] = useState<UseAnvilAnalysisState>({
    data: null,
    loading: false,
    error: null,
  });

  const analyze = useCallback(async (request: AnvilAnalysisRequest) => {
    setState({ data: null, loading: true, error: null });
    try {
      const response = await anvilClient.analyze(request);
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
      await anvilClient.cancel();
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
    analyze,
    cancel,
    reset,
  };
}
