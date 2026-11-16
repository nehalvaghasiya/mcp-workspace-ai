# MCP server development

Each package exports `tool_definitions()` and `create_server(runtime)`. Definitions own the canonical name, typed input, risk, scopes and digest. The shared SDK factory registers structured ToolResult handlers and safe resources/prompts. Handlers call trusted execution context, never model-supplied identity or authority.

Keep one class per schema file and preserve titles/defaults. The SDK envelope is `{"request": {...}}`. Public namespaces remain `gmail`, `calendar`, `drive`, singular `artifact`, and `demo`; the documents directory does not rename the wire contract.

Providers belong in their connector package. Reused parsing/network/mock-store primitives belong in common. Servers import neither API nor other connectors. The API injects database, credential and operation capabilities to keep application persistence out of server dependencies.

Writes prepare snapshots and use the exact-action transaction boundary. Preserve shared locks, cancellation/draining and uncertain outcomes. Do not split approval consumption from operation creation.

Changes require actual client protocol calls, typed/malformed validation and owner/scope negatives. Review contract changes before refreshing generated snapshots. Deferred tools remain unregistered. See [catalog](tool-catalog.md), [client guide](client-integration.md), [approvals](../security/approval-policies.md) and [testing](../development/testing-guide.md).
