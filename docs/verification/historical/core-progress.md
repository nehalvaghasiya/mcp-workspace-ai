# Implementation progress and issue closure

All 22 consolidated local core issues are **done** after focused checks, implementation review, documentation and the final combined gate. No remote issue tracker or commit was created. Each entry below refers to the **same final combined execution**, not 22 independent CI runs. The original guide seed issues are consolidated by capability in [ISSUE_BACKLOG.md](ISSUE_BACKLOG.md); [ACCEPTANCE_MATRIX.md](ACCEPTANCE_MATRIX.md) preserves requirement coverage.

## Final milestone gate

- `LD_LIBRARY_PATH=/tmp/workspace-browser-libs/extracted/usr/lib/x86_64-linux-gnu make ci`: exit 0; 213 backend tests, 86.38% statement coverage, 12 frontend unit tests and 10 browser tests (7 UI fixtures, 3 actual-backend flows). Security target reran 17 of those backend tests.
- Lint, format, Python/TypeScript types, generated API drift, backend/frontend builds, Bandit and source secret-pattern scan passed. Python/npm audits reported no known vulnerabilities.
- Real MCP protocol tests exercised HTTP/stdio, five HTTP namespaces and all 31 tools. Independent Inspector passed 10/10 commands.
- `workspace-ai eval`: exit 0, 52/52 FakeLLM pipeline cases. See the raw evaluation report for denominators and latency; this is not a real-model accuracy score.
- Final Docker and Compose smoke: exit 0; 31 tools, four files, 18 trace events, frontend served. Final Docker run had external networking disabled.
- New recovery tests caught SDK exception wrapping around schema-change denial. Policy evaluation was moved outside the transport context; 33 focused recovery/protocol tests then passed, followed by the complete 213-test gate. No approval bypass or provider effect occurred.

Actual environment, source fingerprint and check records are in [demo/verification.json](demo/verification.json); complete final CI output is in [demo/ci-output.txt](demo/ci-output.txt). External Google, real-model, domain-dependent selection, native Office layout and remote CI checks remain NOT_RUN. Container/browser host adjustments are documented in OPERATIONS.md and web/README.md.

## M0-01

Locked package, setup and app factory. Documentation: [docs/OPERATIONS.md](OPERATIONS.md), tests/evidence: test_api.py.

```yaml
issue: M0-01
status: done
commit: uncommitted local working tree
changed_files: ["pyproject.toml", "Makefile", "src/workspace_ai/api.py"]
checks:
  - command: make ci
    environment: LD_LIBRARY_PATH supplied for this host's Chromium libraries
    exit_code: 0
    backend_tests_passed: 213
    frontend_unit_tests_passed: 12
    browser_tests_passed: 10
mcp_protocol_test: actual HTTP/stdio protocol suite in the successful combined gate
security_review: "Validated configuration and typed API boundaries; mock mode rejects external model providers."
known_limitations: []
updated_at: 2026-11-06T19:43:14.667731+00:00
```

## M0-02

Owned persistence, migrations and sessions. Documentation: [docs/SECURITY.md](SECURITY.md), tests/evidence: test_api.py, test_security.py, test_vault.py.

```yaml
issue: M0-02
status: done
commit: uncommitted local working tree
changed_files: ["src/workspace_ai/db.py", "src/workspace_ai/migrations", "src/workspace_ai/api.py"]
checks:
  - command: make ci
    environment: LD_LIBRARY_PATH supplied for this host's Chromium libraries
    exit_code: 0
    backend_tests_passed: 213
    frontend_unit_tests_passed: 12
    browser_tests_passed: 10
mcp_protocol_test: actual HTTP/stdio protocol suite in the successful combined gate
security_review: "Owner predicates, hashed sessions, CSRF, active identity and deletion fences verified."
known_limitations: []
updated_at: 2026-11-06T19:43:14.667731+00:00
```

## M0-03

Frozen synthetic fixture manifest. Documentation: [docs/USER_GUIDE.md](USER_GUIDE.md), tests/evidence: test_connectors.py.

```yaml
issue: M0-03
status: done
commit: uncommitted local working tree
changed_files: ["src/workspace_ai/connectors.py", "tests/fixtures/synthetic"]
checks:
  - command: make ci
    environment: LD_LIBRARY_PATH supplied for this host's Chromium libraries
    exit_code: 0
    backend_tests_passed: 213
    frontend_unit_tests_passed: 12
    browser_tests_passed: 10
mcp_protocol_test: actual HTTP/stdio protocol suite in the successful combined gate
security_review: "Frozen synthetic state is isolated per user and separate from live storage."
known_limitations: []
updated_at: 2026-11-06T19:43:14.667731+00:00
```

## M1-01

Real HTTP and stdio MCP servers. Documentation: [docs/MCP_PROTOCOL.md](MCP_PROTOCOL.md), tests/evidence: test_protocol.py.

```yaml
issue: M1-01
status: done
commit: uncommitted local working tree
changed_files: ["src/workspace_ai/mcp_servers.py", "src/workspace_ai/runtime.py"]
checks:
  - command: make ci
    environment: LD_LIBRARY_PATH supplied for this host's Chromium libraries
    exit_code: 0
    backend_tests_passed: 213
    frontend_unit_tests_passed: 12
    browser_tests_passed: 10
mcp_protocol_test: actual HTTP/stdio protocol suite in the successful combined gate
security_review: "Real HTTP authentication/Origin negatives and stdio assertions tested."
known_limitations: []
updated_at: 2026-11-06T19:43:14.667731+00:00
```

## M1-02

Discovery, resources, prompts and schema registry. Documentation: [docs/mcp/TOOL_CATALOG.md](mcp/TOOL_CATALOG.md), tests/evidence: test_protocol.py.

```yaml
issue: M1-02
status: done
commit: uncommitted local working tree
changed_files: ["src/workspace_ai/contracts.py", "src/workspace_ai/runtime.py"]
checks:
  - command: make ci
    environment: LD_LIBRARY_PATH supplied for this host's Chromium libraries
    exit_code: 0
    backend_tests_passed: 213
    frontend_unit_tests_passed: 12
    browser_tests_passed: 10
mcp_protocol_test: actual HTTP/stdio protocol suite in the successful combined gate
security_review: "All registered schemas validated; schema-change rejection is typed and blocks execution."
known_limitations: []
updated_at: 2026-11-06T19:43:14.667731+00:00
```

## M2-01

Gmail reads and MIME handling. Documentation: [docs/USER_GUIDE.md](USER_GUIDE.md), tests/evidence: test_connectors.py, test_protocol.py.

```yaml
issue: M2-01
status: done
commit: uncommitted local working tree
changed_files: ["src/workspace_ai/connectors.py"]
checks:
  - command: make ci
    environment: LD_LIBRARY_PATH supplied for this host's Chromium libraries
    exit_code: 0
    backend_tests_passed: 213
    frontend_unit_tests_passed: 12
    browser_tests_passed: 10
mcp_protocol_test: actual HTTP/stdio protocol suite in the successful combined gate
security_review: "MIME and bounded decoding; raw bodies excluded from tool traces."
known_limitations: []
updated_at: 2026-11-06T19:43:14.667731+00:00
```

## M2-02

Calendar read and availability semantics. Documentation: [docs/USER_GUIDE.md](USER_GUIDE.md), tests/evidence: test_connectors.py, test_workflows.py.

```yaml
issue: M2-02
status: done
commit: uncommitted local working tree
changed_files: ["src/workspace_ai/connectors.py", "src/workspace_ai/contracts.py"]
checks:
  - command: make ci
    environment: LD_LIBRARY_PATH supplied for this host's Chromium libraries
    exit_code: 0
    backend_tests_passed: 213
    frontend_unit_tests_passed: 12
    browser_tests_passed: 10
mcp_protocol_test: actual HTTP/stdio protocol suite in the successful combined gate
security_review: "Timezone/DST and unavailable-calendar semantics tested; no unapproved booking."
known_limitations: []
updated_at: 2026-11-06T19:43:14.667731+00:00
```

## M2-03

Drive reads and bounded extraction. Documentation: [docs/OAUTH_SETUP.md](OAUTH_SETUP.md), tests/evidence: test_extraction.py, test_connectors.py.

```yaml
issue: M2-03
status: done
commit: uncommitted local working tree
changed_files: ["src/workspace_ai/connectors.py", "src/workspace_ai/extraction.py"]
checks:
  - command: make ci
    environment: LD_LIBRARY_PATH supplied for this host's Chromium libraries
    exit_code: 0
    backend_tests_passed: 213
    frontend_unit_tests_passed: 12
    browser_tests_passed: 10
mcp_protocol_test: actual HTTP/stdio protocol suite in the successful combined gate
security_review: "Per-file scope, resource-key bounds and hostile parser limits verified."
known_limitations: []
updated_at: 2026-11-06T19:43:14.667731+00:00
```

## M3-01

Artifact IR and seven renderers. Documentation: [docs/SECURITY.md](SECURITY.md), tests/evidence: test_artifacts.py.

```yaml
issue: M3-01
status: done
commit: uncommitted local working tree
changed_files: ["src/workspace_ai/artifacts.py", "assets/fonts"]
checks:
  - command: make ci
    environment: LD_LIBRARY_PATH supplied for this host's Chromium libraries
    exit_code: 0
    backend_tests_passed: 213
    frontend_unit_tests_passed: 12
    browser_tests_passed: 10
mcp_protocol_test: actual HTTP/stdio protocol suite in the successful combined gate
security_review: "Safe formula/string types, ZIP/XML guards and semantic readback verified."
known_limitations: ["Native Office visual layout review NOT_RUN; semantic/structural checks passed"]
updated_at: 2026-11-06T19:43:14.667731+00:00
```

## M3-02

Owned library, provenance and downloads. Documentation: [docs/USER_GUIDE.md](USER_GUIDE.md), tests/evidence: test_api.py, test_workflows.py.

```yaml
issue: M3-02
status: done
commit: uncommitted local working tree
changed_files: ["src/workspace_ai/runtime.py", "src/workspace_ai/api.py"]
checks:
  - command: make ci
    environment: LD_LIBRARY_PATH supplied for this host's Chromium libraries
    exit_code: 0
    backend_tests_passed: 213
    frontend_unit_tests_passed: 12
    browser_tests_passed: 10
mcp_protocol_test: actual HTTP/stdio protocol suite in the successful combined gate
security_review: "Owner downloads, atomic publication, quotas and deletion cleanup verified."
known_limitations: ["Native Office visual layout review NOT_RUN; semantic/structural checks passed"]
updated_at: 2026-11-06T19:43:14.667731+00:00
```

## M4-01

Exact-action policy and one-use approval. Documentation: [docs/SECURITY.md](SECURITY.md), tests/evidence: test_security.py.

```yaml
issue: M4-01
status: done
commit: uncommitted local working tree
changed_files: ["src/workspace_ai/security.py", "src/workspace_ai/runtime.py"]
checks:
  - command: make ci
    environment: LD_LIBRARY_PATH supplied for this host's Chromium libraries
    exit_code: 0
    backend_tests_passed: 213
    frontend_unit_tests_passed: 12
    browser_tests_passed: 10
mcp_protocol_test: actual HTTP/stdio protocol suite in the successful combined gate
security_review: "Exact arguments/revision, expiry, cross-user access and concurrent replay tested."
known_limitations: []
updated_at: 2026-11-06T19:43:14.667731+00:00
```

## M4-02

Eight gated Google writes. Documentation: [docs/USER_GUIDE.md](USER_GUIDE.md), tests/evidence: test_api.py, test_protocol.py.

```yaml
issue: M4-02
status: done
commit: uncommitted local working tree
changed_files: ["src/workspace_ai/connectors.py", "src/workspace_ai/agent.py"]
checks:
  - command: make ci
    environment: LD_LIBRARY_PATH supplied for this host's Chromium libraries
    exit_code: 0
    backend_tests_passed: 213
    frontend_unit_tests_passed: 12
    browser_tests_passed: 10
mcp_protocol_test: actual HTTP/stdio protocol suite in the successful combined gate
security_review: "All eight Google write tools require server-consumed one-use approval; unknown effects not retried."
known_limitations: []
updated_at: 2026-11-06T19:43:14.667731+00:00
```

## M5-01

OIDC, incremental OAuth and vault lifecycle. Documentation: [docs/OAUTH_SETUP.md](OAUTH_SETUP.md), tests/evidence: test_google_auth.py, test_security.py, test_vault.py.

```yaml
issue: M5-01
status: done
commit: uncommitted local working tree
changed_files: ["src/workspace_ai/google_auth.py", "src/workspace_ai/api.py", "src/workspace_ai/security.py"]
checks:
  - command: make ci
    environment: LD_LIBRARY_PATH supplied for this host's Chromium libraries
    exit_code: 0
    backend_tests_passed: 213
    frontend_unit_tests_passed: 12
    browser_tests_passed: 10
mcp_protocol_test: actual HTTP/stdio protocol suite in the successful combined gate
security_review: "Signed claims, subject/session binding, refresh/revoke fences, atomic rotation and fresh-only restore tested with fixtures."
known_limitations: ["Real Google account/domain verification NOT_RUN; HTTP-stub contracts passed"]
updated_at: 2026-11-06T19:43:14.667731+00:00
```

## M5-02

Live adapter contracts and narrow Drive selection. Documentation: [docs/OAUTH_SETUP.md](OAUTH_SETUP.md), tests/evidence: test_connectors.py, test_security.py.

```yaml
issue: M5-02
status: done
commit: uncommitted local working tree
changed_files: ["src/workspace_ai/connectors.py", "src/workspace_ai/api.py"]
checks:
  - command: make ci
    environment: LD_LIBRARY_PATH supplied for this host's Chromium libraries
    exit_code: 0
    backend_tests_passed: 213
    frontend_unit_tests_passed: 12
    browser_tests_passed: 10
mcp_protocol_test: actual HTTP/stdio protocol suite in the successful combined gate
security_review: "Method-specific scopes, ETags, exact MIME and Drive file/resource-key access tested with HTTP fixtures."
known_limitations: ["Real Google account/domain verification NOT_RUN; HTTP-stub contracts passed"]
updated_at: 2026-11-06T19:43:14.667731+00:00
```

## M6-01

Bounded agent, SSE and resumable state. Documentation: [docs/ARCHITECTURE.md](ARCHITECTURE.md), tests/evidence: test_api.py, test_workflows.py.

```yaml
issue: M6-01
status: done
commit: uncommitted local working tree
changed_files: ["src/workspace_ai/agent.py", "src/workspace_ai/api.py"]
checks:
  - command: make ci
    environment: LD_LIBRARY_PATH supplied for this host's Chromium libraries
    exit_code: 0
    backend_tests_passed: 213
    frontend_unit_tests_passed: 12
    browser_tests_passed: 10
mcp_protocol_test: actual HTTP/stdio protocol suite in the successful combined gate
security_review: "SSE cursor replay, cancellation, bounded calls, interrupted restart and unknown operations tested."
known_limitations: ["FakeLLM pipeline only; real-model reasoning/claim accuracy NOT_RUN"]
updated_at: 2026-11-06T19:43:14.667731+00:00
```

## M6-02

Accessible browser workflows and generated API types. Documentation: [docs/USER_GUIDE.md](USER_GUIDE.md), tests/evidence: web unit and Playwright suites.

```yaml
issue: M6-02
status: done
commit: uncommitted local working tree
changed_files: ["web"]
checks:
  - command: make ci
    environment: LD_LIBRARY_PATH supplied for this host's Chromium libraries
    exit_code: 0
    backend_tests_passed: 213
    frontend_unit_tests_passed: 12
    browser_tests_passed: 10
mcp_protocol_test: actual HTTP/stdio protocol suite in the successful combined gate
security_review: "Exact-action review, generated types, source rendering and duplicate submission handling verified."
known_limitations: []
updated_at: 2026-11-06T19:43:14.667731+00:00
```

## M7-01

Adversarial boundaries and recovery. Documentation: [docs/SECURITY.md](SECURITY.md), tests/evidence: test_security.py, test_extraction.py.

```yaml
issue: M7-01
status: done
commit: uncommitted local working tree
changed_files: ["src/workspace_ai/security.py", "src/workspace_ai/runtime.py", "src/workspace_ai/extraction.py"]
checks:
  - command: make ci
    environment: LD_LIBRARY_PATH supplied for this host's Chromium libraries
    exit_code: 0
    backend_tests_passed: 213
    frontend_unit_tests_passed: 12
    browser_tests_passed: 10
mcp_protocol_test: actual HTTP/stdio protocol suite in the successful combined gate
security_review: "Security suite covers 17 tests plus parser/artifact/injection/isolation cases elsewhere; no extra denominator inferred."
known_limitations: []
updated_at: 2026-11-06T19:43:14.667731+00:00
```

## M7-02

Measured synthetic evaluation. Documentation: [docs/EVALUATION.md](EVALUATION.md), tests/evidence: make eval.

```yaml
issue: M7-02
status: done
commit: uncommitted local working tree
changed_files: ["evaluation.py", "eval"]
checks:
  - command: make ci
    environment: LD_LIBRARY_PATH supplied for this host's Chromium libraries
    exit_code: 0
    backend_tests_passed: 213
    frontend_unit_tests_passed: 12
    browser_tests_passed: 10
mcp_protocol_test: actual HTTP/stdio protocol suite in the successful combined gate
security_review: "Every case forbids unapproved writes; FakeLLM and reference-integrity scores are explicitly scoped."
known_limitations: ["FakeLLM pipeline only; real-model reasoning/claim accuracy NOT_RUN"]
updated_at: 2026-11-06T19:43:14.667731+00:00
```

## M7-03

CI, dependency scans and containers. Documentation: [docs/OPERATIONS.md](OPERATIONS.md), tests/evidence: make ci and container smoke.

```yaml
issue: M7-03
status: done
commit: uncommitted local working tree
changed_files: ["Dockerfile", "compose.yaml", ".github/workflows/ci.yml", "scripts"]
checks:
  - command: make ci
    environment: LD_LIBRARY_PATH supplied for this host's Chromium libraries
    exit_code: 0
    backend_tests_passed: 213
    frontend_unit_tests_passed: 12
    browser_tests_passed: 10
mcp_protocol_test: actual HTTP/stdio protocol suite in the successful combined gate
security_review: "Dependency audits, Bandit and heuristic source scan passed; no-network nonroot image smoke passed."
known_limitations: ["Remote CI/public deployment NOT_RUN; local gates and containers passed"]
updated_at: 2026-11-06T19:43:14.667731+00:00
```

## M8-01

Architecture, setup and operations documentation. Documentation: [docs/FINAL_HANDOFF.md](FINAL_HANDOFF.md), tests/evidence: schema/docs review.

```yaml
issue: M8-01
status: done
commit: uncommitted local working tree
changed_files: ["README.md", "docs"]
checks:
  - command: make ci
    environment: LD_LIBRARY_PATH supplied for this host's Chromium libraries
    exit_code: 0
    backend_tests_passed: 213
    frontend_unit_tests_passed: 12
    browser_tests_passed: 10
mcp_protocol_test: actual HTTP/stdio protocol suite in the successful combined gate
security_review: "Commands and limits reviewed against implementation; live prerequisites explicit."
known_limitations: []
updated_at: 2026-11-06T19:43:14.667731+00:00
```

## M8-02

Independent protocol and artifact examples. Documentation: [docs/MCP_PROTOCOL.md](MCP_PROTOCOL.md), tests/evidence: independent client and readback.

```yaml
issue: M8-02
status: done
commit: uncommitted local working tree
changed_files: ["examples", "docs/demo"]
checks:
  - command: make ci
    environment: LD_LIBRARY_PATH supplied for this host's Chromium libraries
    exit_code: 0
    backend_tests_passed: 213
    frontend_unit_tests_passed: 12
    browser_tests_passed: 10
mcp_protocol_test: actual HTTP/stdio protocol suite in the successful combined gate
security_review: "Only synthetic files/captures/traces included; Inspector credentials held in private temporary config."
known_limitations: []
updated_at: 2026-11-06T19:43:14.667731+00:00
```

## M8-03

Final acceptance and handoff. Documentation: [docs/FINAL_HANDOFF.md](FINAL_HANDOFF.md), tests/evidence: full verification.

```yaml
issue: M8-03
status: done
commit: uncommitted local working tree
changed_files: ["docs/progress.md", "docs/FINAL_HANDOFF.md"]
checks:
  - command: make ci
    environment: LD_LIBRARY_PATH supplied for this host's Chromium libraries
    exit_code: 0
    backend_tests_passed: 213
    frontend_unit_tests_passed: 12
    browser_tests_passed: 10
mcp_protocol_test: actual HTTP/stdio protocol suite in the successful combined gate
security_review: "Check counts derive from actual successful executions; external checks remain NOT_RUN."
known_limitations: ["Remote CI/public deployment NOT_RUN; local gates and containers passed"]
updated_at: 2026-11-06T19:43:14.667731+00:00
```

