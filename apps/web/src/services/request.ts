import { ApiError } from './api-error';

let csrfToken = '';

export function setCsrfToken(token: string) {
  csrfToken = token;
}

export async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body) headers.set('Content-Type', 'application/json');
  if (init.method && init.method !== 'GET') headers.set('X-CSRF-Token', csrfToken);
  const response = await fetch(`/api${path}`, { ...init, headers, credentials: 'same-origin' });
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
