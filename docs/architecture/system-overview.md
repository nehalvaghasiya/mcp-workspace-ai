# System overview

The repository is a uv/pnpm workspace with one supported backend process. FastAPI hosts application APIs and five independently addressable official-SDK MCP endpoints. React consumes REST and persisted SSE events. Provider calls occur inside authenticated MCP handlers, even when host and servers share a process.

| Workspace | Owns |
|---|---|
| API application | Routes, sessions, OAuth/vault, database models, agents/LLM, approvals, metadata and lifecycle |
| Gmail, Calendar, Drive | Canonical tool definitions, typed inputs, snapshots and mock/live providers |
| Documents | Artifact IR, seven generators, validators, templates and licensed fonts; namespace remains `artifact` |
| Demo | Authenticated protocol vertical slice and safe synthetic metadata |
| Common | Contracts, signing, guards, execution interfaces, mock-store primitives and bounded extraction |
| Evaluations | Preserved cases, installed HTTP-based runner and pipeline metrics |
| Web/shared types | Responsive UI and generated API contract types |

The API assembles server definitions once. Servers import common code, never the API or another connector. The composition root injects trusted authorization, credential and operation capabilities. Those capabilities stay outside model context.

One execution context owns task/adapter registries, write/refresh locks, render limits, schema digests and deletion fences. Per-server copies would change concurrency semantics and are prohibited by the reorganization contract.

SQLAlchemy uses explicit ownership and SQLite WAL. Alembic revisions 0001 and 0002 retain their identifiers and table semantics. Mock/live state stays under `.local/{mode}`. Startup labels active runs interrupted and dispatched writes outcome_unknown; it does not redispatch them.

The default image serves the frontend and API together. Diagnostic component images retain existing CLI entrypoints and do not introduce a distributed default runtime. Redis, indexing, hosted MCP onboarding and optional monitoring/provisioning remain deferred.

See the [diagram](architecture-diagram.md), [MCP lifecycle](mcp-lifecycle.md), [data flow](data-flow.md), [agent workflows](agent-workflows.md) and [workspace ADR](../adr/0010-workspace-organization.md).
