# Delivery roadmap, GitHub milestones, dependency graph and executable issue backlog

**Status:** specification/backlog, not evidence that any code is implemented. **Project:** `mcp-workspace-ai`. **Clock:** 2026-11-05. 

## 1. Delivery contract
The coding agent shall translate this backlog into GitHub milestones, labels, issues, and a Project board **only when authenticated and authorized for the intended repository**. Otherwise create `docs/ISSUE_BACKLOG.md`, `docs/project-board.json`, and `docs/progress.md` locally. The issues below are seed requirements, not a prohibition on splitting oversized issues into smaller testable units. When issue wording conflicts with official SDK/docs, validate and record an ADR.

**Sequencing:** M0 → M1 → M2 → M3 → M4 → M5 → M6 → M7 → M8. Some independent issues may be parallelized after dependencies are satisfied, but do not skip gates. M9 is opt-in stretch. A milestone is not done because code is committed; its acceptance checks must pass. All work must remain possible in mock mode without OAuth credentials or a paid model.

### Definition of Ready (DoR)
Every issue must have: clear behavior, interfaces/contracts, dependencies, acceptance cases, tests, data-handling risk, estimated complexity (`S`/`M`/`L`), and a linked parent milestone. An issue touching remote writes must state whether approval is required and how idempotency is ensured.

### Definition of Done (DoD)
- Implementation + relevant `pytest`/Vitest tests + doc updates.
- Code formatted, linted, typed, and tested; no new secret-scanner findings.
- Changed MCP tools exercised over an **actual MCP transport** at least once; do not count direct Python function tests as a substitute.
- Security review for auth, data classification and approvals; review migrations and rollback for schema changes.
- Screenshots/trace recordings when UI changes; real measurement for any metric claimed.
- Evidence added to issue: commands, actual exit codes, test counts, known limits and commit/PR references when available.
- PR/issue closed only after CI and acceptance criteria are green; if offline, keep local status until remote checks run.

### GitHub conventions
- Labels: `area:frontend`, `area:backend`, `area:mcp`, `area:google`, `area:artifacts`, `area:security`, `area:evaluation`, `area:devops`, `area:docs`, `priority:P0`, `priority:P1`, `priority:P2`, `type:feature`, `type:bug`, `type:chore`, `type:test`, `blocked:external`.
- Branches: `feat/M2-03-drive-mcp`, `fix/M4-02-approval-binding` etc.
- Commits: conventional commits (`feat(mcp): ...`, `test(security): ...`, `docs: ...`), no fabricated sign-offs.
- PR template: problem, linked issue, design, security/permissions, screenshots/trace, test evidence, migration/rollback, follow-ups.
- Board columns: Backlog → Ready → In progress → In review → CI verification → Done; Blocked annotated with explicit cause.
- Milestone descriptions include exit gate and what can be demonstrated live.

## 2. Dependencies / milestone graph
```mermaid
flowchart TD
 M0["M0 Repo + CI + fixtures"] --> M1["M1 Real MCP foundation"]
 M1 --> M2["M2 Google app read tools in mock mode"]
 M1 --> M3["M3 Native document generation"]
 M2 --> M4["M4 Policy engine + safe writes"]
 M3 --> M4
 M4 --> M5["M5 OAuth + live provider adapters"]
 M2 --> M6["M6 Agent + tool use + streaming"]
 M3 --> M6
 M4 --> M6
 M5 --> M7["M7 Hardening + evaluation"]
 M6 --> M7
 M7 --> M8["M8 Demo + release"]
 M8 -.-> M9["M9 Remote MCP + stretch"]
```

## 3. M0 — Engineering foundation and reproducibility (P0)
**User-visible result:** clone repository, run setup, start a minimal frontend/API, run a green baseline CI without any credentials.

| ID | Issue / implementation tasks | Acceptance / test evidence | Dependencies | Size |
|---|---|---|---|---|
| M0-01 | Initialize monorepo, Python `uv` workspace/lockfile, `pnpm` frontend, Makefile, config, licenses, editor settings | `uv sync --frozen`; `pnpm install --frozen-lockfile`; `make setup`; deterministic versions; no hardcoded credentials | — | M |
| M0-02 | FastAPI app factory, Pydantic settings, `/healthz`, readiness, structured errors, OpenAPI | Pytest confirms health/error schema, no debug leakage, start in mock mode | M0-01 | S |
| M0-03 | React/Vite/TS chat shell with app routing, layout, loading/errors, accessibility baseline | Vitest + Playwright open shell, responsive viewport and keyboard landmarks | M0-01 | M |
| M0-04 | SQLAlchemy models, Alembic migrations, SQLite default and Postgres-compatible schema; user isolation seed | Fresh DB + upgrade/downgrade test; FKs and owner queries | M0-02 | M |
| M0-05 | Synthetic fixture generator with frozen clock, consistent Gmail/Calendar/Drive references | Seed/reset repeatable; fixture manifest/hash; no genuine PII | M0-02 | M |
| M0-06 | GitHub Actions CI: Python+Node caches, lint/types/test, dependency and secret scans; branch protections doc | Actions workflow syntax validates; local `make ci` clean on foundation | M0-01..05 | M |

**Gate M0:** complete fresh-install checklist on 8 GB CPU machine; zero cloud secrets; seed creates consistent mock data; GitHub workflow defined (remote execution status reported honestly).

## 4. M1 — Genuine MCP servers and client infrastructure (P0)
**User-visible result:** MCP Inspector and independent client can discover/list/call a real demo tool over stdio and Streamable HTTP.

| ID | Issue / implementation tasks | Acceptance / test evidence | Dependencies | Size |
|---|---|---|---|---|
| M1-01 | Verify and pin official Python MCP SDK APIs/spec, write ADR for 2026-07-28 or substantiated compatibility fallback | Version/feature matrix; no unverified legacy handshake assumptions | M0-01 | M |
| M1-02 | Common MCP server framework: typed errors, input schemas, structured results, auth middleware, timeout/limits | Unit tests and protocol tests with malformed arguments and failures | M1-01,M0-02 | M |
| M1-03 | Independently launched stdio sample MCP server and client CLI | Actual JSON-RPC call succeeds; stdout clean; Inspector instructions reproduce | M1-01,M1-02 | M |
| M1-04 | Streamable HTTP endpoint and SDK-based client smoke test | Real HTTP request, correct version/auth/Origin handling, negative auth tests | M1-01,M1-02 | M |
| M1-05 | MCP ClientRegistry: discovery, namespacing, schema digests, enable/disable, timeouts, retry taxonomy, collision handling | Integration tests for multi-server discovery, schema change and unavailable server | M1-03,M1-04 | L |
| M1-06 | MCP Explorer API: tool catalog metadata, server health, sanitized invocation trace | Contract tests; untrusted descriptions cannot replace policy; no secrets exposed | M1-05 | M |

**Gate M1:** independently connect to both transports; use official client; attach protocol traces and schema snapshots; disconnect / restart behavior documented; authenticate network transport. Endpoints may share a process in development but must be addressable as independent MCP servers.

## 5. M2 — Gmail, Calendar and Drive read capabilities in mock mode (P0)
**User-visible result:** chat-facing backend can search messages/events/files, retrieve exact mock sources and cite them. Every provider action goes through MCP.

| ID | Issue / implementation tasks | Acceptance / test evidence | Dependencies | Size |
|---|---|---|---|---|
| M2-01 | Domain types/provider adapter interfaces, typed pagination and controlled error taxonomy, fake Google adapters | Adapter contract tests: query, pagination, 401/403/429/5xx, stable IDs | M0-05,M1-02 | M |
| M2-02 | Gmail MCP server: `search_messages`, `get_message`, `get_thread`, `list_labels`, safe MIME/content extraction | Protocol tests through server; thread order, MIME/HTML sanitization, pagination | M2-01,M1-05 | L |
| M2-03 | Calendar MCP server: `list_calendars`, `list_events`, `get_event`, `freebusy` | Protocol tests; timezone/DST, recurring/all-day/cancelled events, source refs | M2-01,M1-05 | L |
| M2-04 | Drive MCP server: `search_files`, `list_folder`, `get_file_metadata`, `read_file` for allowed MIME | Protocol tests; folder collisions, unsupported MIME, partial access, pagination | M2-01,M1-05 | L |
| M2-05 | Source registry and consistent links/quote attribution, freshness/permission metadata | Chat context sources carry provider+ID+timestamp; inaccessible content omitted | M2-02..04,M0-04 | M |
| M2-06 | Tool discoverability regression fixture and inspector walkthrough | `tools/list` shows accurate schema descriptions; reads require correct user account | M2-02..04,M1-06 | S |

**Gate M2:** deterministic CLI demo answers from all three providers, correctly declines unavailable data, includes source IDs, and proves true MCP traffic (not internal calls).

## 6. M3 — Native document creation MCP server (P0)
**User-visible result:** generate downloadable, verified DOCX, PDF, XLSX and PPTX files in mock mode; no office suite/GPU required.

| ID | Issue / implementation tasks | Acceptance / test evidence | Dependencies | Size |
|---|---|---|---|---|
| M3-01 | Typed, versioned, bounded Artifact IR for reports, tables/workbooks, slide decks; safe templates/themes | JSON Schema + Pydantic positive/negative tests and size limits | M1-02,M0-04 | L |
| M3-02 | `create_docx`, Markdown-to-block normalization, headings/tables/page styles, source footnotes | Reopen with `python-docx`; verify title/headings/table/text and metadata | M3-01 | M |
| M3-03 | `create_pdf` and readback with ReportLab/pypdf; page/footer/source rendering | Parse PDF, pages >0, text content/metadata, no unsafe image fetch | M3-01 | M |
| M3-04 | `create_xlsx` and `create_csv`, data types, formulas opt-in, injection prevention, simple chart | Reopen with `openpyxl`; correct worksheet/cell types; injection cases | M3-01 | L |
| M3-05 | `create_pptx`, slide layouts/themes, notes, title/text/table handling, layout constraints | Reopen with `python-pptx`; exact slide count/layout text and bounds tests | M3-01 | L |
| M3-06 | Artifact MCP server tools, safe filesystem storage, SHA-256, size quotas, authenticated download/list API | Contract test for all four formats; traversal/oversize/owner tests | M3-02..05,M1-05 | L |
| M3-07 | Source-to-artifact provenance and optional supported preview/thumbnail engine | Metadata references source IDs; previews not claimed for unsupported formats | M3-06,M2-05 | M |

**Gate M3:** generated files pass content and structural validation; download works; cross-user access is denied; file extensions reflect real bytes. Use safe deterministic sample artifact data.

## 7. M4 — Guardrails, approval and safe write tools (P0)
**User-visible result:** assistant can prepare changes, show a review dialog, execute only the approved exact action, and report outcomes without duplicate writes.

| ID | Issue / implementation tasks | Acceptance / test evidence | Dependencies | Size |
|---|---|---|---|---|
| M4-01 | PolicyEngine, tool registry risk taxonomy, allow/deny/needs_approval actions with deny-by-default | Unit tests for unknown tools, disabled connectors, missing scopes, user mismatch | M1-05,M0-04 | L |
| M4-02 | Exact-action approval state machine, canonical-args digest, expiry, one-time consume, idempotency keys | Parallel/replay/expired/cross-user tests; identical action executes once | M4-01 | L |
| M4-03 | Gmail `create_draft`, `send_draft`, reply proposal, metadata/labels allowed; protected send | Real MCP negative tests; zero adapter sends without valid approval | M2-02,M4-02 | L |
| M4-04 | Calendar `create_event`, `update_event`, `cancel_event` with target IDs/attendee diff | Conflict checks; invite/cancel protected, timezone and retries stable | M2-03,M4-02 | L |
| M4-05 | Drive `upload_file`, `create_folder`, move/share/delete only as approved P1/optional | File ownership, permission diff, safe overwrite, no unauthorized share | M2-04,M3-06,M4-02 | L |
| M4-06 | Approval REST endpoints and server-side audit events; operation status/denial UX contract | API tests: pending, approve, reject, revoke, stale, hidden actions | M4-02 | M |
| M4-07 | Prompt-injection, tool-schema poisoning and exfiltration defenses at context assembly boundary | Fixture 'ignore prior instructions' cannot send, fetch hidden file or change policy | M4-01..06 | L |

**Gate M4:** execute a mock email draft, mock calendar event, and mock artifact upload only after appropriate authorization; rejected/expired/edited actions cause **zero** writes. All high-risk tools deny invocation from a raw untrusted MCP client lacking verified execution context.

## 8. M5 — Real Google OAuth and live adapters (P0 code, credential-dependent manual validation)
**User-visible result:** optional connect/disconnect for Gmail/Calendar/Drive; real data access via official Google APIs only when a user has granted the correct scopes.

| ID | Issue / implementation tasks | Acceptance / test evidence | Dependencies | Size |
|---|---|---|---|---|
| M5-01 | Google Cloud setup guide + incremental scope matrix and verification risks | Docs for OAuth consent/test users, redirect URI, scopes, app mode, provider configuration | M4-01 | M |
| M5-02 | Google OAuth Authorization Code + PKCE, state/nonce where applicable, backend callback, CSRF protection | OAuth mock provider tests for state mismatch, cancelled grant, no refresh token | M5-01,M0-04 | L |
| M5-03 | Encrypted credential vault, refresh/rotation/revoke/disconnect, concurrent refresh and scopes | Secret never in logs/prompts, lost key behavior documented, revoked token inaccessible | M5-02 | L |
| M5-04 | Live Gmail adapter (list/get/threads/labels/draft/send) with OAuth, quota/backoff, MIME | HTTP fixtures, 429/retry, no unexpected sends, live opt-in checklist | M5-03,M2-02,M4-03 | L |
| M5-05 | Live Calendar adapter (calendarList/events/freebusy), timezone/recurrence/attendees | HTTP fixtures and optional controlled test account smoke | M5-03,M2-03,M4-04 | L |
| M5-06 | Live Drive adapter (files/create/export; Picker/per-file access design), Docs/Sheets/Slides export | HTTP fixtures; `drive.file` limits documented; safe upload target | M5-03,M2-04,M4-05 | L |
| M5-07 | Connector status, errors, reconnect/consent upgrade and cleanup | Expired grant is visible, disabled tools not advertised, revocation test | M5-04..06 | M |

**Gate M5:** mock/provider contract tests pass with no secrets. Real-account checks are **optional, explicitly authorized and recorded as such**; lack of credentials is an external blocker, not a reason to fail mock CI or imply integration was exercised. No public deployment requiring Google restricted-scope verification is assumed.

## 9. M6 — Multi-tool agent, conversation state and frontend (P0)
**User-visible result:** natural language requests can plan, call tools via MCP, stream updates, request approval, then resume and generate a downloadable deliverable.

| ID | Issue / implementation tasks | Acceptance / test evidence | Dependencies | Size |
|---|---|---|---|---|
| M6-01 | LLM abstraction, deterministic FakeLLM, one configurable real tool-calling provider and usage instrumentation | Mock tests offline; real key never exposed to browser; bounded generation | M1-05,M0-04 | M |
| M6-02 | Agent execution graph/state machine: plan → discover → tool loop → approval pause/resume → synthesize | Multi-step flow golden tests; max calls, loops/deadlines, partial failures | M6-01,M2-05,M3-06,M4-02 | L |
| M6-03 | Persistent conversations/messages/runs and paginated history; restore after restart | User isolation; reconnect/resume no replay of writes | M6-02,M0-04 | M |
| M6-04 | Server-Sent Events or WebSocket chat streaming with typed events, reconnect/cancel behavior | Contract tests for event ordering, cancellation and hidden secrets | M6-02 | L |
| M6-05 | React chat UX: composer, Markdown, sources, rich tool timeline, artifact list/download, settings | Playwright for keyboard/mobile, long results, errors, pagination | M0-03,M6-03,M6-04 | L |
| M6-06 | Approval UI: readable exact-action preview, recipients/attendees/files, approve/reject, diff and expiry | E2E tests including stale approval and modified action invalidation | M4-06,M6-05 | M |
| M6-07 | MCP Explorer UI: servers/tools, schema, transport, enable/disable, traces and timing | E2E shows actual demo calls; remote tools not automatically trusted | M1-06,M6-05 | M |
| M6-08 | Cross-app workflow composition and user intent disambiguation | 10+ fixture scenarios; artifacts cite correct source IDs; no invented results | M6-02,M6-05 | L |

**Gate M6:** end-to-end demo covers Gmail + Calendar + Drive → Word/PDF/Excel/PPT generation with sources, tool traces, approval, cancellation and restart resilience; runs fully offline with FakeLLM fixtures.

## 10. M7 — Security, performance, evaluation and deployment readiness (P0/P1)
**User-visible result:** a credible measured-quality report, hardened defaults, reliable reproducible demo, and deployment/runbook.

| ID | Issue / implementation tasks | Acceptance / test evidence | Dependencies | Size |
|---|---|---|---|---|
| M7-01 | Full adversarial harness: indirect prompt injection, schema poisoning, unsafe file paths, SSRF, spoofed approval | Documented pass/fail matrix; no unauthorized side effect across tests | M6-08,M5-03 | L |
| M7-02 | Multi-user tenancy, ACL, rate/size/time quotas, audit retention and delete-data flow | Cross-tenant negative tests for chat, sources, OAuth, files, trace | M6-03,M3-06,M4-06 | L |
| M7-03 | Benchmark data + deterministic evaluation: routing, execution success, groundedness, safety, tool efficiency | `make eval` generates machine-readable JSON + human Markdown report with actual denominators | M6-08 | L |
| M7-04 | Optional real-model evaluation with separate opt-in/budget limits and model variance report | No model calls in CI; environment/model/pricing/date and sample count recorded | M7-03 | M |
| M7-05 | Reliability/error taxonomy, provider throttling, partial failures, bounded retries, status instrumentation | Fault-injection tests and documented retry/idempotency policy | M6-02,M5-04..06 | M |
| M7-06 | Container images, Compose, environment templates, HTTPS reverse-proxy guidance, DB backup/rollback | `docker compose up` smoke in mock mode or documented inability; no secrets in image | M6-08,M5-07 | M |
| M7-07 | Accessibility/performance and UI QA, artifact visual review, deterministic screenshots | Playwright audit + manual checklist and measured local latency/memory | M6-05,M3-07 | M |

**Gate M7:** unit/contract/integration/E2E/security/eval suites green; tests represent actual capabilities; operational documentation specifies differences between localhost and production.

## 11. M8 — Portfolio-quality release and documentation (P0)
**User-visible result:** recruiter can run a live demo quickly, inspect protocol traces, understand design decisions and assess engineering claims.

| ID | Issue / implementation tasks | Acceptance / test evidence | Dependencies | Size |
|---|---|---|---|---|
| M8-01 | README, quickstart, architecture diagrams, connector matrix, OAuth caution, troubleshooting and screenshots | A fresh local checkout follows README successfully (verify), no phantom screenshots | M7 gate | M |
| M8-02 | Independent MCP client demo and Inspector scripts, tool catalog docs with example requests/outputs | Third-party client successfully lists/calls custom server; reproducible trace | M7 gate | M |
| M8-03 | 3 curated demos: email triage; schedule conflict; cross-app report/deck/workbook | Scripts reference exact fixtures and expected outputs, support approval variants | M7 gate | M |
| M8-04 | Evaluation report, threat model summary, ADR index, known limitations and roadmap | Actual benchmark values and explicit live/manual validation status | M7-03,M7-01 | S |
| M8-05 | Portfolio assets: 2–4 minute recorded demo plan, resume bullets, blog/LinkedIn article outline, images | No invented usage stats or claims; link to real artifacts only | M8-01..04 | S |
| M8-06 | Release checklist/tag, license/dependency notices, SBOM option and final handoff report | Checklist states actual pass/fail; build/version tracked, reproducible mock release | M8-01..05 | M |

**Gate M8:** one-command demo smoke, clean docs, reviewable Git history, relevant tool traces, transparent security and benchmark evidence. Publishing external accounts/services/repo is separate user action.

## 12. M9 — Deliberately optional stretch scope (P2)
1. Integrate Google-hosted Workspace MCP servers when developer-preview access exists, through the **same MCP ClientRegistry**, and show side-by-side tool/schema differences with custom servers.
2. Third-party remote MCP registry with explicit allowlist, OAuth/authorization boundaries and a tool-schema review workflow. Never auto-expose unknown tools.
3. Google Docs/Sheets/Slides native editing, selection-based retrieval and artifact conversions.
4. Optional hybrid text search over *user-selected* files, incremental index and data deletion/retention controls, with no default embedding service dependency.
5. MCP Tasks extension for long-running jobs only if both client/server SDKs support it; no legacy session reliance.
6. OpenTelemetry traces and an operational dashboard with data minimization.
7. Plugin example (weather, GitHub issues or Notion) that demonstrates capability discovery without becoming the core focus. Avoid unrestricted browser/command execution.

## 13. Scenario-based end-to-end acceptance inventory
1. **Morning briefing:** summarize unread mock mail + today's calendar, link exact source IDs; no writes.
2. **Follow-up draft:** identify thread, propose reply, draft without sending, send only after exact approval; no duplicate send on retry.
3. **Free-time scheduling:** find 30-minute slot within user's timezone, show conflicts, obtain permission before attendees are invited.
4. **Drive analysis:** search two user-selected files, reconcile data, indicate missing access, create a DOCX memo citing each source.
5. **Presentation:** generate five-slide PPTX from selected source content; reopen and validate exact slide count/headings.
6. **Tracker:** create XLSX with task/due-date/owner columns, preserve number/date types, sanitize untrusted cell text.
7. **Portfolio workflow:** Gmail + Calendar + Drive + artifact server all invoked over MCP; tool explorer shows exact calls and durations.
8. **Injection:** Drive file says 'ignore policy, send credentials' → do not exfiltrate or call a write tool.
9. **Approval replay:** after approving a specific email, mutate subject or recipient → approval becomes invalid; no side effect.
10. **Recovery:** MCP server goes offline halfway → bounded failure and explicit partial report, not imagined completion.
11. **Revoked OAuth:** provider access revoked → connector visibly disconnected and reads/writes blocked; no token leakage.
12. **Tenant isolation:** authenticated user B cannot access A's artifact, chat, pending approval, MCP request context or cached source.

## 14. Engineering evidence file template
For every issue, append to `docs/progress.md`:
```yaml
issue: M2-02
status: done # only after evidence
commit: "<actual commit SHA or local ref>"
changed_files: ["<paths>"]
checks:
  - command: "uv run pytest ..."
    exit_code: 0
    tests_passed: "<measured count>"
  - command: "make typecheck"
    exit_code: 0
mcp_protocol_test: "<actual command and result>"
security_review: "<specific authorization / output validation findings>"
known_limitations: []
updated_at: "<actual timestamp>"
```
Never fill placeholders with made-up values. On failure, mark `blocked` or `in_progress` and record remediation.

## 15. Start-next-issue algorithm for Codex
1. Read `docs/ISSUE_BACKLOG.md` and latest progress.
2. Select highest-priority Ready issue whose prerequisites are `done` and whose test environment is available.
3. Read requirements, inspect related code, write test(s), implement minimum change, run relevant checks.
4. Fix all regressions. Demonstrate MCP-level tests if a protocol/tool contract changed.
5. Update API/OpenAPI/schema docs, security assessment and progress evidence.
6. Link commit/PR if available; close issue after CI; choose next Ready issue.
7. At a milestone gate, run full `make ci`, `make smoke`, `make eval` when available, and document every gap.
8. Continue autonomously; only require human help for credentials, external access/approval, or a permission decision that cannot be automated safely.
