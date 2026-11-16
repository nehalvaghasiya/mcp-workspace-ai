# Reorganization issue backlog

The 22 completed core issues remain unchanged in [historical backlog](../verification/historical/core-issue-backlog.md), [board](../verification/historical/core-project-board.json) and [closure evidence](../verification/historical/core-progress.md). The six cards below track the approved source migration, not new product scope. All six cards are closed against the executed [final verification record](../verification/reorganization/final.json) and [handoff](../verification/final-handoff.md). External acceptance retains its separate NOT_RUN status.

| ID | Work / owner | Dependencies | Complexity | State |
|---|---|---|---|---|
| R01 | Capture source, contracts, cases and database baseline (root) | — | M | done |
| R02 | Establish uv/pnpm workspace boundaries (root / web) | R01 | M | done |
| R03 | Split API, connector and document responsibilities (root / connectors / documents) | R02 | L | done |
| R04 | Organize frontend features and components (web) | R02 | M | done |
| R05 | Relocate tests, guides, examples and support material (root / documentation) | R02 | M | done |
| R06 | Verify packaged installation and final cutover (root) | R03, R04, R05 | L | done |

## R01: Capture source, contracts, cases and database baseline

Acceptance: Checkpoint excludes runtime data/secrets; raw schemas, digests, table metadata, fixture hashes and test/case identities are retained.

Current evidence: 149 source/config/resource files mapped; source-only rollback archive and original baseline hashes verified. All 213 backend identities and 52 case definitions preserved.

Security/rollback: preserve owned state and exact contracts; restore the relevant source moves from the checkpoint if a gate fails. Never reset private data or replay provider writes to roll back a code-layout change. Update current guides and identity/move manifests before closure.

## R02: Establish uv/pnpm workspace boundaries

Acceptance: Eight installable Python members, one uv lock, pinned pnpm 12.18.0 workspace and one frontend lock; generated types have one owner.

Current evidence: Locked make setup passed; eight noneditable member wheels passed fresh foreign-directory installation; pnpm 12.18.0 frozen lock and security override verified.

Security/rollback: preserve owned state and exact contracts; restore the relevant source moves from the checkpoint if a gate fails. Never reset private data or replay provider writes to roll back a code-layout change. Update current guides and identity/move manifests before closure.

## R03: Split API, connector and document responsibilities

Acceptance: One class per file, dependency DAG, one shared execution context and atomic approval/operation semantics; contracts and data remain compatible.

Current evidence: 221 backend cases passed; 89.30% coverage across every production member; class/import/size guards pass; all 31 raw MCP contracts/digests, OpenAPI and SQL metadata match; existing owned/encrypted state passes.

Security/rollback: preserve owned state and exact contracts; restore the relevant source moves from the checkpoint if a gate fails. Never reset private data or replay provider writes to roll back a code-layout change. Update current guides and identity/move manifests before closure.

## R04: Organize frontend features and components

Acceptance: One component per file; generated sharedtypes; unchanged routes, session/CSRF/SSE, idempotency and accessible browser behavior.

Current evidence: 12 frontend and 10 Chromium cases passed; 22 identities retained; actual backend download/history/approvals, mobile layouts and scoped accessibility checks pass.

Security/rollback: preserve owned state and exact contracts; restore the relevant source moves from the checkpoint if a gate fails. Never reset private data or replay provider writes to roll back a code-layout change. Update current guides and identity/move manifests before closure.

## R05: Relocate tests, guides, examples and support material

Acceptance: Identity-preserving test/case moves; originalguides/evidence retain bytes; currentlinks/resources/supportconfig validate.

Current evidence: 41 retained hashes verified; original guides/historical records preserved; tests/cases mapped; workflow/configuration checks passed; current documentation and evidence organized.

Security/rollback: preserve owned state and exact contracts; restore the relevant source moves from the checkpoint if a gate fails. Never reset private data or replay provider writes to roll back a code-layout change. Update current guides and identity/move manifests before closure.

## R06: Verify packaged installation and final cutover

Acceptance: Completewheelset outside checkout; existing DB; full CI, actual HTTP/stdio/Inspector,52 cases, no-networkimage andCompose; obsoleteauthorities removed.

Current evidence: Complete CI passed; final static and all-package coverage reruns passed; 52/52 evaluation; HTTP/stdio clients 10/10; Inspector 10/10; no-network Docker and Compose smoke/cleanup passed. External acceptance remains NOT_RUN.

Security/rollback: preserve owned state and exact contracts; restore the relevant source moves from the checkpoint if a gate fails. Never reset private data or replay provider writes to roll back a code-layout change. Update current guides and identity/move manifests before closure.

The [machine-readable board](project-board.json), [approved plan](reorganization-plan.md) and [verification progress](../verification/progress.md) share this scope. Code/dependency gates and external acceptance are reported separately.
