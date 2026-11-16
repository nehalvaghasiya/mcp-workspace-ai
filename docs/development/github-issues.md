# Ten GitHub issues for MCP Workspace AI

These ten issue drafts cover the approved M0–M8 core release using the current repository layout. Copy each numbered section into a GitHub issue. `I01`–`I10` are local references; replace them with actual GitHub issue numbers when publishing.

The project already contains these implementation areas. These are full-project delivery scopes, not ten newly discovered gaps. Acceptance checkboxes are templates; the [final handoff](../verification/final-handoff.md) records actual completion and external checks. The existing [local board](project-board.json) remains the execution record.

## How to use the branch and commit commands

Run commands from the repository root. Create each branch from a base containing its completed dependencies, with no unrelated staged changes. Directory paths stage their nested files; every path below is relative to the repository root. Review `git diff --cached` before committing.

The current working tree contains the complete implementation as largely untracked files. Shared files appear in several issues because later features extend earlier interfaces. To split this snapshot into a historical commit sequence, first prepare the intermediate versions of shared files in a separate checkout. Whole-file staging of the finished snapshot can otherwise include functionality from later issues. The blocks below describe issue-scoped development commits; a branch name alone does not isolate existing working-tree changes.

Every issue includes its tests and documentation. Stage only synthetic evidence; `.env`, `.local`, credentials and private artifacts stay out of commits. GitHub publication and live Google writes require their own authorization.

| Ref | Issue title | Milestone | Dependencies | Branch |
|---|---|---|---|---|
| I01 | Establish the uv/pnpm workspace and development foundation | M0 | None | `chore/01-workspace-foundation` |
| I02 | Implement owned persistence, sessions and application lifecycle | M0 | I01 | `feat/02-owned-persistence-sessions` |
| I03 | Implement the authenticated MCP runtime and Demo server | M1 | I02 | `feat/03-authenticated-mcp-runtime` |
| I04 | Implement grounded Gmail, Calendar and Drive reads | M2 | I03 | `feat/04-workspace-read-connectors` |
| I05 | Implement validated artifacts and private downloads | M3 | I03 | `feat/05-validated-artifacts` |
| I06 | Implement exact-action approvals and durable Google writes | M4 | I04, I05 | `feat/06-approved-workspace-writes` |
| I07 | Implement Google sign-in, connector consent and live adapters | M5 | I06 | `feat/07-google-auth-live-adapters` |
| I08 | Implement bounded agents, persisted chat and streaming | M6 | I04, I05, I06 | `feat/08-agent-chat-streaming` |
| I09 | Implement the accessible workspace frontend | M6 | I07, I08 | `feat/09-workspace-frontend` |
| I10 | Complete security, evaluation, operations and release handoff | M7–M8 | I01–I09 | `chore/10-verification-release-handoff` |

Shared completion rules: use uv for all Python dependencies and the single root lockfile; use pinned pnpm with the single frontend lockfile; keep one handwritten class per file and one React component per component file. Preserve `/api` URLs, canonical tool names, the `{"request": ...}` envelope, database revisions and private storage paths. Run focused verification for each issue and the applicable combined gates before closure. Record real command exits and distinguish mock, live and manual evidence. The [specifications](../specifications/00_START_HERE.md), [approved organization](reorganization-plan.md) and [acceptance matrix](../verification/acceptance-matrix.md) define the scope.

## I01 — Establish the uv/pnpm workspace and development foundation

**Milestone:** M0 · **Complexity:** M · **Dependencies:** None

**Labels:** `type:chore`, `area:devops`, `priority:P0`

### Problem

The API, MCP servers, evaluation runner and web application need a reproducible installation and clear package boundaries. Separate dependency authorities and inconsistent commands make development and CI unreliable.

### Solution

Create eight installable Python workspace members under a non-distributable root uv project. Configure the web/shared-types pnpm workspace with Node 24 and locally bootstrapped pnpm 12.18.0. Add configuration examples, coding rules, development scripts, baseline CI and contributor templates. Preserve the requested directory ownership and original specifications.

### Acceptance criteria

- [ ] `make setup` installs all eight Python members and frontend packages with locked dependencies and no account credentials.
- [ ] There is one root `uv.lock`, one `pnpm-lock.yaml`, and no npm dependency lockfile.
- [ ] API → servers/common/evaluations, servers/evaluations → common, and web → shared-types boundaries are documented and checked.
- [ ] Class/component ownership and module-size checks pass; no callable placeholder tools are introduced.
- [ ] The documented Make targets exist, and example environment/configuration files contain no secrets.
- [ ] The security override for `@typescript-eslint/typescript-estree>minimatch` resolves to `11.0.5`.

**Verification:** `make setup`; `make architecture-check`; `uv lock --check`.

### Branch and commit

```bash
git switch -c chore/01-workspace-foundation
git add -- \
  .gitignore .dockerignore .editorconfig .python-version .env.example \
  .prettierrc.json .pre-commit-config.yaml AGENTS.md LICENSE CONTRIBUTING.md \
  pyproject.toml uv.lock package.json pnpm-workspace.yaml pnpm-lock.yaml Makefile \
  apps/api/pyproject.toml apps/api/alembic.ini apps/web/package.json \
  mcp-servers/gmail/pyproject.toml mcp-servers/calendar/pyproject.toml \
  mcp-servers/drive/pyproject.toml mcp-servers/documents/pyproject.toml \
  mcp-servers/demo/pyproject.toml packages/mcp-common/pyproject.toml \
  evaluations/pyproject.toml packages/shared-types/package.json \
  packages/shared-types/tsconfig.json .devcontainer .github/ISSUE_TEMPLATE \
  .github/PULL_REQUEST_TEMPLATE.md .github/dependabot.yml .github/workflows/ci.yml \
  scripts/__init__.py scripts/bootstrap.py scripts/bootstrap_pnpm.py \
  scripts/check_architecture.py scripts/check_frontend_architecture.mjs \
  scripts/check_dependencies.py scripts/setup.sh scripts/run_dev.sh \
  scripts/run_tests.sh config/README.md config/logging.yaml config/models.example.yaml \
  docs/specifications docs/adr docs/development docs/AGENTS.md
git diff --cached --stat
git diff --cached --check
git commit -m "chore(workspace): establish uv and pnpm project foundation"
```

## I02 — Implement owned persistence, sessions and application lifecycle

**Milestone:** M0 · **Complexity:** L · **Dependencies:** I01

**Labels:** `type:feature`, `area:backend`, `area:security`, `priority:P0`

### Problem

Conversations, credentials, approvals, files and events must survive restarts without exposing one user's data to another. Background tasks and deletion can race with writes unless the application has one owner for shared execution state.

### Solution

Implement FastAPI composition, settings, SQLAlchemy models, Alembic migrations, ownership lookups, opaque sessions, CSRF/Origin checks and encrypted credential storage. Keep tasks, adapters, locks, render limits and deletion fences in one application-scoped context. Add retention, account deletion, health/readiness and restart reconciliation.

### Acceptance criteria

- [ ] Models and migrations preserve table names and revisions; each handwritten model has its own file.
- [ ] Mock login and opaque HttpOnly sessions work; CSRF, ownership and Origin failures are rejected.
- [ ] Records, mock/live stores, artifacts and events are isolated by user and mode.
- [ ] A pre-migration synthetic database preserves sessions, artifacts, encrypted credentials and pending approvals.
- [ ] Restarted running work becomes interrupted; dispatched writes retain an explicit uncertain outcome and are not replayed.
- [ ] Deletion cancels/fences in-flight work so deleted data cannot be recreated; retention and shutdown clean up owned tasks.

**Verification:** `uv run --locked pytest tests/security/test_existing_storage.py tests/security/test_privacy.py tests/cross_server/test_recovery.py apps/api/tests/security/test_vault.py`.

### Branch and commit

```bash
git switch -c feat/owned-persistence-sessions
git add -- \
  apps/api/src/mcp_workspace_api/__init__.py apps/api/src/mcp_workspace_api/main.py \
  apps/api/src/mcp_workspace_api/core apps/api/src/mcp_workspace_api/db \
  apps/api/src/mcp_workspace_api/api/__init__.py \
  apps/api/src/mcp_workspace_api/api/middleware \
  apps/api/src/mcp_workspace_api/api/v1/__init__.py \
  apps/api/src/mcp_workspace_api/api/v1/health.py \
  apps/api/src/mcp_workspace_api/api/v1/account.py \
  apps/api/src/mcp_workspace_api/auth/__init__.py \
  apps/api/src/mcp_workspace_api/auth/session_service.py \
  apps/api/src/mcp_workspace_api/auth/permissions.py \
  apps/api/src/mcp_workspace_api/auth/token_vault.py \
  apps/api/src/mcp_workspace_api/services/__init__.py \
  apps/api/src/mcp_workspace_api/services/deletion_service.py \
  apps/api/src/mcp_workspace_api/services/retention_service.py \
  packages/mcp-common/src/mcp_workspace_common/__init__.py \
  packages/mcp-common/src/mcp_workspace_common/security.py \
  packages/mcp-common/src/mcp_workspace_common/hashing.py \
  packages/mcp-common/src/mcp_workspace_common/clock.py \
  packages/mcp-common/src/mcp_workspace_common/constants.py \
  packages/mcp-common/src/mcp_workspace_common/errors \
  packages/mcp-common/src/mcp_workspace_common/schemas \
  packages/mcp-common/src/mcp_workspace_common/py.typed \
  conftest.py tests/__init__.py tests/support tests/fixtures/legacy-storage \
  tests/security/test_existing_storage.py tests/security/test_privacy.py \
  tests/cross_server/test_recovery.py apps/api/tests/security/test_vault.py \
  docs/security/data-privacy.md docs/architecture/data-flow.md
git diff --cached --stat
git diff --cached --check
git commit -m "feat(api): add owned persistence sessions and lifecycle controls"
```

## I03 — Implement the authenticated MCP runtime and Demo server

**Milestone:** M1 · **Complexity:** L · **Dependencies:** I02

**Labels:** `type:feature`, `area:mcp`, `area:security`, `priority:P0`

### Problem

Direct calls to connector functions do not demonstrate MCP interoperability or enforce authorization at the receiving server. Duplicated schemas and discovery metadata can drift from the host's policy.

### Solution

Build the runtime with the official MCP SDK, a single typed schema/risk registry and authenticated HTTP/stdio transports. Inject trusted execution interfaces into handlers while keeping providers inside the MCP boundary. Add Demo, discovery, resources, prompts, schema pinning, tracing, the CLI and an independent client example.

### Acceptance criteria

- [ ] Demo can be discovered and called over actual loopback HTTP and a subprocess stdio transport using the official client and Inspector.
- [ ] Missing/expired assertions, wrong audiences, spoofed users, unauthorized methods and hostile HTTP Origins are rejected.
- [ ] Tools, resources and prompts have explicit read authorization; malformed/extra input fields fail validation.
- [ ] The registry owns typed inputs/outputs, scopes, risk and digests; discovery rejects unexpected schema changes.
- [ ] The CLI preserves `workspace-ai` subcommands and exposes five server entrypoints, with Documents using the public namespace `artifact`.
- [ ] SDK/version/protocol observations, disconnects and timeout behavior are documented; tokens and source bodies stay out of traces and examples.

**Verification:** `uv run --locked pytest tests/mcp_protocol`; independent client and Inspector using the [integration guide](../mcp/client-integration.md).

### Branch and commit

```bash
git switch -c feat/03-authenticated-mcp-runtime
git add -- \
  packages/mcp-common/src/mcp_workspace_common/contracts.py \
  packages/mcp-common/src/mcp_workspace_common/execution \
  packages/mcp-common/src/mcp_workspace_common/mcp \
  packages/mcp-common/src/mcp_workspace_common/server.py \
  packages/mcp-common/src/mcp_workspace_common/utils \
  mcp-servers/demo/src apps/api/src/mcp_workspace_api/mcp \
  apps/api/src/mcp_workspace_api/contracts.py apps/api/src/mcp_workspace_api/cli \
  apps/api/src/mcp_workspace_api/api/v1/tools.py \
  apps/api/src/mcp_workspace_api/services/audit_service.py \
  config/mcp-servers.example.json config/tool-policies.yaml \
  scripts/check_schema.py scripts/export_tool_policies.py \
  scripts/verify_mcp_servers.py scripts/inspector_proof.py \
  tests/mcp_protocol tests/security/test_architecture_boundaries.py \
  examples/multi-server-workflows/independent_mcp_client.py \
  docs/mcp docs/architecture/mcp-lifecycle.md
git diff --cached --stat
git diff --cached --check
git commit -m "feat(mcp): add authenticated transports registry and demo server"
```

## I04 — Implement grounded Gmail, Calendar and Drive reads

**Milestone:** M2 · **Complexity:** L · **Dependencies:** I03

**Labels:** `type:feature`, `area:mcp`, `area:google`, `priority:P0`

### Problem

The assistant needs reliable source data across three applications. Incorrect pagination, MIME parsing, timezones or file extraction can produce misleading answers and invalid citations.

### Solution

Implement read tools, schemas and synthetic providers for Gmail, Calendar and Drive behind real MCP calls. Freeze the Northstar fixtures, provide structured `SourceRef` citations and use bounded extraction for text, PDF and Office files. Keep connector state owned, narrow Drive access and retain canonical tool names.

### Acceptance criteria

- [ ] Gmail searches/messages/threads/labels support bounded pagination, MIME decoding and deterministic thread ordering.
- [ ] Calendar lists calendars/events and implements `calendar.query_freebusy`, with timezone, DST and recurrence cases.
- [ ] Drive search/list/metadata/read supports scoped files, resource keys, bounded native exports and text/PDF/Office extraction.
- [ ] Results carry valid source references; unknown or inaccessible IDs fail without cross-user leakage.
- [ ] Mock fixtures seed repeatably and never call Google or a model provider.
- [ ] Malformed archives, XML expansion, active HTML and oversized/parser-hostile inputs are rejected within documented bounds.

**Verification:** `uv run --locked pytest tests/cross_server packages/mcp-common/tests/unit/test_extraction.py`; exercise all read tools through the official MCP client.

### Branch and commit

```bash
git switch -c feat/04-workspace-read-connectors
git add -- \
  mcp-servers/gmail/src mcp-servers/calendar/src mcp-servers/drive/src \
  packages/mcp-common/src/mcp_workspace_common/mock \
  packages/mcp-common/src/mcp_workspace_common/extraction \
  apps/api/src/mcp_workspace_api/connectors/__init__.py \
  apps/api/src/mcp_workspace_api/connectors/mock_workspace.py \
  apps/api/src/mcp_workspace_api/services/source_resolver.py \
  scripts/seed_mock_data.py tests/fixtures/synthetic \
  tests/cross_server/test_gmail_adapters.py \
  tests/cross_server/test_calendar_adapters.py \
  tests/cross_server/test_drive_adapters.py \
  tests/cross_server/test_frozen_fixtures.py \
  packages/mcp-common/tests/unit/test_extraction.py \
  examples/gmail-workflows examples/calendar-workflows examples/drive-workflows \
  docs/mcp/tool-catalog.md docs/mcp/tool-catalog.json docs/architecture/data-flow.md
git diff --cached --stat
git diff --cached --check
git commit -m "feat(connectors): add grounded mock Gmail Calendar and Drive reads"
```

## I05 — Implement validated artifacts and private downloads

**Milestone:** M3 · **Complexity:** L · **Dependencies:** I03

**Labels:** `type:feature`, `area:artifacts`, `area:mcp`, `priority:P0`

### Problem

Generated files must contain usable content and remain private. A filename or successful renderer return value does not prove a valid document, safe spreadsheet or complete publication.

### Solution

Implement typed report blocks, sheets/cells and slides, named templates and seven format generators in the Documents package. Add structural/semantic readback, bounded rendering, atomic publication, provenance, metadata/list/validation tools and owner-only artifact API downloads. Package fonts, templates and licenses independently of the checkout path.

### Acceptance criteria

- [ ] DOCX, PDF, XLSX, PPTX, CSV, Markdown and sanitized HTML are generated from validated specifications through `artifact` MCP tools.
- [ ] Readback verifies text, tables, numeric/date/formula types, pages and slides as appropriate; invalid/partial files never become downloadable artifacts.
- [ ] CSV/spreadsheet injection, traversal, unsafe HTML and oversized output are handled safely.
- [ ] Metadata/list/validation and downloads enforce ownership and retain checksums, revisions and source provenance.
- [ ] Render concurrency, per-user quotas and deletion fences apply during file creation/publication.
- [ ] Installed wheels include the complete resources and render Unicode content outside the checkout; native Office visual review has its own explicit status.

**Verification:** `uv run --locked pytest mcp-servers/documents/tests/unit tests/end_to_end/test_chat_artifacts.py`; installed-wheel resource/readback probe.

### Branch and commit

```bash
git switch -c feat/05-validated-artifacts
git add -- \
  mcp-servers/documents/src mcp-servers/documents/tests mcp-servers/documents/README.md \
  apps/api/src/mcp_workspace_api/services/artifact_service.py \
  apps/api/src/mcp_workspace_api/api/v1/artifacts.py \
  packages/mcp-common/src/mcp_workspace_common/utils/artifacts.py \
  tests/support/artifact_specs.py tests/end_to_end/test_chat_artifacts.py \
  scripts/generate_examples.py examples/document-generation artifacts/.gitkeep \
  docs/adr/0006-artifact-fidelity.md docs/tutorials/user-guide.md
git diff --cached --stat
git diff --cached --check
git commit -m "feat(artifacts): generate validate and privately publish seven formats"
```

## I06 — Implement exact-action approvals and durable Google writes

**Milestone:** M4 · **Complexity:** L · **Dependencies:** I04, I05

**Labels:** `type:feature`, `area:security`, `area:google`, `priority:P0`

### Problem

Model suggestions cannot authorize email, calendar or Drive mutations. Replayed approvals, changed content and uncertain provider responses can cause unintended or duplicated effects.

### Solution

Create exact-action approval snapshots and transactional approval consumption plus durable operation creation. Enforce user/account/scope/target/content bindings inside the receiving MCP handler. Add the eight approved write tools, immutable draft MIME, conditional calendar revisions and explicit reconciliation for uncertain outcomes. Execution capabilities stay outside model context.

### Acceptance criteria

- [ ] Gmail create-draft/send-draft/apply-labels, Calendar create/update/cancel and Drive upload-artifact/create-folder require individual approvals.
- [ ] The preview includes exact content, recipients/attendees, destination and relevant revision/hash; changing any bound value invalidates approval.
- [ ] Rejection, expiry, replay, races and cross-user/account attempts produce zero provider writes.
- [ ] Approval consumption, executable-run validation and operation creation are one atomic transaction.
- [ ] Sending uses the approved MIME snapshot and rejects a changed draft; calendar updates enforce a conditional revision where supported.
- [ ] Cancellation blocks future effects; already dispatched effects retain their actual outcome. Ambiguous non-idempotent results become `outcome_unknown` without automatic redispatch.

**Verification:** `uv run --locked pytest tests/security/test_approvals.py tests/security/test_connector_authority.py tests/cross_server/test_recovery.py tests/end_to_end/test_chat_artifacts.py`.

### Branch and commit

```bash
git switch -c feat/workspace-writes
git add -- \
  apps/api/src/mcp_workspace_api/services/approval_service.py \
  apps/api/src/mcp_workspace_api/api/v1/approvals.py \
  apps/api/src/mcp_workspace_api/schemas/requests/decision.py \
  apps/api/src/mcp_workspace_api/db/models/approval.py \
  apps/api/src/mcp_workspace_api/db/models/operation.py \
  apps/api/src/mcp_workspace_api/mcp/tool_adapter.py \
  apps/api/src/mcp_workspace_api/mcp/gateway.py \
  packages/mcp-common/src/mcp_workspace_common/mcp/guard.py \
  mcp-servers/gmail/src/mcp_gmail/tools mcp-servers/gmail/src/mcp_gmail/schemas \
  mcp-servers/gmail/src/mcp_gmail/providers/mock.py \
  mcp-servers/calendar/src/mcp_calendar/tools mcp-servers/calendar/src/mcp_calendar/schemas \
  mcp-servers/calendar/src/mcp_calendar/providers/mock.py \
  mcp-servers/drive/src/mcp_drive/tools mcp-servers/drive/src/mcp_drive/schemas \
  mcp-servers/drive/src/mcp_drive/providers/mock.py config/tool-policies.yaml \
  tests/security/test_approvals.py tests/security/test_connector_authority.py \
  tests/support/security_actions.py tests/cross_server/test_recovery.py \
  tests/end_to_end/test_chat_artifacts.py docs/security/approval-policies.md \
  docs/adr/0004-exact-action-approvals.md
git diff --cached --stat
git diff --cached --check
git commit -m "feat(approvals): bind exact actions and persist one-use write operations"
```

## I07 — Implement Google sign-in, connector consent and live adapters

**Milestone:** M5 · **Complexity:** L · **Dependencies:** I06

**Labels:** `type:feature`, `area:google`, `area:security`, `priority:P0`

### Problem

Multiple users need trustworthy Google identities and least-privilege connector access. OAuth grants can expire, narrow, refresh or be revoked while requests are in flight.

### Solution

Implement server-side Google OIDC with state, nonce, PKCE and validated identity claims. Request connector permissions incrementally, encrypt credentials and coordinate refresh/revocation with the shared execution context. Add method-specific live adapters, reconnect/status endpoints and narrow Drive file selection. Keep provider-bound LLM content-sharing consent separate from Google consent.

### Acceptance criteria

- [ ] Invalid state/nonce/issuer/audience/signature, stale callbacks and account/session mismatch are rejected.
- [ ] Connector grants reflect returned scopes; refresh preserves valid grants and uses shared locking.
- [ ] Disabling a connector is local; revocation invalidates affected grants and pending execution capabilities, including in-flight refresh races.
- [ ] Live adapters map methods, pagination, MIME, conditional revisions, scope errors and bounded provider failures using mocked HTTP responses.
- [ ] Drive uses `drive.file`; domain-dependent Open-with/`drive.install` setup is documented with explicit execution status.
- [ ] Credentials, provider tokens and unauthorized raw private content never reach browser storage, logs, traces or model context.
- [ ] Mock tests make zero Google/provider requests. Real-account reads and writes retain separate NOT_RUN/actual results, with explicit authorization for live effects.

**Verification:** `uv run --locked pytest apps/api/tests/unit/test_google_auth.py apps/api/tests/security tests/cross_server/test_provider_contracts.py tests/cross_server/test_drive_adapters.py`.

### Branch and commit

```bash
git switch -c feat/07-google-auth-live-adapters
git add -- \
  apps/api/src/mcp_workspace_api/auth apps/api/src/mcp_workspace_api/api/v1/auth.py \
  apps/api/src/mcp_workspace_api/api/v1/connections.py \
  apps/api/src/mcp_workspace_api/services/connection_service.py \
  apps/api/src/mcp_workspace_api/connectors/google_workspace.py \
  apps/api/src/mcp_workspace_api/mcp/connection_manager.py \
  apps/api/src/mcp_workspace_api/schemas/requests/connector_update.py \
  packages/mcp-common/src/mcp_workspace_common/providers \
  mcp-servers/gmail/src/mcp_gmail/providers/google.py \
  mcp-servers/calendar/src/mcp_calendar/providers/google.py \
  mcp-servers/drive/src/mcp_drive/providers/google.py \
  mcp-servers/drive/src/mcp_drive/providers/resource_keys.py \
  apps/api/tests/unit/test_google_auth.py apps/api/tests/security \
  tests/support/stub_oauth.py tests/support/oauth_fixtures.py \
  tests/cross_server/test_provider_contracts.py tests/cross_server/test_drive_adapters.py \
  docs/security/oauth-setup.md docs/security/data-privacy.md \
  docs/adr/0003-identity-and-vault.md docs/adr/0005-drive-selection.md
git diff --cached --stat
git diff --cached --check
git commit -m "feat(google): add OIDC incremental consent and live connector adapters"
```

## I08 — Implement bounded agents, persisted chat and streaming

**Milestone:** M6 · **Complexity:** L · **Dependencies:** I04, I05, I06

**Labels:** `type:feature`, `area:backend`, `area:mcp`, `priority:P0`

### Problem

The application needs to turn user requests into grounded, recoverable multi-tool workflows. Unbounded loops, lost run state and reconnection-triggered effects would make chat unsafe and unreliable.

### Solution

Implement deterministic FakeLLM and one configurable OpenAI-compatible tool-calling provider. Persist conversations, messages, sources, approval pauses and ordered run events. Use a bounded orchestrator with real MCP execution, SSE event IDs/replay, cancellation, partial-failure synthesis and explicit provider-bound data-sharing consent.

### Acceptance criteria

- [ ] W01–W14 execute against frozen fixtures, including cross-app reports, approval resume, ambiguity and blocked source injection.
- [ ] Call counts, read retries, tool deadlines and total run time are bounded; unavailable connectors produce truthful partial/failed outcomes.
- [ ] SSE reconnection replays ordered events by ID without repeating tool effects; history and interrupted states survive restart.
- [ ] Duplicate message request IDs are idempotent; conflicting reuse is rejected.
- [ ] Cloud context uses only authorized content after separate consent; tool output is treated as untrusted data and cannot supply execution capabilities.
- [ ] Provider-stub tests validate tool arguments, errors and usage; mock mode always uses FakeLLM and never contacts a paid model.
- [ ] A Northstar workflow uses Gmail, Calendar and Drive sources to produce four validated files with persisted traces.

**Verification:** `uv run --locked pytest tests/end_to_end apps/api/tests/contract/test_model.py tests/cross_server/test_recovery.py`.

### Branch and commit

```bash
git switch -c feat/08-agent-chat-streaming
git add -- \
  apps/api/src/mcp_workspace_api/agents apps/api/src/mcp_workspace_api/llm \
  apps/api/src/mcp_workspace_api/schemas apps/api/src/mcp_workspace_api/api/v1/chat.py \
  apps/api/src/mcp_workspace_api/api/v1/conversations.py \
  apps/api/src/mcp_workspace_api/api/v1/settings.py \
  apps/api/src/mcp_workspace_api/services/run_service.py \
  apps/api/src/mcp_workspace_api/core/application_context.py \
  apps/api/src/mcp_workspace_api/core/execution_context.py \
  apps/api/src/mcp_workspace_api/core/lifecycle.py \
  packages/mcp-common/src/mcp_workspace_common/utils/results.py \
  apps/api/tests/contract/test_model.py tests/end_to_end \
  tests/support/stub_model.py tests/support/api_actions.py \
  tests/cross_server/test_recovery.py tests/security/test_privacy.py \
  docs/architecture/agent-workflows.md docs/api docs/adr/0007-bounded-orchestration.md
git diff --cached --stat
git diff --cached --check
git commit -m "feat(agent): add bounded persisted workflows and reconnectable chat streams"
```

## I09 — Implement the accessible workspace frontend

**Milestone:** M6 · **Complexity:** L · **Dependencies:** I07, I08

**Labels:** `type:feature`, `area:frontend`, `priority:P0`

### Problem

Users need to understand agent progress, inspect sources/files and confirm exact Google actions. An inaccessible layout or confusing permission state can conceal failures or make approvals unsafe.

### Solution

Build the React application with strict TypeScript, TanStack Query, Tailwind and accessible controls. Separate routes/providers, components, feature hooks, API/SSE services and generated shared types. Deliver sign-in/demo, conversations, sources, activity, approvals, connectors, artifact library, settings and MCP Explorer.

### Acceptance criteria

- [ ] Existing hash routes and `/api` URLs work; generated shared types are imported without web-to-common schema duplication.
- [ ] Sessions use same-origin cookies and CSRF; browser storage contains no credentials. Mutations are not silently retried.
- [ ] Users can submit/cancel/reconnect, restore history, inspect citations/traces and download owned artifacts.
- [ ] Approval screens expose exact content/recipients/attendees/targets and handle rejection, expiry and stale decisions.
- [ ] Connector status, consent/reconnect and separate LLM-sharing consent are visible; Explorer shows actual schemas and run evidence.
- [ ] All 12 existing frontend cases and 10 browser workflows pass with preserved identities; fixture and actual-backend evidence are distinguished.
- [ ] Keyboard navigation, focus restoration, reduced motion, scoped axe checks and 390×844/1440×900 layouts pass; actual synthetic screenshots are retained.

**Verification:** `make schema-check`; `make test`; `make test-e2e` with the documented Chromium dependencies.

### Branch and commit

```bash
git switch -c feat/09-workspace-frontend
git add -- \
  apps/web/src apps/web/public apps/web/tests apps/web/qa apps/web/README.md \
  apps/web/index.html apps/web/tsconfig.json apps/web/vite.config.ts \
  apps/web/vitest.config.ts apps/web/eslint.config.js apps/web/playwright.config.ts \
  apps/web/.gitignore apps/web/.prettierignore packages/shared-types \
  scripts/run_e2e.py scripts/check_frontend_architecture.mjs \
  .github/workflows/e2e-tests.yml demo/screenshots/reorganization \
  docs/tutorials/user-guide.md docs/development/testing-guide.md
git diff --cached --stat
git diff --cached --check
git commit -m "feat(web): add accessible chat approvals connectors and MCP explorer"
```

## I10 — Complete security, evaluation, operations and release handoff

**Milestone:** M7–M8 · **Complexity:** L · **Dependencies:** I01–I09

**Labels:** `type:chore`, `area:security`, `area:evaluation`, `area:devops`, `area:docs`, `priority:P0`

### Problem

The complete application needs reproducible evidence and operating procedures. Passing a few fixture tests does not establish tenant safety, portable packaging, reliable recovery, model quality or a deployable demonstration.

### Solution

Complete adversarial/isolation/fault tests, identity-preserving evaluation datasets and measured reports. Add all-package coverage, clean wheel installation, resource/database compatibility checks, no-network Docker/Compose smoke, backup/restore/key rotation and operations guidance. Finish CI workflows, examples, verified captures and a handoff that separates local verification from external acceptance.

### Acceptance criteria

- [ ] `make setup`, `make ci`, `make smoke` and `make eval` pass in their documented environments; current baseline is 221 backend, 12 frontend and 10 browser cases, with original identities preserved.
- [ ] All 52 deterministic case IDs/expectations pass; at least 12 adversarial cases run separately. Reports show actual denominators, failures, latency, memory and usage, with FakeLLM results separate from real-model scores.
- [ ] Coverage includes every production package, including unimported modules, and meets at least 86%; static ownership/import/schema checks and security audits pass.
- [ ] All eight wheels install outside the checkout without editable imports or `PYTHONPATH`; migrations, fixtures, datasets, templates, fonts and licenses load correctly.
- [ ] A non-root read-only no-network container and the default one-service Compose stack serve the built UI, generate four files and clean up only test resources.
- [ ] Backup/restore, encryption-key rotation, retention and deletion/restart recovery have validated procedures and focused tests; no private database reset is used for compatibility.
- [ ] Original specifications/historical evidence remain intact, source rollback and file/test mappings are recorded, and all 31 tools have real protocol evidence.
- [ ] Google/domain/model/native-Office/remote-CI checks show actual executed results or explicit NOT_RUN status. Manual release builds downloadable artifacts without automatically publishing/deploying.
- [ ] README, walkthroughs, catalog, Inspector/client examples, screenshots, generated files, limitations and deferred-feature READMEs are complete and linked.

**Verification:** `make ci`; `make smoke eval` against a running mock API; `uv run --locked python scripts/verify_installed_wheels.py`; build the documented image, then run `uv run --locked python scripts/verify_containers.py` and `uv run --locked python scripts/verify_containers.py --compose` sequentially with browser checks stopped.

### Branch and commit

```bash
git switch -c chore/10-verification-release-handoff
git add -- \
  evaluations tests/security tests/mcp_protocol tests/cross_server tests/end_to_end \
  tests/fixtures tests/support apps/api/tests packages/mcp-common/tests \
  mcp-servers/documents/tests apps/api/src/mcp_workspace_api/operations \
  apps/api/src/mcp_workspace_api/cli Makefile scripts/run_evaluations.sh \
  scripts/secret_scan.py scripts/verify_installed_wheels.py scripts/verify_containers.py \
  config/evaluation.yaml infra docker-compose.yml \
  .github/workflows/ci.yml .github/workflows/security.yml \
  .github/workflows/integration-tests.yml .github/workflows/evaluations.yml \
  .github/workflows/e2e-tests.yml .github/workflows/release.yml \
  README.md SECURITY.md CHANGELOG.md docs/README.md docs/architecture \
  docs/deployment docs/evaluations docs/security/threat-model.md \
  docs/verification docs/development demo examples
git diff --cached --stat
git diff --cached --check
git commit -m "chore(release): verify security packaging evaluations and local handoff"
```

## Scope coverage and external boundaries

| Requirement | Issues |
|---|---|
| FR-01 agent/chat/persistence/streaming | I02, I08 |
| FR-02 Gmail; FR-03 Calendar; FR-04 Drive | I04, I06, I07 |
| FR-05 seven artifact formats | I05 |
| FR-06 genuine MCP integration | I03, I04, I05, I10 |
| FR-07 identity/authorization/approvals | I02, I06, I07 |
| FR-08 sources and provenance | I04, I05, I08, I09 |
| FR-09 accessible responsive UI | I09 |
| FR-10 reproducible local operations | I01, I10 |
| W01–W14, adversarial/isolation/recovery, evaluation | I06, I08, I09, I10 |

These issues cover the approved core release. Hosted/third-party MCP onboarding, advanced native Google editing, indexing, extended attachments, Drive move/share, document conversion, Terraform and monitoring remain documented deferred work. Real-account Google execution, real-model evaluation, domain-dependent Drive setup, native Office visual review, remote CI and public deployment retain their separate prerequisites from the [acceptance matrix](../verification/acceptance-matrix.md).
