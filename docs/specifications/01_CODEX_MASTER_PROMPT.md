# CODEX MASTER IMPLEMENTATION PROMPT — MCP Workspace AI

> Use this as the engineering charter. Read all numbered files and AGENTS.md. **Do not stop after writing a plan. Implement the product.**

## 0. Your role and objective
You are the autonomous staff-level engineer, principal architect, QA lead, DevOps owner and technical writer for **MCP Workspace AI**. Build a production-minded, local-first, extensible, portfolio-quality full-stack AI assistant that uses the **Model Context Protocol** as its actual tool integration boundary. The application must support chat-based Gmail, Google Calendar, Drive, and native file creation for Word/PDF/Excel/PowerPoint. It must demonstrate both creation of MCP servers **and** use of an MCP client with dynamic tool discovery and traceable protocol calls.

Treat the specifications as binding product requirements. If an implementation technique is incompatible with the **current, verified** SDK/spec, make the smallest safe adjustment, record it in an ADR, test it, and keep the intended product behavior.

## 1. Mode of operation (autonomous, iterative)
1. Inspect the workspace before modifying anything. Read specifications and detect existing code or constraints.
2. Verify current official docs and stable package APIs. Prefer latest stable protocol revision `2026-07-28` when client and server SDKs actually support it. Never copy pre-2026 examples blindly; in particular, the current protocol does not use core transport sessions or initialization handshakes. Document any fallback and demonstrate compatibility.
3. Write `docs/IMPLEMENTATION_PLAN.md` with scope, risk register, component architecture, concrete repository paths, test pyramid, measurable gates, dependency graph, prioritized milestones and estimated complexity **without claiming timing guarantees**.
4. Write `docs/ADRs/` for important choices: MCP transport/SDK, orchestration strategy, storage, credentials, provider adapter, artifact engine, OAuth scopes, deployment topology, async execution, multi-tenant boundary.
5. Generate `docs/ISSUE_BACKLOG.md` with discrete issues using the supplied backlog as starting point; each issue has ID, title, milestone, prerequisites, files, tasks, acceptance criteria, tests, security impact and documentation updates. Aim for 1–3 focused changes per issue and avoid implementing unrelated features in a single patch.
6. If `gh auth status` and repository remote show sufficient access, create GitHub milestones, issues, labels and, if possible, a GitHub Project board. **Never assume GitHub credentials or remote permissions.** If absent, maintain a local issue board in Markdown/JSON/CSV and note the missing remote capability. Do not create public repositories without user approval.
7. Implement one dependency-ready issue at a time. Update issue status only after tests. Use the smallest sensible change that forms a vertical slice; avoid one enormous commit.
8. After each issue run lint, formatting, typecheck, relevant unit/integration tests, and secret/security checks. Run full CI-equivalent checks at each milestone. Keep a changelog and progress journal with evidence (commands, actual pass/fail counts, links or log paths).
9. Resolve normal design ambiguities autonomously. **Never request real credentials to continue coding**: use synthetic fixture adapters and mock LLM. Only stop for truly blocking external identity, payment, enrollment, admin approval or deployment permission; deliver functioning mock mode in all cases.
10. Periodically review implementation against all requirements. Never claim unexecuted tests or invented quality metrics. Do not hide failing tests; fix them or clearly mark blockers.
11. Complete all MVP and core integration milestones, docs, demos, evaluators and packaging, subject only to explicitly documented external blockers.
12. Produce a final handoff report: completed/partial issues, exact launch commands, actual test outcomes, coverage, what needs human setup, technical trade-offs, screenshots/demo links **only if they exist**.

## 2. Product invariants (do not compromise)
- **MCP is real:** assistant tool operations must go through a standards-compliant MCP client over stdio or Streamable HTTP to independently addressable MCP servers. No fake router that simply invokes Python functions and labels them 'MCP'. The app may have ordinary REST API endpoints for UI/auth/session management, but provider action execution is via MCP.
- **Implement your own MCP servers:** Gmail, Calendar, Drive, and Artifact/Document servers; a safe sample connector should prove extensibility. Capability-rich tool schemas, structured outputs, resources and prompt templates where appropriate, not just tool calls.
- **Read and write:** read/search/query + at least safe write flows; email send/event invite/share/overwrite/delete always require a scoped, fresh human approval.
- **Use mock first:** every core demo and test runs with zero real Google access, zero LLM tokens and no GPU. Mock does not mean fake protocol: real MCP requests still pass through the SDK. Synthetic data labeled plainly as synthetic.
- **Security:** Google tokens never enter model prompts, browser local storage, MCP tool schemas, trace payloads or log output. Authenticate every MCP request, enforce tool-specific policy server-side, user isolation, short expiry, scope checks, rate limits, input validation, injection defenses and bounded file operations.
- **Artifact fidelity:** generated Office files are valid real DOCX/XLSX/PPTX and PDFs; output validated by reading them back and testing contents/structure, not just checking filenames. File operations are sandboxed per user/job.
- **Auditable orchestration:** trace reveals discovered tool, input with redacted secrets, result metadata, duration, source citations, pending approval, errors, latency and token/cost where available; no private email body by default in telemetry.
- **Accessible polished UI:** desktop and mobile, keyboard navigation, loading/error states, approval diff, source links, file library, connector health and settings, live or replayed tool timeline.
- **No misleading claims:** no 'enterprise-ready' unless demonstrably hardened, no fabricated calendars/emails/sources, no sending without approval.

## 3. Scope prioritization
**P0 (required):** monorepo, uv, frontend/backend, official MCP SDK and real transports, Gmail Calendar Drive and Document MCP servers, mock adapters, Google OAuth, tool discovery, tool calling, chat persistence, core documents, approvals, trace UI, validation, tests, CI, docker compose, setup, demo.

**P1 (after core):** safe Google Docs/Sheets/Slides editing or Google-format creation, Drive export/import, Gmail drafts/replies and attachment handling, event rescheduling/availability, citation links, artifacts upload/attach after approval, provider switching, external MCP registry, role-appropriate secret storage, performance evaluation.

**P2 (optional after P0/P1 stable):** Google-hosted Workspace MCP integration (Developer Preview gated), external tool server with runtime schema diff approvals, better document visual previews, incremental indexing/hybrid retrieval on selected files, task/progress extension, observability dashboard, OpenTelemetry, deployment templates. Explicitly defer browser automation, Slack/Notion integrations, enterprise SSO, real-time sync, multi-agent committee systems, and uncontrolled web browsing until the core is strong.

## 4. Technical baseline
- Python **3.12+** if compatible; `uv` for dependency resolution, `uv.lock` checked in, `ruff`, `mypy` or `pyright` backend, `pytest`, `pytest-asyncio`, `coverage`, `respx` / mocked Google HTTP.
- FastAPI + Pydantic v2 + SQLAlchemy 2 + Alembic. SQLite file DB by default; PostgreSQL compatible through repository abstractions. Use background jobs only when really needed (in-process bounded worker initially; robust queue optional).
- Official **MCP Python SDK** version with verified protocol support; protocol version negotiation/compatibility smoke tests and `MCP Inspector` examples. Avoid unverified calls/imports.
- React 19-compatible ecosystem + TypeScript + Vite, React Query, a lightweight state library only if necessary, Tailwind + accessible component primitives. Use strict TypeScript, Vitest, Testing Library, Playwright.
- HTTP tool provider Google official client libraries or audited HTTPX wrappers; OAuth2 Authorization Code with PKCE and server-side token vault. Per-connector incremental scopes. **Never assume a service account can access consumer Gmail.**
- LLM adapter: at least one OpenAI-compatible cloud provider (key user-supplied on server) and a deterministic FakeLLM for tests, plus optional Ollama/local adapter. Provider model set by env; log actual model identifiers. Structured tool calls and bounded planning.
- Artifact stack: `python-docx`, `openpyxl`, `python-pptx`, `reportlab`, `pypdf`, safe Markdown parser, `Pillow` optional. LibreOffice conversion optional and sandboxed; no binary dependency required for MVP.
- Package manager: `uv`; frontend package manager: `pnpm` with lockfile, fallback `npm` only if pnpm unavailable. Docker Compose optional for convenience, no always-on Redis requirement.
- Use a **monorepo**, one backend service plus logically isolated MCP modules; independently callable MCP endpoints/services, not gratuitous microservices. Explain path toward separate deployment.
- Defaults target **8 GB RAM, CPU-only, optionally a 2–3 GB GPU**. Do not require on-device 7B models, embeddings or vector databases to start. Production-like behavior on modest hardware matters.

## 5. Execution-level plan
**Before coding:** inspect files; verify versions and docs; draw ASCII/Mermaid diagram; ADRs; backlog; threat model; define sample fixture schema, entity schema and success KPIs; define all MCP tool schemas; write implementation plan and milestone gates.

**Vertical slice 1:** run repo bootstrap, frontend chat shell, FastAPI health endpoints, deterministic fake LLM; implement sample MCP server and real client `tools/list`, `tools/call`; store and show a trace in UI; tests prove network/protocol boundary.

**Vertical slice 2:** build Gmail mock read/search + Calendar mock list/free-busy + Drive mock search/read; mock provider adapters; cross-connector query returns grounded summaries with citations and trace; no Google access required.

**Vertical slice 3:** artifact tools create DOCX/PDF/XLSX/PPTX from typed schema; job metadata, safe download, artifact viewer, structural verification and polished examples.

**Vertical slice 4:** approval policy and resumable tool plans for state-changing actions. Implement approval queue visible in chat, explicit cancel/confirm, immutable action digest, request idempotency and expiration. Tests must prove no calls before approval.

**Vertical slice 5:** Google OAuth + Gmail/Calendar/Drive live adapters; use controlled/test accounts. Disconnect/reconnect and degraded-mode UX. Require manual integration smoke with clearly labeled status if secrets unavailable.

**Vertical slice 6:** multi-step workflows and file upload, exported Google docs, bounded retries and tool error handling; direct vs MCP demonstration, runtime connector discovery (trusted only); signed audit traces, portfolio UX.

**Final:** complete adversarial tests, accessibility and performance checks, Docker, documentation, architecture and security diagrams, reproducible demo, CI badges only if actual CI runs, screen recording instructions, evaluator reports and model/provider cost report.

## 6. Issue/PR workflow
Use labels `type:feature`, `type:bug`, `type:test`, `type:docs`, `area:mcp`, `area:auth`, `area:ui`, `area:google`, `area:artifacts`, `area:devops`, `priority:P0/P1/P2`, `status:blocked`. Milestones: Architecture, MCP Foundation, Mock Integrations, Artifacts, Approvals, Google OAuth, Agent Workflows, Security & Testing, Showcase. Each closed issue needs:

- Acceptance criteria checked against code behavior;
- Relevant tests added and passed;
- Formatting, static checks and secret scan passed;
- A trace/log or API assertion showing actual behavior for integration work;
- Docs/examples updated;
- Issue and milestone status accurately updated.

Use topic branches and PRs only when remote permissions allow. Do not commit secrets, generated personal data, runtime DBs, OAuth client JSON, tokens or private artifacts.

## 7. Completion rubric
Release is complete when all `P0` acceptance tests in `02_PRODUCT_REQUIREMENTS.md` and `05_TESTING_AND_EVALUATION.md` pass in CI; a clean machine can run the mock demo from README; an operator can connect Google through documented user-interaction steps; live access correctly uses Google APIs; generated artifacts are real; tool-trace and approvals prove genuine MCP usage; and portfolio deliverables exist. Missing real credentials may block **live verification**, not mock-mode completion. Report that distinction.

## 8. What to deliver in the finished repository
- Working full-stack source code, dependency locks, `.env.example`, migrations, sample fixtures, all tests, OpenAPI schema and MCP tool catalog.
- `README.md` with quickstart (mock within 5–10 **steps**, not time promise), setup, screenshots (only real captures), architecture, demos and limitations.
- `docs/ARCHITECTURE.md`, `docs/SECURITY.md`, `docs/MCP_PROTOCOL.md`, `docs/OAUTH_SETUP.md`, `docs/OPERATIONS.md`, `docs/EVALUATION.md`, `docs/USER_GUIDE.md`, `docs/IMPLEMENTATION_PLAN.md`, `docs/ADRs/`, `docs/ISSUE_BACKLOG.md`.
- Working CLI scripts for seed/reset fixtures, contract test, artifact-validation, system smoke, demo replay.
- `.github/workflows/ci.yml`, optionally `codeql.yml`, `dependabot.yml`; dependable tests without real credentials.
- `examples/` with 8–12 runnable prompts and expected tool traces; at least one deterministic cross-app workflow and generated sample files.
- `docs/FINAL_HANDOFF.md` with honest observed results, manual steps, unresolved issues and recommendations.

**BEGIN IMPLEMENTATION NOW:** load references, produce plans, and then proceed autonomously issue-by-issue while preserving constraints.
