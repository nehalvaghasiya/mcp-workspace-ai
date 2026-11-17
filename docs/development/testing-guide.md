# Testing guide

The repeated pre-migration baseline passed 213 backend tests with 86.38% coverage, 12 frontend unit tests and 10 browser tests. These are baseline measurements, not a new workspace gate claim. Preserve old-to-new test identities and evaluation assertions, not counts alone.

| Command | Purpose |
|---|---|
| `make lint format-check typecheck` | Static checks and formatting |
| `make schema-check` | API and generated-type drift |
| `make test-unit` | Unit tests, including frontend |
| `make test-integration` | Real transport, API and cross-server integration |
| `make test` | Complete backend/frontend unit/contract/integration checks |
| `make test-e2e` | Isolated mock backend and Chromium workflows |
| `make security` | Advisory audits, Bandit/source checks and regressions |
| `make smoke` | Running mock stack and four downloads |
| `make eval` | Running mock API and 52 preserved FakeLLM cases |
| `make ci` | Complete local gate |

Package tests live beside their package; root tests cover cross-server/protocol/end-to-end/security/performance concerns. Helpers have individual class files. Mock execution calls no Google/model service; live contracts use HTTP fixtures. Advisory audits and dependency installation use their own network services.

Exercise actual TCP/stdio, all canonical tools, malformed/authentication/Origin cases, schema changes and deadlines. Reopen artifacts and inspect semantics. Verify isolation, approval races/replay/staleness, cancellation, deletion fences and restart recovery.

Browser evidence distinguishes controlled fixtures from real-backend flows. Native Office visual review remains separate. See [frontend host-library notes](../../apps/web/README.md).

Measure coverage across every production Python package. Install complete wheels outside the checkout without editable imports/PYTHONPATH and verify resources and existing database state. Record final results in [verification progress](../verification/progress.md).
