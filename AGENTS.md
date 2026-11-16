# MCP Workspace AI

Read the authoritative numbered guides in `docs/specifications` before changing behavior. The approved organization plan is `docs/development/reorganization-plan.md`; layout changes supersede the earlier compact-package choice through ADR 0010.

- Use uv for every Python member and preserve one root uv.lock. Use pinned pnpm and one root pnpm-lock.yaml for frontend dependencies.
- Define at most one handwritten class per file, including schemas, exceptions, protocols and test helpers. Keep one React component per component file.
- Keep provider adapters behind real official-SDK MCP calls. Preserve all canonical names, scopes, payloads, public API URLs and CLI subcommands.
- Maintain one typed schema/risk registry. API may import servers/common; servers import common; common imports neither API nor servers. Shared types do not import web code.
- Keep one application-scoped owner of tasks, adapters, write/refresh locks, render limits, schema digests and deletion fences.
- Enforce ownership, scopes and exact-action approvals at the receiving MCP boundary. Keep approval consumption and durable operation creation transactional.
- Mock execution must never call Google or a model provider. Keep tokens and raw source bodies out of prompts where unauthorized, traces, logs and published evidence.
- Preserve database revisions, private storage paths and existing encrypted data. Never reset private data to make a migration pass.
- Run focused checks and required combined gates before closing an issue; record actual exits, identities and remaining limitations.
- Never perform live sends, invitations, sharing, remote deletion, publication or deployment without explicit authorization.
- Preserve original specifications and historical evidence byte-for-byte. Label baseline evidence separately; live/domain/model/native-layout checks remain NOT_RUN until exercised.
