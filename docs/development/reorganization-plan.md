# Approved repository organization plan

The user approved a behavior-preserving migration to the requested monorepo tree. Keep uv for all Python members, adopt pinned pnpm workspaces and retain the single-process runtime with five real MCP endpoints. Define at most one handwritten class per file and one React component per component file; split large modules by responsibility.

## Ownership and contracts

API owns routes, agents/LLM, authentication, persistence, services and operations. Connector packages own their schemas, tool definitions and providers. Documents owns IR/generators/validators/fonts; its public namespace stays artifact. Demo and the installed evaluation runner package existing behavior. Common owns reused contracts/security/parsing primitives; generated frontend contracts have one shared owner.

Dependency direction is API → servers/common/evaluations, servers/evaluations → common, and web → shared types. No reverse API/server imports or cross-connector imports are allowed. One execution context retains task/adapter registries, locks, render bounds, schema digests and deletion fences. Approval consumption, executable-run validation and operation creation stay atomic inside the MCP execution boundary.

Preserve /api routes, OAuth callbacks, SSE shapes, hash navigation, all 31 canonical tools/scopes/digests/request envelopes, CLI subcommands, migration revisions, encrypted credentials and private storage. Installed resources must not rely on checkout parent paths. Deferred features receive roadmap notes without fake tools or services.

## Stages

1. Record source/contract/test/case/database baselines, move inventory and rollback checkpoint, excluding private runtime data.
2. Establish eight-member uv and frontend pnpm workspaces, root locks and shared contracts/types.
3. Split backend routes/services/models/agents/providers/generators while retaining shared state and transport authorization.
4. Split frontend composition, features, hooks, services and components without behavior/visual changes.
5. Organize tests, datasets, resources, examples, docs, CI, development and container support.
6. Remove temporary/obsolete authorities after fresh installation, complete wheels, existing database, full tests/evaluation/protocol/container verification.

Keep one default API/static-web container. Component Dockerfiles are diagnostic entrypoints on a shared base. Manual release builds artifacts only; it does not publish/deploy. Environment variables remain runtime authority; generated policy/config examples do not replace the registry.

## Acceptance

Maintain old-to-new identities for the 213 baseline backend tests, 12 frontend tests, 10 browser cases and 52 evaluation cases. Compare raw schemas/policy digests and OpenAPI, not only normalized semantics. Enforce class/import/size rules and measure coverage across all production members, targeting at least the existing rounded 86%.

Install all wheels in a fresh environment outside the checkout without editable imports/PYTHONPATH assistance. Check packaged migrations, model registrations, fixtures, fonts/templates/licenses and existing encrypted state. Exercise actual HTTP/stdio, Inspector, approvals/races/replay, cancellation/deletion/restart, browser accessibility/downloads, all 52 cases and no-network/Compose smoke.

Preserve original specifications and raw historical evidence byte-for-byte. Record new results separately and close [issues](issue-backlog.md) only on actual gates. Real Google/model/native-layout/domain/public-deployment checks remain separate external prerequisites.
