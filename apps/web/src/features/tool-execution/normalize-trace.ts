import { type ToolTrace } from '@mcp-workspace/shared-types';

export function normalizeTrace(records: ToolTrace[]): ToolTrace[] {
  const invocations: ToolTrace[] = [];
  for (const record of records) {
    if (record.type === 'tool.started') {
      invocations.push({ ...record, status: 'running' });
    } else if (record.type === 'tool.completed') {
      const pending = [...invocations]
        .reverse()
        .find(
          (item) =>
            item.tool === record.tool && item.server === record.server && item.status === 'running',
        );
      const status = record.status === 'error' ? 'failed' : 'completed';
      const result = {
        ...record,
        status,
        error: status === 'failed' ? (record.code ?? 'Tool failed') : undefined,
      };
      if (pending) Object.assign(pending, result);
      else invocations.push(result);
    } else invocations.push(record);
  }
  return invocations;
}
