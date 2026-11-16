# Requirements and verification matrix

The numbered guides remain authoritative. The approved core scope is recorded in [IMPLEMENTATION_PLAN.md](historical/core-implementation-plan.md); compact implementations and integration adjustments are recorded in [ADRs](../adr/). The local issues below consolidate the guide's seed issues without dropping their core behaviors. The linked core handoff is historical baseline evidence. Current migration status is in [progress](progress.md); the [approved organization plan](../development/reorganization-plan.md) and [new issues](../development/issue-backlog.md) preserve these requirements through the move.

| Requirement | Local issues | Implementation | Verification |
|---|---|---|---|
| FR-01 bounded agent, streaming, persisted context | M6-01 | API agents/routes and owned run/event rows | API, model, workflow and recovery tests; browser reload/SSE |
| FR-02 Gmail reads/writes | M2-01, M4-02, M5-02 | Mock/live adapters behind Gmail MCP | MIME/query/pagination/method tests; all writes over MCP |
| FR-03 Calendar and free/busy | M2-02, M4-02, M5-02 | Explicit timezone, recurrence, DST, conditional revisions | Connector/workflow tests; create/update/cancel approvals |
| FR-04 narrow Drive and bounded extraction | M2-03, M4-02, M5-02 | `drive.file`, exports, resource keys, folder/upload | Connector/extraction tests; disabled connector and owner checks |
| FR-05 seven artifact formats | M3-01, M3-02 | Typed report/sheet/slide IR, templates, validators, atomic files | Artifact tests reopen files and inspect text/tables/numeric/formula/slide/page structure |
| FR-06 actual MCP boundary | M1-01, M1-02, M8-02 | Five SDK servers, actual HTTP client, stdio CLI | 31 tools exercised, malformed inputs, independent client, Inspector |
| FR-07 Google identity, authorization, approvals | M0-02, M4-01, M5-01, M7-01 | OIDC/OAuth, encrypted vault, exact one-use action capability | Signed claims/HTTP stubs, race/replay/expiry/changed-content tests |
| FR-08 provenance | M2-01..03, M3-02, M6-01 | Common SourceRef, source cards, artifact metadata, private trace | Cross-app API/browser tests; evaluation reference-integrity assertions |
| FR-09 responsive accessible UI | M6-02 | React strict TS, generated API types, history/artifacts/approval/Explorer | Vitest, desktop/mobile Playwright, scoped axe/keyboard checks and actual captures |
| FR-10 local operations | M0-01, M7-03, M8-01 | uv/pnpm locks, Make targets, containers, backup/restore/rotation | Full CI, Docker/Compose smoke, vault lifecycle tests |
| No cloud dependency in mock execution | M0-03, M7-02, M7-03 | Frozen fixtures, FakeLLM, separate mode storage | No-network container smoke; injected live transports in contracts |
| Cancellation, reconnection, restart | M6-01, M7-01 | SSE cursors, cancellation/fencing, interrupted/unknown states | API/recovery/security tests; no effect replay |
| Schema changes and unavailable/slow server | M1-02, M7-01 | Pinned discovery digest, bounded reads/tool deadlines | Recovery tests use actual MCP traffic and transport faults |
| Scope and identity isolation | M0-02, M5-01 | Owner predicates, active subject/session, returned-scope validation | Cross-user, scope narrowing, logged-out callback and refresh-fence tests |
| Parser/filesystem/model attack boundaries | M3-01, M7-01 | Bounded extraction/rendering, safe formulas, source-data separation | ZIP/XML/PDF/macro, traversal, injection, canary and consent tests |
| Retention and deletion | M0-02, M3-02, M7-01 | Hourly inactive-data cleanup; delete/cancel/fence | Workflow/security tests including in-flight renderer |
| Measured evaluation and honest showcase | M7-02, M8-02, M8-03 | 52 explicit JSONL cases, reports, actual files/screenshots | Saved execution reports; FakeLLM results labeled separately |

W01–W14 are mapped in [demo/SCENARIOS.md](../../demo/walkthrough.md). The deterministic evaluation's category counts are 10 + 8 + 8 + 8 + 8 + 5 + 5 = **52**; the guide's stated 58 is corrected by ADR 0008. Security regressions are additional to those 52 cases and include more than twelve adversarial boundaries.

## External acceptance

| Check | Status | Prerequisite |
|---|---|---|
| Real-account OIDC/incremental connector consent and reads | NOT_RUN | Operator Google project, configured client, controlled test account |
| Actual approved send/invitation/remote changes | NOT_RUN | Dedicated resources/recipients and explicit execution authorization |
| Existing-file Drive Open-with | NOT_RUN | Full domain, Drive UI configuration and drive.install consent |
| Real-model task/claim accuracy and costs | NOT_RUN | Configured provider/model/key and per-user content-sharing consent |
| Native Office/PDF visual layout review | NOT_RUN | Installed viewer/Office or controlled review environment |
| Remote GitHub Actions | NOT_RUN | Authorized repository publication and workflow execution |
| Public deployment/Google verification | Out of local release scope | Separate authorization and applicable verification/security assessment |

These prerequisites do not block mock behavior or HTTP-stub adapter tests. Local checks establish the prototype's executed behavior; they do not establish public production readiness.
