# Protocol evidence and reproduction

The [baseline proof narrative](historical/core-protocol-proof.md) and [raw evidence](../../demo/evidence/baseline/) preserve the original executed SDK/Inspector/HTTP/stdio results. They retain their original source fingerprint and are not relabeled as current runs.

The migration keeps all 31 canonical schemas/policy digests and five server audiences unchanged. Root integration compared their raw contracts exactly. Fresh TCP/stdio calls against all five servers and the independent Inspector passed; see the [current handoff](final-handoff.md), [client proof](../../demo/evidence/reorganization/independent-client.json) and [Inspector proof](../../demo/evidence/reorganization/inspector-proof.json).

Reproduce with `make setup`, `make dev`, then `make smoke`, `make eval`, the [independent client](../../examples/multi-server-workflows/README.md), and [Inspector guide](../mcp/inspector-guide.md). Four actual baseline files and their [manifest](../../examples/document-generation/generated/manifest.json) remain available, alongside the [Northstar trace](../../examples/multi-server-workflows/expected-traces/northstar.json).

The [new screenshots](../../demo/screenshots/reorganization/) are actual synthetic application captures from the reorganized backend browser workflows. Earlier captures remain under the parent directory. Controlled fixture-only and actual-backend browser evidence remain distinguished. Native Office visual review is NOT_RUN.

Final workspace results are recorded separately in [verification progress](progress.md) and the integration handoff.
