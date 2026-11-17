# Executed protocol and runtime proof

These results were captured from the local uncommitted working tree on 2026-11-06. No Google account or model service was contacted.

| Execution | Observed result | Saved evidence |
|---|---|---|
| Official SDK independent HTTP client | Protocol 2026-07-28, discovery and Demo call PASS; credential output absent | `examples/independent_mcp_client.py`; full protocol tests |
| Official SDK independent stdio client | Protocol 2026-07-28, discovery and Demo call PASS; credential output absent | Same independent example and subprocess test |
| Inspector 2.5.0 | 10/10 commands exited 0 across HTTP and stdio | [inspector-proof.json](inspector-proof.json) |
| Discovered catalog | 31 actual schemas, five server identities | [tool-catalog.json](../mcp/tool-catalog.json) |
| Northstar report | Gmail, Calendar, Drive and Artifact traces; four files downloaded and reopened | [trace](../../examples/expected_traces/northstar.json), [file manifest](../../examples/generated/manifest.json) |
| Isolated final Docker image | Nonroot, read-only root filesystem, no external network; smoke PASS, frontend PASS | [container-proof.json](container-proof.json) |
| Docker Compose | Built service became healthy; four-file smoke and frontend PASS; own test volume removed | [compose-proof.json](compose-proof.json) |

The container's smoke run observed 31 tools, four generated files and 18 tool-trace events. Measured cgroup peak memory was 237,375,488 bytes under an 8 GiB limit. This is one synthetic run, not a physical 8 GB machine or concurrency benchmark. Image identity and settings are preserved in the JSON.

The browser captures in [screenshots](screenshots/) were produced by the running application and inspected. Desktop/mobile report, artifact library, and exact-action approval captures are available. Fixture-only UI tests and actual-backend browser flows are distinguished in [browser QA evidence](../../web/qa/evidence.json). Native Word/PowerPoint/Excel/PDF application layout review is NOT_RUN.

Reproduce with `make setup`, `make dev`, then `make smoke`, `make eval`, `uv run python scripts/generate_examples.py`, and the [Inspector procedure](../mcp/INSPECTOR_GUIDE.md). `make test` and `make test-e2e` start isolated mock servers; stop a dev API before the browser suite.
