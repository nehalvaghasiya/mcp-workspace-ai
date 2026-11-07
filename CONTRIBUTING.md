# Contributing

Run `make setup`, then `make dev`. Python dependencies use uv and the root `uv.lock`; frontend dependencies use the pinned pnpm workspace and root lockfile. `make setup` bootstraps missing pnpm locally. For manual pnpm commands, use an existing exact-version executable or the path printed by `uv run python scripts/bootstrap_pnpm.py`.

Make focused changes with acceptance criteria, relevant tests and documentation. Preserve the real MCP transport boundary, per-user ownership and exact-action approvals. Treat retrieved content as untrusted data. Mock tests must never call Google or a model provider.

Define at most one handwritten class per file, including schemas, exceptions and test helpers. Keep one React component per component file. Split modules by responsibility, target fewer than 300 lines, and document any justified exception above 400 lines. Generated contracts, data and unchanged migration revisions have separate size rules.

Use `uv add --package <workspace-package> <dependency>` for backend changes. Update frontend dependencies with the pinned pnpm and the appropriate workspace filter. Keep generated contracts derived from their authoritative models, not handwritten copies.

Before review, run `make lint format-check typecheck schema-check test`. Use `make test-e2e`, `make security`, and the isolated mock evaluation when affected; `make ci` is the complete local gate. Stop a dev API before browser tests reserve port 8000. Record actual results and distinguish fixture tests from real-account checks.

Optional local hooks are defined in `.pre-commit-config.yaml`; they invoke locked project tools. Run the hook runner through uv, for example `uvx pre-commit run --all-files`. Installing hooks is a local choice; CI performs the required checks independently.

Do not publish, deploy, send real email, invite attendees or modify Google resources without explicit authorization. Keep credentials and private `.local` data out of changes and screenshots. See [security policy](SECURITY.md) for private reporting and [development guides](docs/development/) for setup/testing details.
