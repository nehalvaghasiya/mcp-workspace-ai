# Approved core implementation plan

The core release covers M0–M8 from the original guides. It includes an offline synthetic demonstration, real MCP client/server traffic, multiple app users through Google sign-in, incremental connector consent, approved writes, validated native documents, and an observable browser interface. Optional remote MCP onboarding, native Google editing, extended attachments, indexing, and public deployment are deferred.

## Locked design

- One Python 3.12 package, managed exclusively with uv and uv.lock; React/TypeScript/Vite frontend with npm lockfile.
- FastAPI, SQLAlchemy, Alembic, SQLite; one process containing five independently addressable official-SDK MCP servers. App operations cross real loopback HTTP; standalone stdio is also supported.
- One typed registry defines all 31 tool inputs, risk levels and required scopes. Discovery comes from the running servers, with schema-digest checks.
- Persisted conversations, runs, events, source references, approvals and write outcomes; SSE supports reconnection without resending actions.
- Google OIDC login is separate from incremental Gmail/Calendar/Drive consent. Tokens stay encrypted server-side. Live model use requires provider-specific user consent.
- Every Google write requires a fresh exact-action approval. The downstream server consumes the approval transactionally and records a durable operation. Ambiguous writes are not automatically retried.
- Mock data and FakeLLM never contact Google or a model provider. Mock/live databases, fixtures and artifacts use separate directories.
- Drive defaults to drive.file. Existing-file Open-with integration requires a configured full domain and drive.install; localhost can use app-created files.

## Dependency order and exit gates

| Milestone | Depends on | Exit evidence |
|---|---|---|
| M0 Foundation | — | Locked setup, migrations, ownership/session boundaries, fixtures, CI definition |
| M1 MCP foundation | M0 | Real HTTP and stdio; tools/resources/prompts; authenticated calls; first chat trace |
| M2 Workspace reads | M1 | Gmail/Calendar/Drive mocks, bounded extraction, pagination/timezones and citations |
| M3 Artifacts | M1 | Seven formats, semantic readback, safe local storage and downloads |
| M4 Approved writes | M2,M3 | Eight Google writes gated at server, replay/race/changed-action tests |
| M5 Google integration | M4 | OIDC/OAuth/refresh/revocation plus live adapters verified through HTTP stubs |
| M6 Full workflows | M2,M3,M4 | Browser chat/history/streaming/approval/resume/Explorer and cross-app documents |
| M7 Verification/ops | M5,M6 | Security/evaluation/browser suites, measured reports and container checks |
| M8 Showcase | M7 | Reproducible README, actual screenshots/examples, compatibility and handoff reports |

M2/M3 have independent boundaries. Implementation ownership is recorded in ISSUE_BACKLOG.md and project-board.json. Each issue closes only after focused tests, required static checks and documentation evidence. External checks retain NOT_RUN until performed; no milestone is complete merely because files exist.

## Risks and verification

Primary risks are OAuth account/session confusion, mutable-target approval bypass, duplicate writes after network uncertainty, cross-user access, untrusted content, hostile document extraction, SDK drift and misleading demo metrics. The acceptance matrix maps each requirement to tests. Test actual TCP and stdio rather than only calling handlers. Reopen Office/PDF files and inspect semantics. Keep deterministic pipeline scores separate from real-model quality, which is opt-in and not assumed tested.

See ADRs for compact package layout, MCP compatibility, credentials, exact-action writes, Drive selection, artifact fidelity, orchestration, and evaluation accounting.
