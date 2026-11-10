import { FakeSource } from '../support/fake-event-source';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApiError } from '../../src/services/api-error';
import { request } from '../../src/services/request';
import { normalizeTrace } from '../../src/features/tool-execution/normalize-trace';
import { safeDownloadUrl } from '../../src/lib/urls';
import { safeSourceUrl } from '../../src/lib/urls';
import { setCsrfToken } from '../../src/services/request';
import { subscribeRun } from '../../src/services/run-events';

afterEach(() => vi.unstubAllGlobals());
describe('authenticated request boundary', () => {
  it('sends CSRF on mutation and uses same-origin cookies without browser token storage', async () => {
    const fetcher = vi.fn().mockResolvedValue(new Response(JSON.stringify({ ok: true })));
    vi.stubGlobal('fetch', fetcher);
    setCsrfToken('test-csrf');
    await request('/approvals/a/decide', { method: 'POST', body: '{"decision":"approve"}' });
    const [url, init] = fetcher.mock.calls[0] as [string, RequestInit];
    expect(url).toBe('/api/approvals/a/decide');
    expect(new Headers(init.headers).get('X-CSRF-Token')).toBe('test-csrf');
    expect(init.credentials).toBe('same-origin');
    expect(localStorage.length).toBe(0);
  });
  it('exposes actionable backend errors and does not retry a mutation', async () => {
    const fetcher = vi
      .fn()
      .mockResolvedValue(
        new Response(JSON.stringify({ detail: 'Approval already consumed' }), { status: 409 }),
      );
    vi.stubGlobal('fetch', fetcher);
    await expect(request('/approvals/a/decide', { method: 'POST' })).rejects.toEqual(
      new ApiError('Approval already consumed', 409),
    );
    expect(fetcher).toHaveBeenCalledTimes(1);
  });
});
describe('untrusted URLs', () => {
  it('rejects executable source links and untrusted artifact downloads', () => {
    expect(safeSourceUrl('javascript:alert(1)')).toBeUndefined();
    expect(safeSourceUrl('data:text/html,hello')).toBeUndefined();
    expect(safeSourceUrl('https://drive.google.com/file/d/abc')).toBe(
      'https://drive.google.com/file/d/abc',
    );
    expect(safeDownloadUrl('https://outside.invalid/file')).toBeUndefined();
    expect(safeDownloadUrl('/api/artifacts/../../account/download')).toBeUndefined();
    expect(safeDownloadUrl('//outside.invalid/file')).toBeUndefined();
    expect(safeDownloadUrl('/api/artifacts/owned-id/download')).toBe(
      '/api/artifacts/owned-id/download',
    );
  });
});
describe('run events', () => {
  it('joins persisted start/completion records without presenting a failed tool as success', () => {
    const traces = normalizeTrace([
      {
        id: 'start',
        type: 'tool.started',
        tool: 'gmail.search_messages',
        server: 'gmail',
        arguments: { query: 'launch' },
      },
      {
        id: 'end',
        type: 'tool.completed',
        tool: 'gmail.search_messages',
        server: 'gmail',
        status: 'error',
        code: 'CONNECTOR_NOT_AUTHORIZED',
        elapsed_ms: 31,
      },
    ]);
    expect(traces).toHaveLength(1);
    expect(traces[0]?.status).toBe('failed');
    expect(traces[0]?.arguments).toEqual({ query: 'launch' });
    expect(traces[0]?.error).toBe('CONNECTOR_NOT_AUTHORIZED');
  });
  it('deduplicates replayed IDs, rejects other runs, and closes on terminal events', () => {
    vi.stubGlobal('EventSource', FakeSource);
    const received = vi.fn();
    const connection = vi.fn();
    const close = subscribeRun('run-1', received, connection);
    FakeSource.instance.onopen?.();
    const event = { id: 1, run_id: 'run-1', type: 'message.delta', data: { text: 'hello' } };
    FakeSource.instance.receive(event);
    FakeSource.instance.receive(event);
    FakeSource.instance.receive({ ...event, id: 2, run_id: 'run-other' });
    expect(received).toHaveBeenCalledTimes(1);
    expect(connection).toHaveBeenCalledWith(true);
    FakeSource.instance.receive({ id: 3, run_id: 'run-1', type: 'run.cancelled', data: {} });
    expect(FakeSource.instance.close).toHaveBeenCalledOnce();
    close();
    expect(FakeSource.instance.close).toHaveBeenCalledTimes(2);
  });
});
