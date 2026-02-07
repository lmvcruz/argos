/**
 * API utility functions with comprehensive logging.
 *
 * All API calls are logged with debug parameters (inputs/outputs)
 * and info level status updates.
 */

import logger from './logger';

export interface ApiError {
  status: number;
  message: string;
  detail?: string;
}

/**
 * Make an authenticated API request with logging.
 *
 * @param endpoint The API endpoint (relative path)
 * @param options Fetch options
 * @returns Parsed JSON response
 * @throws ApiError if request fails
 */
export async function apiRequest<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${endpoint}`;
  const method = options.method || 'GET';

  logger.debug(`[API_REQUEST] ${method} ${endpoint}`, { body: options.body });
  logger.info(`API call: ${method} ${endpoint}`);

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    const data = await response.json();

    if (!response.ok) {
      const error: ApiError = {
        status: response.status,
        message: data.detail || response.statusText,
        detail: data.detail,
      };
      logger.error(`[API_FAILED] ${method} ${endpoint}: ${error.status} ${error.message}`, {
        status: error.status,
        detail: error.detail,
      });
      throw error;
    }

    logger.debug(`[API_SUCCESS] ${method} ${endpoint} Response:`, { data });
    logger.info(`API success: ${method} ${endpoint} (${response.status})`);
    
    return data;
  } catch (error) {
    if (error instanceof TypeError) {
      logger.error(`[API_ERROR] ${method} ${endpoint}: Network error`, { error });
      throw {
        status: 0,
        message: 'Network error',
        detail: String(error),
      };
    }
    throw error;
  }
}

/**
 * GET request
 */
export async function apiGet<T = any>(endpoint: string, params?: Record<string, any>): Promise<T> {
  const query = params ? '?' + new URLSearchParams(params).toString() : '';
  logger.debug(`[API_GET] Parameters:`, params);
  return apiRequest<T>(`${endpoint}${query}`, { method: 'GET' });
}

/**
 * POST request
 */
export async function apiPost<T = any>(endpoint: string, data?: any): Promise<T> {
  logger.debug(`[API_POST] Request payload:`, data);
  return apiRequest<T>(endpoint, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * PUT request
 */
export async function apiPut<T = any>(endpoint: string, data?: any): Promise<T> {
  logger.debug(`[API_PUT] Request payload:`, data);
  return apiRequest<T>(endpoint, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

/**
 * DELETE request
 */
export async function apiDelete<T = any>(endpoint: string): Promise<T> {
  logger.debug(`[API_DELETE] Deleting ${endpoint}`);
