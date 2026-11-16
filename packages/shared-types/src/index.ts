export type Json = null | boolean | number | string | Json[] | { [key: string]: Json };
import type { components } from './generated-api';

// REST shapes come directly from the backend-exported OpenAPI schema.
export type User = components['schemas']['UserView'];
export type Session = components['schemas']['SessionView'];
export type SourceRef = components['schemas']['SourceRef'];
export type Artifact = components['schemas']['ArtifactView'];
export type WorkspaceFile = components['schemas']['WorkspaceFileView'];
export type Message = components['schemas']['MessageView'];
export type Run = components['schemas']['RunView'];
export type RunStatus = Run['status'];
export type ConversationSummary = components['schemas']['ConversationSummary'];
export type Conversation = components['schemas']['ConversationView'];
export type Connector = components['schemas']['ConnectorView'];
export type McpServer = components['schemas']['ServerView'];
export type McpTool = components['schemas']['ToolView'];
export type Settings = components['schemas']['SettingsView'];
// Pydantic exports JsonValue as an unconstrained schema. Keep the browser JSON
// boundary explicit, and accept legacy string summaries used by UI fixtures.
export type Approval = Omit<components['schemas']['ApprovalView'], 'arguments' | 'summary'> & {
  arguments: Record<string, Json>;
  summary: string | Record<string, Json>;
};
export interface ToolTrace {
  id?: string;
  type?: 'tool.started' | 'tool.completed';
  tool: string;
  server: string;
  arguments?: Json;
  data?: Json;
  status?: string;
  elapsed_ms?: number;
  sources?: SourceRef[];
  error?: string;
  code?: string;
}
interface EventBase {
  id: string | number;
  run_id: string;
}
export type StreamEvent = EventBase &
  (
    | { type: 'run.started'; data: Record<string, Json> }
    | {
        type: 'model.started' | 'model.completed' | 'model.failed' | 'model.usage';
        data: Record<string, Json>;
      }
    | { type: 'tool.started'; data: { tool: string; server: string; arguments: Json } }
    | {
        type: 'tool.completed';
        data: {
          tool: string;
          server: string;
          data: Json;
          elapsed_ms: number;
          sources?: SourceRef[];
          status?: string;
          code?: string;
        };
      }
    | { type: 'approval.required'; data: Approval }
    | { type: 'message.delta'; data: { text: string } }
    | {
        type: 'run.completed';
        data: {
          content: string;
          sources: SourceRef[];
          artifacts: Artifact[];
          workspace_files?: WorkspaceFile[];
        };
      }
    | { type: 'run.failed'; data: { message: string; code: string } }
    | { type: 'run.cancelled'; data: Record<string, Json> }
  );
