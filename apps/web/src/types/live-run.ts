import { type StreamEvent } from '@mcp-workspace/shared-types';

export interface LiveRun {
  id: string;
  text: string;
  events: StreamEvent[];
  finished: boolean;
  error?: string;
  connected: boolean;
}
