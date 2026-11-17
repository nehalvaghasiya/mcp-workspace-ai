# Official MCP SDK and transport contracts

Status: accepted for the approved core release.

Pin the official Python mcp package in uv.lock. Observed version 2.3.0 supports 2026-07-28 over real HTTP and stdio. Use SDK discovery rather than an invented JSON-RPC router. MCP uses HTTPX2; Google/OAuth adapters use HTTPX with injected mock transports. Keep the SDK-generated request wrapper {request:{...}} so one Pydantic input model defines validation and schema. Legacy interoperability and optional protocol extensions are not release claims.

Evidence: source contracts and tests, docs/MCP_PROTOCOL.md, docs/SECURITY.md and the final handoff record.
