# Observed MCP compatibility

Baseline verified locally before reorganization on 2026-11-06 with Python 3.12.12, official `mcp==2.3.0` (locked by uv), and MCP Inspector 2.5.0. Both independent clients observed protocol **2026-07-28**. This records the baseline compatibility, not every optional protocol feature. New workspace gate results are recorded separately.

The reorganized workspace repeats the protocol tests and Inspector's ten checks successfully. The [independent client proof](../../demo/evidence/reorganization/independent-client.json) additionally records discovery and one bounded read against each of the five servers over both HTTP and stdio: 10/10 successful observations using protocol 2026-07-28. See the [current handoff](../verification/final-handoff.md) and [Inspector proof](../../demo/evidence/reorganization/inspector-proof.json).

| Capability | HTTP over loopback TCP | Subprocess stdio | Evidence |
|---|---|---|---|
| Modern protocol connection | PASS | PASS | Independent example and Inspector |
| Tool discovery and structured invocation | PASS, all 31 tools across five endpoints | PASS, discovery and one bounded read per endpoint | Protocol/API tests, independent client and Inspector |
| Resources and prompts | PASS, list/read/get on five servers | PASS, Demo list/read/get | Protocol suite; Inspector lists |
| Authentication | Missing, expired, wrong audience and spoofed user rejected | Assertion required in environment | Protocol suite |
| Input validation | Unknown fields rejected for every registered tool | Typed Demo request | Protocol suite |
| Origin/host protection | Untrusted Origin rejected; SDK DNS-rebinding protection enabled | Not applicable | Protocol suite and HTTP guard |
| Approval and owner authorization | Rechecked inside the receiving MCP handler | Same handler/policy implementation | Eight write tools exercised over HTTP |
| Schema trust | Input/output/policy digest pinned by local registry | Same registry | Registry checks and discovery |
| Timeouts, disconnect and cancellation | Bounded deadlines; run cancellation and unavailable-connector tests | Process cleanup verified | API/protocol tests, independent client |

HTTP uses `MCPServer`, official `Client` and `streamable_http_client` with HTTPX2. Under the modern protocol, discovery establishes compatibility without requiring a legacy initialization/session-header exchange. Inspector's CLI action called `initialize` is its connection probe; it is not evidence of an old wire handshake.

Each tool receives `{"request": {...}}`, as generated from the Pydantic model by the SDK. Tool output is the common typed `ToolResult` envelope, with JSON-valued domain data. Scope/risk metadata remain host policy, and are not trusted from a model-supplied description.

The five private endpoints use short-lived internal assertions. They do **not** implement public MCP OAuth discovery for arbitrary hosted clients. Remote server registration, legacy protocol versions, resumable MCP transport streams and Tasks/MRTR extensions have not been independently certified. Stdio acceptance covers discovery and bounded reads; approved writes remain exercised over HTTP in the local protocol/workflow suite. Application SSE reconnection is separately tested and does not redispatch effects.

See [Inspector proof](../../demo/evidence/baseline/inspector-proof.json), [tool schemas](tool-catalog.json), [protocol guide](client-integration.md), and [ADR 0002](../adr/0002-official-mcp-sdk.md).
