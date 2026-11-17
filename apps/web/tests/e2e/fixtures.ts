/** Synthetic browser API fixtures exercise UI states; real MCP flows live in workspace.spec.ts. */
import type { Page } from '@playwright/test';
import type { Approval } from '@mcp-workspace/shared-types';
import type { Artifact } from '@mcp-workspace/shared-types';
import type { Connector } from '@mcp-workspace/shared-types';
import type { Conversation } from '@mcp-workspace/shared-types';
import type { Session } from '@mcp-workspace/shared-types';
import type { SourceRef } from '@mcp-workspace/shared-types';

export const sources: SourceRef[] = [
  {
    provider: 'gmail',
    resource_id: 'mock-mail-001',
    title: 'Northstar launch review',
    url: null,
    retrieved_at: '2026-11-05T12:00:00Z',
    pointer: '',
    snippet: 'Alex confirmed that the accessibility review is the last launch dependency.',
  },
  {
    provider: 'calendar',
    resource_id: 'mock-event-001',
    title: 'Launch readiness review',
    url: null,
    retrieved_at: '2026-11-05T12:00:00Z',
    pointer: '',
    snippet: 'Thursday 2:00 PM America/Chicago. Conflicts with the design review.',
  },
  {
    provider: 'drive',
    resource_id: 'mock-drive-001',
    title: 'Launch readiness checklist',
    url: null,
    retrieved_at: '2026-11-05T12:00:00Z',
    pointer: '',
    snippet: 'Accessibility review remains open. Owner: Morgan.',
  },
];
export const files: Artifact[] = ['pdf', 'docx', 'xlsx', 'pptx'].map((format, index) => ({
  id: `artifact-${index}`,
  title: `Northstar launch brief.${format}`,
  format,
  mime_type:
    format === 'pdf'
      ? 'application/pdf'
      : `application/vnd.openxmlformats-officedocument.${format}`,
  size: 12000 + index * 1000,
  sha256: 'e92b36a094e4247b7f82d6caaafe522f61203e58094af735ae51e1fe5bf2ccf8',
  created_at: '2026-11-05T12:00:00Z',
  validated: true,
  download_url: `/api/artifacts/artifact-${index}/download`,
  sources,
}));
export const proposal: Approval = {
  id: 'approval-001',
  run_id: 'run-001',
  tool: 'gmail.send_draft',
  summary: 'Send the launch review follow-up to Alex',
  arguments: {
    from: 'taylor@example.invalid',
    to: ['alex@example.invalid'],
    cc: [],
    bcc: [],
    subject: 'Northstar launch review',
    body_text:
      'Hi Alex,\n\nThe accessibility review is our remaining launch dependency. Let’s discuss it Thursday at 3:00 PM America/Chicago.\n\nThanks,\nTaylor',
    attachments: [],
    draft_id: 'mock-draft-001',
    side_effects: 'Sends one email to the listed recipient. Synthetic demo outbox only.',
  },
  status: 'pending',
  expires_at: '2099-11-05T23:00:00Z',
  action_digest: '42d485eadd7586e07a1a7248822b545f5df322c57a83d9a42a78f47a9286b822',
};
export const session: Session = {
  user: {
    id: 'demo-user',
    display_name: 'Taylor Morgan',
    email: 'taylor@example.invalid',
    timezone: 'America/Chicago',
  },
  csrf_token: 'synthetic-csrf-fixture',
  mode: 'mock',
  llm: { provider: 'fake', model: 'deterministic-demo', consented: false },
};
export const conversation: Conversation = {
  id: 'conversation-001',
  title: 'A clearer view of the Northstar launch',
  runs: [
    {
      id: 'run-001',
      conversation_id: 'conversation-001',
      status: 'completed',
      error: null,
      read_count: 0,
      retryable: false,
    },
  ],
  messages: [
    {
      id: 'message-001',
      role: 'user',
      content:
        'Review the Northstar launch messages, meetings, and checklist. Create a decision brief with sources.',
      sources: [],
      artifacts: [],
    },
    {
      id: 'message-002',
      role: 'assistant',
      content:
        '## The launch is close. One decision remains.\n\nThe **accessibility review** is the remaining launch dependency. Morgan owns the review, and Alex is waiting for the final sign-off.\n\nThere is a scheduling conflict: the launch readiness review overlaps the design review on Thursday at **2:00 PM America/Chicago**. Check the suggested alternatives before moving either meeting.\n\n### Recommended next steps\n\n1. Complete the accessibility review with Morgan.\n2. Resolve Thursday’s scheduling conflict.\n3. Confirm launch readiness with Alex.\n\nI prepared four files from the retrieved synthetic source records.',
      sources,
      artifacts: files,
    },
  ],
};

export async function fixtureApi(
  page: Page,
  options: {
    signedIn?: boolean;
    mode?: string;
    partial?: boolean;
    recoverable?: boolean;
    approvals?: Approval[];
    delay?: number;
  } = {},
) {
  let signedIn = options.signedIn ?? true;
  let approvals = options.approvals ?? [];
  let resumed = false;
  const connectors: Connector[] = ['gmail', 'calendar', 'drive'].map((id) => ({
    id,
    name: id === 'gmail' ? 'Gmail' : id === 'calendar' ? 'Calendar' : 'Drive',
    mode: 'mock',
    status: 'mock',
    scopes: [`mock:${id}:read`, `mock:${id}:write`],
    enabled: true,
  }));
  const mutations: {
    path: string;
    method: string;
    body: string | null;
    csrf: string | undefined;
  }[] = [];
  await page.context().route('**/api/**', async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    const method = request.method();
    if (method !== 'GET')
      mutations.push({
        path,
        method,
        body: request.postData(),
        csrf: request.headers()['x-csrf-token'],
      });
    const reply = (value: unknown, status = 200) =>
      route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(value) });
    if (path === '/api/session') {
      if (options.delay) await new Promise((resolve) => setTimeout(resolve, options.delay));
      return reply({
        ...session,
        user: signedIn ? session.user : null,
        mode: options.mode ?? 'mock',
      });
    }
    if (path === '/api/auth/demo') {
      signedIn = true;
      return reply(session);
    }
    if (path === '/api/auth/logout') {
      signedIn = false;
      return reply({});
    }
    if (path === '/api/connectors') return reply(connectors);
    if (path.startsWith('/api/connectors/') && method === 'PATCH') {
      const connector = connectors.find((item) => item.id === path.split('/').at(-1));
      if (connector) connector.enabled = (request.postDataJSON() as { enabled: boolean }).enabled;
      return reply(connector);
    }
    if (path === '/api/conversations')
      return reply([
        { id: conversation.id, title: conversation.title, updated_at: '2026-11-05T12:00:00Z' },
      ]);
    if (path === '/api/runs/run-001/retry' && method === 'POST') {
      resumed = true;
      return reply({
        ...conversation.runs[0],
        id: 'run-resumed',
        status: 'completed',
        retry_of: 'run-001',
      });
    }
    if (path === '/api/runs/run-resumed/trace') return reply([]);
    if (path === `/api/conversations/${conversation.id}` && resumed)
      return reply({
        ...conversation,
        runs: [
          ...conversation.runs,
          { ...conversation.runs[0], id: 'run-resumed', status: 'completed' },
        ],
        messages: [
          ...conversation.messages,
          {
            ...conversation.messages[1],
            id: 'resumed-message',
            content: 'Continued using the saved email reads.',
            artifacts: [],
          },
        ],
      });
    if (path === `/api/conversations/${conversation.id}`)
      return reply(
        options.partial
          ? {
              ...conversation,
              runs: [
                {
                  ...conversation.runs[0],
                  status: 'failed',
                  retryable: options.recoverable ?? false,
                  error_code: 'MODEL_TIMED_OUT',
                  read_count: 1,
                  selected_count: 5,
                },
              ],
              messages: [
                {
                  ...conversation.messages[1],
                  content:
                    'I retrieved the launch messages. Calendar and Drive are unavailable, so the report is incomplete.',
                  artifacts: [],
                },
              ],
            }
          : conversation,
      );
    if (path === '/api/runs/run-001/trace')
      return reply(
        [
          'gmail.search_messages',
          'calendar.list_events',
          'drive.read_file',
          'artifact.create_pdf',
        ].map((tool, index) => ({
          id: `tool-${index}`,
          tool,
          server: tool.split('.')[0],
          status: 'completed',
          arguments: { query: 'Northstar launch' },
          data: { status: 'success', result_count: index + 1 },
          elapsed_ms: 36 + index * 17,
          sources: [sources[index % 3]],
        })),
      );
    if (path === '/api/artifacts') return reply(files);
    if (path === '/api/workspace-files') return reply([]);
    if (path.startsWith('/api/artifacts/') && path.endsWith('/download'))
      return route.fulfill({
        status: 200,
        contentType: 'application/pdf',
        headers: { 'Content-Disposition': 'attachment; filename="synthetic-browser-fixture.pdf"' },
        body: 'Synthetic browser download fixture. Actual format validation is covered by backend tests.',
      });
    if (path === '/api/approvals') return reply(approvals);
    if (path.startsWith('/api/approvals/') && method === 'POST') {
      const decision = (request.postDataJSON() as { decision: string }).decision;
      approvals = approvals.map((approval) => ({
        ...approval,
        status: decision === 'approve' ? 'consumed' : 'rejected',
      }));
      return reply({ status: decision === 'approve' ? 'consumed' : 'rejected' });
    }
    if (path === '/api/mcp/servers')
      return reply(
        ['gmail', 'calendar', 'drive', 'artifact', 'demo'].map((id) => ({
          id,
          name: `${id[0]?.toUpperCase()}${id.slice(1)} MCP`,
          transport: 'streamable_http',
          protocol_version: 'fixture-protocol',
          status: 'healthy',
        })),
      );
    if (path === '/api/mcp/tools')
      return reply(
        [
          'gmail.search_messages',
          'gmail.send_draft',
          'calendar.list_events',
          'drive.read_file',
          'artifact.create_pdf',
        ].map((name) => ({
          name,
          server: name.split('.')[0],
          input_schema: {
            type: 'object',
            properties: { query: { type: 'string' } },
            additionalProperties: false,
          },
          output_schema: { type: 'object' },
          risk: name.includes('send') ? 'EXTERNAL_EFFECT' : 'READ',
          enabled: true,
          digest: 'synthetic-schema-digest',
        })),
      );
    if (path === '/api/settings')
      return reply({
        provider: 'fake',
        provider_url: 'local synthetic model',
        model: 'deterministic-demo',
        llm_consent: false,
        timezone: 'America/Chicago',
      });
    return reply({ detail: 'Browser fixture endpoint not implemented' }, 404);
  });
  return mutations;
}
