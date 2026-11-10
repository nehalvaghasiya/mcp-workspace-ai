# MCP Workspace AI

A workspace assistant for Gmail, Calendar and Drive, with real MCP traffic, inspectable approvals and validated Office/PDF generation. Default mock mode uses synthetic data and FakeLLM without accounts, paid services or a GPU.

## Run locally

Requires uv, Node 24/npm and GNU make. Python 3.12 is selected by `.python-version`. Setup bootstraps **pnpm 12.18.0** locally when missing.

```sh
cp .env.example .env
make setup
make dev
```

Open **http://localhost:5173**, choose **Explore demo**, and try:

> Review Northstar launch emails, calendar meetings and Drive proposal; create PDF Word Excel PowerPoint reports.

In another terminal, `make smoke` verifies the running stack and four downloads. The demo clock is November 5, 2026 in America/Chicago. FakeLLM tests curated pipeline behavior, not general model reasoning.

## What is implemented

- Five authenticated official-SDK MCP endpoints, actual HTTP host/client calls, stdio entrypoints, tools, resources and prompts.
- Gmail/Calendar/Drive reads and eight Google writes requiring server-enforced exact-action approval.
- DOCX, PDF, XLSX, PPTX, CSV, Markdown and sanitized HTML, with structural/semantic readback, provenance and owner-only downloads.
- Persistent conversations, SSE activity, source cards, approval review, connectors, settings, artifact library and MCP Explorer.
- Google OIDC/incremental OAuth, encrypted credentials and live adapter contracts; model-content sharing has separate provider-bound consent.
- Isolated fixtures, recovery/security tests, accessible browser workflows and measured evaluation tooling.

![Verified synthetic workspace](demo/screenshots/reorganization/workspace-desktop.png)

## Repository organization

| Location | Responsibility |
|---|---|
| `apps/api` | API, agents/LLM, authentication, persistence, services and operations |
| `apps/web` | React application, feature hooks/components and browser tests |
| `mcp-servers` | Gmail, Calendar, Drive, Documents (`artifact`) and Demo |
| `packages` | Shared Python contracts/utilities and generated frontend types |
| `evaluations`, `tests` | Packaged evaluation data/runner and cross-package verification |
| `infra`, `scripts`, `config` | Local builds, entrypoints and documented/generated configuration |
| `docs`, `examples`, `demo` | Guides, validated examples, walkthrough and actual evidence |

Eight Python packages share **one root uv.lock**. Frontend packages share **one pnpm-lock.yaml**. The default runtime remains one backend process with real network calls between host and mounted MCP endpoints. One handwritten class per file and package dependency directions are checked automatically.

## Documentation and checks

Run `make lint`, `make format-check`, `make typecheck`, `make schema-check`, `make test`, `make security`, `make build`, and `make ci`. Browser tests reserve port 8000; stop an existing dev API first. `make eval` measures 52 preserved synthetic cases against a running mock API.

- [Documentation index](docs/README.md), [architecture](docs/architecture/system-overview.md), [organization plan](docs/development/reorganization-plan.md)
- [Local setup](docs/development/local-setup.md), [testing](docs/development/testing-guide.md), [operations](docs/deployment/operations.md)
- [MCP integration](docs/mcp/client-integration.md), [tool catalog](docs/mcp/tool-catalog.md), [Inspector](docs/mcp/inspector-guide.md)
- [Google setup](docs/security/oauth-setup.md), [approval policy](docs/security/approval-policies.md), [privacy](docs/security/data-privacy.md)
- [Walkthrough](demo/walkthrough.md), [example files](examples/document-generation/generated/), [evaluation method](docs/evaluations/evaluation-guide.md)
- [Verification progress](docs/verification/progress.md), [acceptance matrix](docs/verification/acceptance-matrix.md), [issue board](docs/development/project-board.json)

The reorganized implementation passes 221 backend tests, 12 frontend tests, 10 browser workflows and all 52 deterministic evaluation cases. Coverage across all eight production packages is **89.30%**. Clean wheel installation, HTTP/stdio clients, Inspector, Docker and Compose checks also pass. See the [final handoff and evidence](docs/verification/final-handoff.md) for exact scope, identities and remaining external checks.

Live Google, real-model quality and native Office visual checks remain separately recorded and unrun unless explicitly exercised. Drive uses narrow `drive.file`; existing-file Open-with requires domain setup. Hosted MCP onboarding, advanced native editing, indexing, extended attachments and optional infrastructure remain deferred. Public publishing/deployment and real external writes require their own authorization.

MIT licensed. Bundled DejaVu notices are packaged with the document fonts under `mcp-servers/documents/src/mcp_documents/assets/fonts`.
