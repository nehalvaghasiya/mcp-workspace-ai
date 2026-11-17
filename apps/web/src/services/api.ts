import {
  type Approval,
  type Artifact,
  type Connector,
  type Conversation,
  type ConversationSummary,
  type McpServer,
  type McpTool,
  type Run,
  type Session,
  type Settings,
  type ToolTrace,
  type WorkspaceFile,
} from '@mcp-workspace/shared-types';
import { normalizeTrace } from '../features/tool-execution/normalize-trace';
import { request, setCsrfToken } from './request';

export const body = (value: unknown) => JSON.stringify(value);

export const api = {
  session: async (signal?: AbortSignal) => {
    const session = await request<Session>('/session', { signal });
    setCsrfToken(session.csrf_token);
    return session;
  },
  demo: async () => {
    const session = await request<Session>('/auth/demo', { method: 'POST' });
    setCsrfToken(session.csrf_token);
    return session;
  },
  logout: () => request<void>('/auth/logout', { method: 'POST' }),
  connectors: (signal?: AbortSignal) => request<Connector[]>('/connectors', { signal }),
  toggleConnector: (id: string, enabled: boolean) =>
    request<Connector>(`/connectors/${encodeURIComponent(id)}`, {
      method: 'PATCH',
      body: body({ enabled }),
    }),
  disconnect: () => request<void>('/auth/google/disconnect', { method: 'POST' }),
  conversations: (signal?: AbortSignal) =>
    request<ConversationSummary[]>('/conversations', { signal }),
  createConversation: () =>
    request<Conversation>('/conversations', { method: 'POST', body: body({}) }),
  conversation: (id: string, signal?: AbortSignal) =>
    request<Conversation>(`/conversations/${encodeURIComponent(id)}`, { signal }),
  deleteConversation: (id: string) =>
    request<void>(`/conversations/${encodeURIComponent(id)}`, { method: 'DELETE' }),
  send: (id: string, content: string, requestId: string) =>
    request<Run>(`/conversations/${encodeURIComponent(id)}/messages`, {
      method: 'POST',
      body: body({ content, request_id: requestId }),
    }),
  trace: async (id: string, signal?: AbortSignal) =>
    normalizeTrace(await request<ToolTrace[]>(`/runs/${encodeURIComponent(id)}/trace`, { signal })),
  cancel: (id: string) =>
    request<void>(`/runs/${encodeURIComponent(id)}/cancel`, { method: 'POST' }),
  retry: (id: string, requestId: string) =>
    request<Run>(`/runs/${encodeURIComponent(id)}/retry`, {
      method: 'POST',
      body: body({ request_id: requestId }),
    }),
  approvals: (signal?: AbortSignal) => request<Approval[]>('/approvals', { signal }),
  decide: (id: string, decision: 'approve' | 'reject') =>
    request<{ status: string }>(`/approvals/${encodeURIComponent(id)}/decide`, {
      method: 'POST',
      body: body({ decision }),
    }),
  artifacts: (signal?: AbortSignal) => request<Artifact[]>('/artifacts', { signal }),
  workspaceFiles: (signal?: AbortSignal) =>
    request<WorkspaceFile[]>('/workspace-files', { signal }),
  deleteArtifact: (id: string) =>
    request<void>(`/artifacts/${encodeURIComponent(id)}`, { method: 'DELETE' }),
  servers: (signal?: AbortSignal) => request<McpServer[]>('/mcp/servers', { signal }),
  tools: (signal?: AbortSignal) => request<McpTool[]>('/mcp/tools', { signal }),
  settings: (signal?: AbortSignal) => request<Settings>('/settings', { signal }),
  updateSettings: (settings: { llm_consent: boolean; timezone: string }) =>
    request<{ status: string }>('/settings', { method: 'PATCH', body: body(settings) }),
  deleteAccount: () => request<void>('/account', { method: 'DELETE' }),
};
