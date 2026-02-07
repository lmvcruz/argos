/**
 * useApi - Centralized API call hook with error handling, loading states, and retry logic.
 *
 * Provides a consistent interface for making API calls across the application with:
 * - Automatic error handling and user-friendly error messages
 * - Loading state management
 * - Retry logic with exponential backoff
 * - Request/response logging
 * - Type-safe fetch with TypeScript generics
 *
 * Usage:
 *   const { data, loading, error, execute } = useApi<Project>();
 *   const handleFetch = async () => {
 *     const result = await execute('GET', '/api/projects');
 *     if (!error) { ... }
 *   };
 */

import { useState, useCallback } from 'react';

/**
 * API error response structure.
 */
export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
  status?: number;
}

/**
 * API response structure.
 */
export interface ApiResponse<T> {
  data: T | null;
  error: ApiError | null;
  loading: boolean;
}

/**
 * Hook options for customizing API behavior.
 */
export interface UseApiOptions {
  baseUrl?: string;
  timeout?: number;
  retryCount?: number;
  retryDelay?: number;
  onError?: (error: ApiError) => void;
  headers?: Record<string, string>;
}

/**
 * HTTP methods.
 */
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';

/**
 * Retry configuration.
 */
interface RetryConfig {
  count: number;
  delay: number;
  maxDelay: number;
}

/**
 * useApi hook - Centralized API call handler.
 *
 * Args:
 *   options: Configuration options for API calls (baseUrl, timeout, retries, headers)
 *
 * Returns:
 *   Object with { data, loading, error, execute, reset } methods
 *
 * Examples:
 *   const { execute, data, error } = useApi<Project>();
 *   const projects = await execute('GET', '/api/projects');
 */
export function useApi<T = unknown>(options: UseApiOptions = {}) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  const {
    baseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000',
    timeout = 30000,
    retryCount = 3,
    retryDelay = 1000,
    onError,
    headers = {},
  } = options;

  /**
   * Parse error response to create consistent ApiError object.
   */
  const parseErrorResponse = useCallback(
    async (response: Response): Promise<ApiError> => {
      let errorData: Record<string, unknown> = {};

      try {
        errorData = await response.json();
      } catch {
        // JSON parsing failed, use generic message
      }

      const status = response.status;
      let message = errorData.detail || errorData.message || response.statusText;

      // Convert to string if needed
      if (typeof message !== 'string') {
        message = String(message);
      }

      // Map HTTP status codes to user-friendly messages
      if (!message || message === 'Unknown') {
        switch (status) {
          case 400:
            message = 'Bad request. Please check your input.';
            break;
          case 401:
            message = 'Unauthorized. Please log in.';
            break;
          case 403:
            message = 'Forbidden. You do not have permission.';
            break;
          case 404:
            message = 'Resource not found.';
            break;
          case 409:
            message = 'Conflict. A project with this name already exists.';
            break;
          case 500:
            message = 'Server error. Please try again later.';
            break;
          case 503:
            message = 'Service unavailable. Please try again later.';
            break;
          default:
            message = `Error: ${status} ${response.statusText}`;
        }
      }

      const code = errorData.code || `HTTP_${status}`;

      return {
        code: String(code),
        message,
        status,
        details: errorData,
      };
    },
    []
  );

  /**
   * Sleep for specified milliseconds (used for retry delays).
   */
  const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

  /**
   * Calculate exponential backoff delay.
   */
  const getRetryDelay = (attemptNumber: number, baseDelay: number): number => {
    return Math.min(baseDelay * Math.pow(2, attemptNumber - 1), 10000);
  };

  /**
   * Execute API request with retry logic.
   *
   * Args:
   *   method: HTTP method (GET, POST, PUT, DELETE)
   *   endpoint: API endpoint path (e.g., '/api/projects')
   *   body: Request body (for POST/PUT/DELETE requests)
   *   customHeaders: Override default headers for this request
   *
   * Returns:
   *   Response data of type T, or null if error
   */
  const execute = useCallback(
    async (
      method: HttpMethod,
      endpoint: string,
      body?: unknown,
      customHeaders?: Record<string, string>
    ): Promise<T | null> => {
      setLoading(true);
      setError(null);
      setData(null);

      const url = new URL(endpoint, baseUrl).toString();
      const mergedHeaders: Record<string, string> = {
        'Content-Type': 'application/json',
        ...headers,
        ...customHeaders,
      };

      const config: RequestInit = {
        method,
        headers: mergedHeaders,
        signal: AbortSignal.timeout(timeout),
      };

      if (body && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
        config.body = JSON.stringify(body);
      }

      let lastError: ApiError | null = null;
      let attempt = 0;

      // Retry loop with exponential backoff
      while (attempt < retryCount) {
        try {
          attempt += 1;
          const response = await fetch(url, config);

          if (!response.ok) {
            const apiError = await parseErrorResponse(response);
            lastError = apiError;

            // Don't retry on client errors (4xx) except 429 (Too Many Requests)
            if (response.status >= 400 && response.status < 500 && response.status !== 429) {
              setError(apiError);
              onError?.(apiError);
              setLoading(false);
              return null;
            }

            // Retry on server errors (5xx) or rate limit (429)
            if (attempt < retryCount) {
              const delay = getRetryDelay(attempt, retryDelay);
              await sleep(delay);
              continue;
            } else {
              setError(apiError);
              onError?.(apiError);
              setLoading(false);
              return null;
            }
          }

          // Successfully got a response
          let responseData: T;

          if (response.status === 204) {
            // No content response
            responseData = null as unknown as T;
          } else {
            responseData = await response.json();
          }

          setData(responseData);
          setLoading(false);
          return responseData;
        } catch (err) {
          // Network error or timeout
          const errorMessage =
            err instanceof TypeError
              ? 'Network error. Please check your connection.'
              : err instanceof DOMException && err.name === 'AbortError'
                ? 'Request timeout. Please try again.'
                : 'An unexpected error occurred.';

          lastError = {
            code: err instanceof Error ? err.name : 'UNKNOWN_ERROR',
            message: errorMessage,
            details: { originalError: String(err) },
          };

          // Retry on network errors
          if (attempt < retryCount) {
            const delay = getRetryDelay(attempt, retryDelay);
            await sleep(delay);
            continue;
          } else {
            setError(lastError);
            onError?.(lastError);
            setLoading(false);
            return null;
          }
        }
      }

      // All retries exhausted
      if (lastError) {
        setError(lastError);
        onError?.(lastError);
      }
      setLoading(false);
      return null;
    },
    [baseUrl, timeout, retryCount, retryDelay, headers, parseErrorResponse, onError]
  );

  /**
   * Reset the hook state (clear data, error, and loading).
   */
  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setLoading(false);
  }, []);

  return {
    data,
    loading,
    error,
    execute,
    reset,
  };
}

/**
 * Helper hook for making GET requests.
 *
 * Args:
 *   endpoint: API endpoint path
 *   dependencies: Dependency array for automatic fetching
 *   options: API configuration options
 *
 * Returns:
 *   Object with { data, loading, error, refetch } methods
 *
 * Examples:
 *   const { data: projects, loading, error, refetch } = useGet<Project[]>('/api/projects', []);
 */
export function useGet<T = unknown>(
  endpoint: string,
  dependencies: unknown[] = [],
  options: UseApiOptions = {}
) {
  const { execute, data, loading, error, reset } = useApi<T>(options);
  const [refetch, setRefetch] = useState(0);

  const doFetch = useCallback(async () => {
    await execute('GET', endpoint);
  }, [endpoint, execute]);

  // Auto-fetch on mount and dependency change
  React.useEffect(() => {
    doFetch();
  }, [...dependencies, refetch, doFetch]);

  return {
    data,
    loading,
    error,
    refetch: () => setRefetch((prev) => prev + 1),
  };
}

/**
 * Helper hook for making POST requests.
 *
 * Args:
 *   endpoint: API endpoint path
 *   options: API configuration options
 *
 * Returns:
 *   Object with { mutate, data, loading, error, reset } methods
 *
 * Examples:
 *   const { mutate, loading, error } = usePost<Project>('/api/projects');
 *   await mutate({ name: 'My Project', ... });
 */
export function usePost<T = unknown>(endpoint: string, options: UseApiOptions = {}) {
  const { execute, data, loading, error, reset } = useApi<T>(options);

  const mutate = useCallback(
    async (body?: unknown, customHeaders?: Record<string, string>) => {
      return execute('POST', endpoint, body, customHeaders);
    },
    [endpoint, execute]
  );

  return {
    mutate,
    data,
    loading,
    error,
    reset,
  };
}

export default useApi;
