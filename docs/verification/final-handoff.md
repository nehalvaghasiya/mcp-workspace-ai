# Workspace reorganization handoff

The approved repository migration preserves the core release and its mock workflows. External acceptance remains separate: live Google execution, real-model quality, domain-dependent Drive selection, native Office layout review, remote CI and public deployment have not been exercised.

## Delivered organization

Eight installable Python members share one uv environment and root lockfile: API, Gmail, Calendar, Drive, Documents, Demo, common utilities and evaluations. The frontend and generated shared types use pinned pnpm 12.18.0 with one root lockfile. Node 24 and Python 3.12 remain the supported development versions.

The default runtime is one backend process with five authenticated official-SDK MCP endpoints. Providers remain behind actual MCP calls. One application execution context owns adapters, tasks, locks, render limits, schema digests and deletion fences. Approval consumption and operation creation remain transactional.

The API, tools, database, schemas, providers and test helpers have at most one handwritten class per file. React components have individual files. Architecture checks cover import direction, legacy imports, ownership and module size. All 31 tool contracts, risk/schema digests, public OpenAPI and database metadata compare exactly with the baseline. Database revisions and private storage paths are preserved.

## Executed verification

| Check | Actual result |
|---|---|
| Locked `make setup` | PASS; uv workspace and pinned pnpm frozen lock |
| Complete `make ci` | PASS; static checks, backend/frontend/security tests, builds and browser workflows |
| Backend identities | All 213 baseline identities mapped; 221 tests pass, including eight migration checks |
| Coverage across all eight production source directories | 89.30%: 4,772 of 5,344 statements; required minimum 86% |
| Frontend | 12 unit/integration cases and 10 Chromium browser cases pass; all 22 identities mapped |
| Security | 40 security regression cases pass separately; dependency audits report no known vulnerabilities |
| Wire/data compatibility | All 31 raw MCP descriptors/digests, OpenAPI and SQL metadata match; synthetic pre-migration storage opens without resetting data |
| Installed wheels | Eight noneditable wheels installed in a fresh environment outside the checkout; no `PYTHONPATH` or editable imports |
| Packaged resources | Migrations, fixtures, 52 unchanged cases, templates, fonts/license and seven generated formats pass the installed-package probe |
| Independent MCP client | All five endpoints pass discovery and bounded reads over HTTP and subprocess stdio: 10/10 |
| Inspector 2.5.0 | HTTP and stdio connection, tools/list, tools/call, resources/list and prompts/list: 10/10 |
| Deterministic evaluation | 52/52 preserved FakeLLM cases pass; p50 410.96 ms, p95 734.11 ms |
| Docker and Compose | Built frontend, 31-tool smoke, four valid files, 52 packaged cases and cleanup pass |

The full CI gate passed before the final correction to coverage source selection. Static checks and `make test` were then repeated with all production directories explicitly included, so an unimported evaluation package cannot silently disappear from the denominator. The authoritative final measurement is recorded separately from the earlier 91.23% imported-package result.

The container ran as `10001:10001`, with a read-only root filesystem and no external network. Its measured cgroup peak was 278,634,496 bytes under an 8 GiB limit. This synthetic smoke run is not a physical-machine or load-test benchmark. Model cost is zero for FakeLLM; these cases do not measure general model reasoning or freeform claim accuracy.

## Evidence and reproduction

- [Final machine-readable record](reorganization/final.json), [installed wheels](reorganization/wheels.json), [integrity checks](reorganization/integrity.json)
- [Complete move inventory](reorganization/move-inventory.json), [Python source moves](reorganization/source-moves.json), [backend identities](reorganization/test-moves.json), [frontend identities](reorganization/frontend-test-moves.json), [dependency comparison](reorganization/dependency-migration.json)
- [Independent client](../../demo/evidence/reorganization/independent-client.json), [Inspector](../../demo/evidence/reorganization/inspector-proof.json), [container](../../demo/evidence/reorganization/container-proof.json), [Compose](../../demo/evidence/reorganization/compose-proof.json)
- [Latest 52-case report](../../evaluations/reports/latest.json), [summary](../../evaluations/reports/latest.md), [actual application captures](../../demo/screenshots/reorganization/)

Run `make setup`, `make ci`, and then `make dev`. Against the running mock API, run `make smoke eval`. `uv run --locked python scripts/verify_installed_wheels.py` checks the complete wheel set after `make build`. Build the image with `docker buildx build --load --target api -f infra/docker/base.Dockerfile -t mcp-workspace-ai:reorganized .`, then run `uv run --locked python scripts/verify_containers.py` and `uv run --locked python scripts/verify_containers.py --compose`. Compose/browser checks reserve port 8000 and must run sequentially.

The evaluation resources have one packaged authority, with `evaluations/datasets` linking to it. Both direct wheels and wheels rebuilt from source distributions contain the same six datasets. The installed-wheel probe caught and verified the correction to source-distribution resource selection.

## Preservation and remaining boundaries

The complete inventory maps 149 baseline files. Original specifications and historical evidence retain recorded hashes. A source-only rollback archive is stored at ignored `.local/reorganization/source-baseline.tar.gz`; its checksum and 149 entries are verified. The original temporary checkpoint paths are historical capture locations; use the durable local archive if those paths no longer exist. No private runtime data was copied into the archive, reset or relocated.

Authlib emits a deprecation warning for its JOSE import; the current dependency audit passes. A narrowly documented Bandit exclusion identifies Google's public token endpoint URL as a URL rather than a password. Neither warning is represented as a failed provider check.

Live sends, invitations, sharing, remote deletion, publication and deployment were not performed. Deferred Drive move/share, document conversion, hosted MCP registration, indexing and optional infrastructure remain documented roadmap items. See the [external acceptance matrix](acceptance-matrix.md) for prerequisites and explicit NOT_RUN statuses. Historical baseline results remain under [historical records](historical/README.md) and [baseline evidence](../../demo/evidence/baseline/).
