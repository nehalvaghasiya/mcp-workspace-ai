# Local issue backlog

GitHub CLI was unavailable; no remote issues, PRs or publishing actions were performed. All **22 core issues are done** after the final combined checks; per-issue closure evidence is in [progress.md](progress.md). External verification remains separate and NOT_RUN where listed in [FINAL_HANDOFF.md](FINAL_HANDOFF.md).

Each issue follows implementation → focused tests → static/security checks → docs → closure. Common rollback: revert the focused source change; restore a stopped-app backup for schema/data changes. Never roll back by replaying a provider write. High-risk items include exact-action approval and idempotency/unknown-outcome handling.

| ID | Issue / owner | Dependencies | Complexity | Acceptance / evidence | Status |
|---|---|---|---|---|---|
| M0-01 | Locked package, setup and app factory (root) | — | M | Locked install, health and typed error boundaries; test_api.py | done |
| M0-02 | Owned persistence, migrations and sessions (root) | — | M | Fresh schema, authenticated sessions, owner isolation and local deletion; test_api.py, test_security.py, test_vault.py | done |
| M0-03 | Frozen synthetic fixture manifest (google_connectors) | — | M | Repeatable isolated messages/events/files, error and hostile fixtures; test_connectors.py | done |
| M1-01 | Real HTTP and stdio MCP servers (root) | M0 | M | All five namespaces independently callable; auth and Origin negatives; test_protocol.py | done |
| M1-02 | Discovery, resources, prompts and schema registry (root) | M0 | M | 31 typed tools, safe resources/prompts, digest and unknown-tool checks; test_protocol.py | done |
| M2-01 | Gmail reads and MIME handling (google_connectors) | M1 | M | Query/pagination, bounded decoding, thread order and citations; test_connectors.py, test_protocol.py | done |
| M2-02 | Calendar read and availability semantics (google_connectors) | M1 | M | Time ranges, DST, recurring/all-day events and inaccessible-calendar behavior; test_connectors.py, test_workflows.py | done |
| M2-03 | Drive reads and bounded extraction (google_connectors) | M1 | M | Per-file permissions, native export, text/PDF/Office extraction and hostile limits; test_extraction.py, test_connectors.py | done |
| M3-01 | Artifact IR and seven renderers (artifact_engine) | M1 | M | Real files pass semantic/structural readback, formula and archive safety; test_artifacts.py | done |
| M3-02 | Owned library, provenance and downloads (root) | M1 | M | Opaque files, atomic publication, quotas and authenticated downloads; test_api.py, test_workflows.py | done |
| M4-01 | Exact-action policy and one-use approval (root) | M2,M3 | M | Changed/replayed/cross-user/expired approval cannot dispatch; races consume once; test_security.py | done |
| M4-02 | Eight gated Google writes (root) | M2,M3 | M | Draft/send/labels, event create/update/cancel, upload/folder all tested through MCP; test_api.py, test_protocol.py | done |
| M5-01 | OIDC, incremental OAuth and vault lifecycle (google_connectors) | M4 | M | State/PKCE/nonce, subject binding, refresh/revoke/rotation and restore verified with stubs; test_google_auth.py, test_security.py, test_vault.py | done |
| M5-02 | Live adapter contracts and narrow Drive selection (google_connectors) | M4 | M | HTTP-stub methods, exact MIME, ETags and scoped exports; domain requirement explicit; test_connectors.py, test_security.py | done |
| M6-01 | Bounded agent, SSE and resumable state (root) | M2,M3,M4 | M | Multi-app flows, persistent history, cancellation, sources and no write replay; test_api.py, test_workflows.py | done |
| M6-02 | Accessible browser workflows and generated API types (web_app) | M2,M3,M4 | M | Chat, history, artifacts, approvals, connectors/settings and Explorer; actual backend browser flows; web unit and Playwright suites | done |
| M7-01 | Adversarial boundaries and recovery (root) | M6 | M | At least 12 security scenarios, tenant isolation, limits, deletion and unknown outcomes; test_security.py, test_extraction.py | done |
| M7-02 | Measured synthetic evaluation (root) | M6 | M | 52 cases with state/tool/source/file assertions and honest model/live status; make eval | done |
| M7-03 | CI, dependency scans and containers (artifact_engine) | M6 | M | Quality and vulnerability checks, clean build, mock container smoke, isolated browser supervisor; make ci and container smoke | done |
| M8-01 | Architecture, setup and operations documentation (root) | M7 | M | Reproducible commands, ADRs, threat boundaries and exact limitations; schema/docs review | done |
| M8-02 | Independent protocol and artifact examples (root) | M7 | M | Runnable client, actual synthetic files/screenshots and protocol evidence; independent client and readback | done |
| M8-03 | Final acceptance and handoff (root) | M7 | M | Actual check exits/counts, remaining NOT_RUN checks and clean launch instructions; full verification | done |

## Per-issue implementation contracts

### M0-01
Files: pyproject.toml, Makefile, api.py. Tasks: implement the behavior above, prove it with test_api.py, and update docs/OPERATIONS.md. Security impact: local configuration. Acceptance: Locked install, health and typed error boundaries. Closure evidence is recorded in progress.md and FINAL_HANDOFF.md.

### M0-02
Files: db.py, migrations, api.py. Tasks: implement the behavior above, prove it with test_api.py, test_security.py, test_vault.py, and update docs/SECURITY.md. Security impact: identity and private rows. Acceptance: Fresh schema, authenticated sessions, owner isolation and local deletion. Closure evidence is recorded in progress.md and FINAL_HANDOFF.md.

### M0-03
Files: connectors.py, fixtures/synthetic. Tasks: implement the behavior above, prove it with test_connectors.py, and update docs/USER_GUIDE.md. Security impact: synthetic data only. Acceptance: Repeatable isolated messages/events/files, error and hostile fixtures. Closure evidence is recorded in progress.md and FINAL_HANDOFF.md.

### M1-01
Files: mcp_servers.py, runtime.py. Tasks: implement the behavior above, prove it with test_protocol.py, and update docs/MCP_PROTOCOL.md. Security impact: internal assertions. Acceptance: All five namespaces independently callable; auth and Origin negatives. Closure evidence is recorded in progress.md and FINAL_HANDOFF.md.

### M1-02
Files: contracts.py, runtime.py. Tasks: implement the behavior above, prove it with test_protocol.py, and update docs/mcp/TOOL_CATALOG.md. Security impact: schema trust. Acceptance: 31 typed tools, safe resources/prompts, digest and unknown-tool checks. Closure evidence is recorded in progress.md and FINAL_HANDOFF.md.

### M2-01
Files: connectors.py. Tasks: implement the behavior above, prove it with test_connectors.py, test_protocol.py, and update docs/USER_GUIDE.md. Security impact: untrusted mail. Acceptance: Query/pagination, bounded decoding, thread order and citations. Closure evidence is recorded in progress.md and FINAL_HANDOFF.md.

### M2-02
Files: connectors.py, contracts.py. Tasks: implement the behavior above, prove it with test_connectors.py, test_workflows.py, and update docs/USER_GUIDE.md. Security impact: time and permissions. Acceptance: Time ranges, DST, recurring/all-day events and inaccessible-calendar behavior. Closure evidence is recorded in progress.md and FINAL_HANDOFF.md.

### M2-03
Files: connectors.py, extraction.py. Tasks: implement the behavior above, prove it with test_extraction.py, test_connectors.py, and update docs/OAUTH_SETUP.md. Security impact: untrusted files and resource keys. Acceptance: Per-file permissions, native export, text/PDF/Office extraction and hostile limits. Closure evidence is recorded in progress.md and FINAL_HANDOFF.md.

### M3-01
Files: artifacts.py, assets/fonts. Tasks: implement the behavior above, prove it with test_artifacts.py, and update docs/SECURITY.md. Security impact: local files. Acceptance: Real files pass semantic/structural readback, formula and archive safety. Closure evidence is recorded in progress.md and FINAL_HANDOFF.md.

### M3-02
Files: runtime.py, api.py. Tasks: implement the behavior above, prove it with test_api.py, test_workflows.py, and update docs/USER_GUIDE.md. Security impact: filesystem ownership. Acceptance: Opaque files, atomic publication, quotas and authenticated downloads. Closure evidence is recorded in progress.md and FINAL_HANDOFF.md.

### M4-01
Files: security.py, runtime.py. Tasks: implement the behavior above, prove it with test_security.py, and update docs/SECURITY.md. Security impact: Google writes. Acceptance: Changed/replayed/cross-user/expired approval cannot dispatch; races consume once. Closure evidence is recorded in progress.md and FINAL_HANDOFF.md.

### M4-02
Files: connectors.py, agent.py. Tasks: implement the behavior above, prove it with test_api.py, test_protocol.py, and update docs/USER_GUIDE.md. Security impact: external effects and uncertain outcomes. Acceptance: Draft/send/labels, event create/update/cancel, upload/folder all tested through MCP. Closure evidence is recorded in progress.md and FINAL_HANDOFF.md.

### M5-01
Files: google_auth.py, api.py, security.py. Tasks: implement the behavior above, prove it with test_google_auth.py, test_security.py, test_vault.py, and update docs/OAUTH_SETUP.md. Security impact: credentials. Acceptance: State/PKCE/nonce, subject binding, refresh/revoke/rotation and restore verified with stubs. Closure evidence is recorded in progress.md and FINAL_HANDOFF.md.

### M5-02
Files: connectors.py, api.py. Tasks: implement the behavior above, prove it with test_connectors.py, test_security.py, and update docs/OAUTH_SETUP.md. Security impact: live provider grants. Acceptance: HTTP-stub methods, exact MIME, ETags and scoped exports; domain requirement explicit. Closure evidence is recorded in progress.md and FINAL_HANDOFF.md.

### M6-01
Files: agent.py, api.py. Tasks: implement the behavior above, prove it with test_api.py, test_workflows.py, and update docs/ARCHITECTURE.md. Security impact: model context and run state. Acceptance: Multi-app flows, persistent history, cancellation, sources and no write replay. Closure evidence is recorded in progress.md and FINAL_HANDOFF.md.

### M6-02
Files: web. Tasks: implement the behavior above, prove it with web unit and Playwright suites, and update docs/USER_GUIDE.md. Security impact: browser data and action review. Acceptance: Chat, history, artifacts, approvals, connectors/settings and Explorer; actual backend browser flows. Closure evidence is recorded in progress.md and FINAL_HANDOFF.md.

### M7-01
Files: security.py, runtime.py, extraction.py. Tasks: implement the behavior above, prove it with test_security.py, test_extraction.py, and update docs/SECURITY.md. Security impact: security boundary. Acceptance: At least 12 security scenarios, tenant isolation, limits, deletion and unknown outcomes. Closure evidence is recorded in progress.md and FINAL_HANDOFF.md.

### M7-02
Files: evaluation.py, eval. Tasks: implement the behavior above, prove it with make eval, and update docs/EVALUATION.md. Security impact: synthetic reports only. Acceptance: 52 cases with state/tool/source/file assertions and honest model/live status. Closure evidence is recorded in progress.md and FINAL_HANDOFF.md.

### M7-03
Files: Dockerfile, compose.yaml, CI, scripts. Tasks: implement the behavior above, prove it with make ci and container smoke, and update docs/OPERATIONS.md. Security impact: build and runtime isolation. Acceptance: Quality and vulnerability checks, clean build, mock container smoke, isolated browser supervisor. Closure evidence is recorded in progress.md and FINAL_HANDOFF.md.

### M8-01
Files: README.md, docs. Tasks: implement the behavior above, prove it with schema/docs review, and update docs/FINAL_HANDOFF.md. Security impact: truthful claims. Acceptance: Reproducible commands, ADRs, threat boundaries and exact limitations. Closure evidence is recorded in progress.md and FINAL_HANDOFF.md.

### M8-02
Files: examples, docs/demo. Tasks: implement the behavior above, prove it with independent client and readback, and update docs/MCP_PROTOCOL.md. Security impact: synthetic public examples. Acceptance: Runnable client, actual synthetic files/screenshots and protocol evidence. Closure evidence is recorded in progress.md and FINAL_HANDOFF.md.

### M8-03
Files: docs/progress.md, FINAL_HANDOFF.md. Tasks: implement the behavior above, prove it with full verification, and update docs/FINAL_HANDOFF.md. Security impact: release claims. Acceptance: Actual check exits/counts, remaining NOT_RUN checks and clean launch instructions. Closure evidence is recorded in progress.md and FINAL_HANDOFF.md.

