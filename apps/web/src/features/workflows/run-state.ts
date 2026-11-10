import { type Run } from '@mcp-workspace/shared-types';

export function isActiveRun(run: Run | undefined): boolean {
  return !!run && ['running', 'queued', 'needs_approval', 'awaiting_approval'].includes(run.status);
}
