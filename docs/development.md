# Development

Run commands from the repository root. Backend dependencies use the root `uv.lock`; frontend dependencies use the root `pnpm-lock.yaml` and pinned pnpm. `make setup` bootstraps missing tools locally. No global pnpm installation is required.

## Daily commands

| Command | Purpose |
|---|---|
| `make dev` | Run the real configured app |
| `make lint format-check typecheck` | Static checks |
| `make schema-check architecture-check` | API/policy drift, module boundaries, documentation links |
| `make test` | Backend coverage and frontend unit/integration tests |
| `make test-e2e` | Disposable mock backend and real Chromium workflows |
| `make security` | Dependency audits, security tests, Bandit, secret patterns |
| `make build` | All Python packages and frontend production bundle |
| `make ci` | Complete local verification gate |

Browser tests allocate temporary ports and storage; the live app can remain running. Install Chromium with `pnpm --filter @mcp-workspace/web exec playwright install --with-deps chromium`. On this WSL host, the pre-existing extracted libraries are available under `.local/browser-libs/extracted/usr/lib/x86_64-linux-gnu`; add that directory to `LD_LIBRARY_PATH` if needed.

## Rules that matter

- Preserve per-user ownership, real MCP calls, provider-bound model consent, and exact-action Google approvals.
- Treat source content and tool results as data, never trusted instructions.
- Use one handwritten class per Python file and one React component per component file. Keep modules under 400 lines.
- Keep synthetic account/model providers in explicit mock configurations. Tests must not accidentally contact Google or a real model.
- Add meaningful regression coverage for behavior changes. Do not replace test assertions with historical success reports.
- Keep credentials, live storage, private browser state, and unredacted recordings out of Git.

Use `uv add --package <package> <dependency>` for Python dependencies and the pinned pnpm workspace filter for frontend changes. Optional pre-commit hooks use the same locked tools as CI.

## API and policies

Pydantic models are the REST contract source. After an intentional API change, export OpenAPI using an isolated mock configuration and regenerate the shared TypeScript definitions:

```sh
MODE=mock LLM_PROVIDER=fake WORKSPACE_DATA_DIR=/tmp/workspace-schema uv run workspace-ai export-schema
pnpm --filter @mcp-workspace/shared-types generate
make schema-check
```

Tool policies are generated from the typed registry using `uv run python scripts/export_tool_policies.py`. Runtime validation remains authoritative; model-facing schemas and context projections do not change server permission checks.

## Synthetic evaluations

Run a separate mock API with temporary storage and its own port. `workspace-ai eval --url <mock-api-url> --suite all` runs the packaged cases. Suites `tools`, `workflows`, `artifacts`, and `security` select the same authoritative datasets. Reports go to `.local/verification/evaluations` by default. `workspace-ai smoke --url <mock-api-url>` exercises synthetic cross-service files and downloads. Both are distinct from real-account acceptance.

Northstar data is retained only for deterministic fixtures. The packaged datasets and tests remain the source of truth; generated reports do not belong in source control.

## Packaging and evidence

Keep installed-wheel and container checks when changing package resources or deployment files. `scripts/verify_installed_wheels.py --help` verifies fresh noneditable installs; `scripts/verify_containers.py --help` checks isolated test containers. These checks exercise behavior that source imports cannot prove.

Fresh screenshots, reports, and browser captures belong under `.local/verification` or `.local/e2e-captures`. Maintain one sanitized product preview. The UI uses local Inter Variable for interface text and JetBrains Mono for technical output, with shared typography tokens from 12 to 32px.

See [setup](setup.md), [architecture](architecture.md), and [the live demo](../README.md#live-demo).
