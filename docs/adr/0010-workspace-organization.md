# Workspace organization, pnpm and class ownership

Status: accepted through the user's Repository Organization and Modularization Plan.

This decision supersedes ADR 0001's one-distributable-package layout and the earlier npm frontend choice. It preserves the single-process runtime and security/data contracts.

Use a non-distributable root uv project with eight installable members: API, Gmail, Calendar, Drive, Documents, Demo, common and evaluations. All share one uv.lock. API imports server/common/evaluation packages; servers import common; common imports neither applications nor servers. Web consumes generated shared types.

Pin pnpm 12.18.0 and Node 24, using one root workspace/lockfile. Bootstrap missing pnpm locally. Translate the existing minimatch security override rather than dropping it during import. npm is only a bootstrap mechanism, not a parallel dependency authority.

Define at most one handwritten class per file, including nested test helpers. Keep one React component per component file. Split responsibilities without empty classes or duplicated schemas. Generated data/contracts and unchanged migration revisions have explicit size exceptions.

The API injects trusted capabilities into handlers; one execution context retains task/adapter registries, locks, render limits, schema digests and deletion fences. Exact approval consumption and operation creation stay atomic. Provider operations still cross actual MCP transport.

Preserve /api URLs, canonical tool names/request envelopes, CLI subcommands, database revisions, encrypted credentials and private storage. Documents retains the public name artifact. Demo and the installed evaluation runner are additional packages for existing behavior, not new product scope.

Preserve original guides and raw historical evidence. Migration acceptance compares test/case identities, raw schemas/digests, installed resources and existing database behavior. Optional remote MCP, Drive move/share, conversion, Terraform and monitoring remain deferred.

Evaluation JSONL files have one authoritative copy inside the installable evaluation package; `evaluations/datasets` links there for repository access. Explicit source-distribution selection preserves these resources when rebuilding wheels from source, as well as when building wheels directly. Both paths must pass the foreign-directory installation probe.
