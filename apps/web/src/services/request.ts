import { ApiError } from './api-error';

let csrfToken = '';
export const REQUEST_TIMEOUT_MS = 20_000;

export function setCsrfToken(token: string) {
  csrfToken = token;
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const detail: unknown = await response.json().catch(() => null);
    let message = `Request failed (${response.status}). Please try again.`;
    let code: string | undefined;
    if (detail && typeof detail === 'object') {
      const obj = detail as Record<string, unknown>;
      if (typeof obj.detail === 'string') message = obj.detail;
      if (typeof obj.message === 'string') message = obj.message;
      if (obj.error && typeof obj.error === 'object') {
        const error = obj.error as Record<string, unknown>;
        if (typeof error.message === 'string') message = error.message;
        if (typeof error.code === 'string') code = error.code;
      }
    }
    throw new ApiError(message, response.status, code);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body) headers.set('Content-Type', 'application/json');
  if (init.method && init.method !== 'GET') headers.set('X-CSRF-Token', csrfToken);
  const controller = new AbortController();
  let timedOut = false;
  const cancelled = () => controller.abort(init.signal?.reason);
  if (init.signal?.aborted) cancelled();
  else init.signal?.addEventListener('abort', cancelled, { once: true });
  const timeout = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, REQUEST_TIMEOUT_MS);
  try {
    const response = await fetch(`/api${path}`, {
      ...init,
      headers,
      credentials: 'same-origin',
      signal: controller.signal,
    });
    return await parseResponse<T>(response);
  } catch (error) {
    if (timedOut)
      throw new ApiError(
        'The server took too long to respond. Check the connection and try again.',
        0,
        'REQUEST_TIMEOUT',
      );
    if (init.signal?.aborted || error instanceof ApiError) throw error;
    if (error instanceof SyntaxError)
      throw new ApiError(
        'The server returned an invalid response. Please try again.',
        0,
        'INVALID_RESPONSE',
      );
    throw new ApiError(
      'Unable to reach the server. Check the connection and try again.',
      0,
      'NETWORK_ERROR',
    );
  } finally {
    clearTimeout(timeout);
    init.signal?.removeEventListener('abort', cancelled);
  }
}
