# Core release handoff

The M0–M8 core implementation is available in this local working tree. It uses one uv-managed Python package, one React application, five official-SDK MCP endpoints, synthetic offline workflows, Google identity/connector adapters, exact-action approvals, and seven validated artifact formats. No commit, remote issue, PR, publication or deployment was performed.

## Start the application

Prerequisites: uv, Node 24/npm and make. Python 3.12 is selected by the project.

```sh
cp .env.example .env
make setup
make dev
```

Open **http://localhost:5173** and choose **Explore demo**. The [walkthrough](demo/SCENARIOS.md) covers sources, report generation and approvals. The demo is synthetic and has a frozen November 5, 2026 clock. Stop a dev API before `make test-e2e` or `make ci`, which reserve the browser-test port.

From another terminal, `make smoke` verifies a running mock API and generates four files; `make eval` runs 52 isolated synthetic cases. The [operations guide](OPERATIONS.md) covers containers, backup/restore, key rotation, retention and deletion. All backend dependency changes must use uv; frontend changes must preserve the npm lockfile.

## Verification record

The machine-readable [verification record](demo/verification.json) contains the final executed check results and environment. [Acceptance mapping](ACCEPTANCE_MATRIX.md) connects requirements to local issues and tests. [Progress](progress.md) records closure evidence for each consolidated issue.

| Final local gate | Result |
|---|---|
| `make ci` | Exit 0: lint, formatting, type checks, generated API drift, tests, audits and builds |
| Backend | 213 passed; 86.38% statement coverage; one Authlib deprecation warning |
| Frontend unit tests | 12 passed |
| Chromium | 10 passed: 7 controlled UI-fixture cases and 3 actual-backend flows |
| Dependency advisories | Python: no known vulnerabilities; npm: zero known vulnerabilities |
| Security target | Bandit/source scan passed; 17 security tests reran as a subset of the 213 |
| Evaluation | 52/52 stated FakeLLM pipeline assertions passed |
| Container / Compose | Health, 31-tool discovery, four files and frontend smoke passed |

Complete [final CI output](demo/ci-output.txt) is retained. A recovery regression exposed an SDK exception group that obscured the typed schema-change denial; the local policy check now runs after the transport closes, and focused plus complete checks passed afterward.

Protocol evidence includes official-client TCP calls for all 31 tools, a subprocess stdio client, five servers' resource/prompt access, malformed/authentication/Origin negatives, schema changes, timeouts and unavailable-server handling. Inspector 2.5.0 passed ten separately executed HTTP/stdio commands. Compatibility is limited to the [observed matrix](mcp/COMPATIBILITY_MATRIX.md), including protocol 2026-07-28 with SDK 2.3.0.

The [52-case report](EVALUATION.md) passed all stated pipeline assertions. Its latency and citation-integrity metrics describe FakeLLM, not real-model reasoning. The [Docker proof](demo/container-proof.json) records no-network execution under an 8 GiB limit, four real generated files, built frontend delivery, and measured cgroup memory. [Compose proof](demo/compose-proof.json) records health, smoke and cleanup of a uniquely named local test project.

The [four generated files](../examples/generated/) were downloaded through the API and reopened by format readers; the [manifest](../examples/generated/manifest.json) records checksums, structure and sources. The [Northstar trace](../examples/expected_traces/northstar.json) is an actual mock run. [Screenshots](demo/screenshots/) are actual application captures; [browser QA evidence](../web/qa/evidence.json) distinguishes controlled UI fixtures from real-backend flows.

## Remaining external checks

| Check | Execution status | Required setup |
|---|---|---|
| Google sign-in and connector reads against a real account | NOT_RUN | Google project, OAuth client and controlled test account |
| Real send, invitation, upload or remote modification | NOT_RUN | Controlled targets and explicit execution authorization |
| Existing Drive file selection through Open-with | NOT_RUN | Full domain, Drive UI configuration and drive.install consent |
| Real-model reasoning, claim accuracy, latency and cost | NOT_RUN | Configured compatible provider/model/key and separate per-user content consent |
| Native Office/PDF application visual review | NOT_RUN | Suitable installed viewers; structural readback already executed |
| Remote GitHub Actions | NOT_RUN | Authorized repository publication and workflow run |
| Public deployment/Google verification | Out of local core scope | Separate authorization and applicable verification/assessment |

Mock CI makes no Google or model-provider calls. Live adapter/identity/provider contracts use injected HTTP fixtures; those tests cannot establish real-account acceptance. [OAuth setup](OAUTH_SETUP.md) gives the operator procedure without storing credentials in source.

## Known limits and implementation adjustments

One backend process is supported. SQLite, bounded in-process work and local artifacts avoid extra services; multiple API workers need shared scheduling/locking work. MCP assertions are private host credentials, not a public OAuth service for arbitrary clients. Hosted/third-party MCP registration, indexing, extended attachments, advanced native Google editing and richer previews remain deferred as approved.

Pending approvals are exact-action and expire. Interrupted active runs are explicit after restart; dispatched writes become outcome_unknown and are never automatically retried. Cancellation/deletion cannot recall a request already accepted by Google. Deletion fences local work and removes app-owned state; it does not delete Google resources.

FakeLLM is deliberately curated. Artifact generation validates semantic structure but does not prove layout fidelity in every Office viewer. Source-reference checks do not grade every natural-language claim. Dependency advisory results are point-in-time; Authlib's JOSE import emits a deprecation warning and is constrained below 2 pending migration to its replacement API.

This WSL environment needed Chromium runtime libraries and a temporary Docker plugin-directory override. The repository did not change global host configuration. CI installs Chromium dependencies explicitly; local workarounds are described in [web/README.md](../web/README.md) and [operations](OPERATIONS.md).

The [ADRs](ADRs/) record SDK v2 request wrappers, compact layout, identity/vault design, exact approvals, narrow Drive access, artifact fidelity, orchestration, evaluation arithmetic and browser/deployment choices. The original guides are preserved, including their duplicated combined specification.

## Review assessment

Local behavior is supported by executed protocol, artifact, security, recovery and browser checks. External integration acceptance and native visual review are explicitly unresolved. This is a usable, tested core prototype; it is not a certification of public production readiness. No remaining local core issue is closed merely because its files exist: closure points to the final verification record.
