import { type StreamEvent } from '@mcp-workspace/shared-types';

export function subscribeRun(
  runId: string,
  onEvent: (event: StreamEvent) => void,
  onConnection: (connected: boolean) => void,
): () => void {
  const source = new EventSource(`/api/runs/${encodeURIComponent(runId)}/events`, {
    withCredentials: true,
  });
  const seen = new Set<string>();
  const receive = (event: MessageEvent<string>) => {
    try {
      const value: unknown = JSON.parse(event.data);
      if (!value || typeof value !== 'object' || !('type' in value) || !('data' in value)) return;
      const parsed = value as StreamEvent;
      if (parsed.run_id !== runId) return;
      const key = String(parsed.id ?? event.lastEventId);
      if (seen.has(key)) return;
      seen.add(key);
      onEvent(parsed);
      if (['run.completed', 'run.failed', 'run.cancelled'].includes(parsed.type)) source.close();
    } catch {
      onConnection(false);
    }
  };
  source.onmessage = receive;
  for (const type of [
    'run.started',
    'tool.started',
    'tool.completed',
    'approval.required',
    'message.delta',
    'run.completed',
    'run.failed',
    'run.cancelled',
  ])
    source.addEventListener(type, receive as EventListener);
  source.onopen = () => onConnection(true);
  source.onerror = () => onConnection(false);
  return () => source.close();
}
