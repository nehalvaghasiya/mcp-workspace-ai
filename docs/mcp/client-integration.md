# MCP protocol and interoperability

The official Python SDK is pinned in the root uv.lock. Pre-reorganization verification observed `mcp==2.3.0` on Python 3.12.12 with protocol `2026-07-28`. Compatibility is established by calls, not by a configured version string.

Endpoints are independently addressable at `/mcp/gmail/`, `/mcp/calendar/`, `/mcp/drive/`, `/mcp/artifact/` and `/mcp/demo/`. The host uses official `Client` with `streamable_http_client`; every tool call crosses TCP even when servers share the process. The server uses `MCPServer`, typed handlers and structured results. Modern discovery does not rely on a legacy initialization handshake/session header.

All endpoints authenticate each request. Internal assertions are short-lived, audience-bound and tool-scoped. They are private host credentials, not a public OAuth implementation for arbitrary third-party MCP clients. Network exposure of these private endpoints is out of scope. The CLI only issues sample credentials for synthetic users.

Read policy for discovery, resources and prompts permits an active authenticated app user with a valid assertion for that server audience. Those methods expose only tool descriptors, safe template metadata and prompt text. Private workspace reads additionally require the named tool authority, enabled connector and actual Google scope; a metadata read never grants tool execution.

## Independent calls

Start `make dev`. In another terminal:

```sh
uv run workspace-ai token demo
```

Set that short-lived output as `WORKSPACE_MCP_TOKEN` privately in the terminal, then run:

```sh
uv run python examples/multi-server-workflows/independent_mcp_client.py demo --transport http
uv run python examples/multi-server-workflows/independent_mcp_client.py demo --transport stdio
```

The stdio entrypoint is `uv run workspace-ai mcp demo --transport stdio`. Protocol JSON stays on stdout; diagnostics use stderr. The independent example prints protocol/server/tool metadata and a synthetic read result. Use the same data directory so the signed assertion's synthetic user exists.

The machine-readable catalog is `/api/mcp/tools`; `packages/shared-types/openapi.json` describes app routes. Each SDK tool takes `{"request": {...typed fields...}}`, keeping the Pydantic model as the schema source. This explicit wrapper is an SDK-aligned adjustment to the guides' illustrative flat arguments.

Server resources expose safe template metadata; prompts include meeting_brief. Tests retrieve both through MCP. Schema hashes include input/output and local policy; unknown or changed descriptors are not eligible for automatic execution. Remote registry onboarding, MRTR/Tasks extensions and untested legacy interoperability are not claimed supported.

See [observed compatibility](compatibility-matrix.md) and the [tool catalog](tool-catalog.md) for actual observations and available tools.
