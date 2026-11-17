# Application API reference

The public prefix remains `/api`; internal `api/v1` modules do not add `/v1`. The generated [OpenAPI document](../../packages/shared-types/openapi.json) is the complete route/type authority.

| Area | Existing interfaces |
|---|---|
| Health | GET `/api/health`, `/api/ready` |
| Identity | Session, demo/login/logout, Google start/callback/disconnect and Drive Open-with |
| Conversations | List/create/read/delete; message submission with stable request IDs |
| Runs | SSE events, trace and cancellation |
| Approvals | List proposals and exact approve/reject decisions |
| Connectors | Status and local enable/disable |
| Artifacts | Owned list/metadata/download/delete |
| Settings | Timezone and provider-bound sharing consent |
| MCP inspection | Discovered servers and tools |
| Account | Local deletion and authority invalidation |

Sessions use HttpOnly cookies; mutations require CSRF and permitted Origin. Server-side identity establishes ownership, not submitted user/account headers. Source/result/error/event contracts stay typed and bounded.

SSE IDs are persisted; Last-Event-ID replays output without execution. Repeated message IDs return the existing run or reject conflicting reuse. Downloads are authenticated attachments. Browser requests cannot bypass orchestration/MCP authorization to execute arbitrary tools.
