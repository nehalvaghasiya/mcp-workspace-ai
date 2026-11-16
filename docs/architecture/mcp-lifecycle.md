# MCP lifecycle

The application constructs all five SDK servers from package-owned definitions and one shared execution context. Startup enters every server session manager; shutdown drains/cancels tasks and closes adapters and managers through the same context.

The host discovers tools over actual HTTP using the official client. A descriptor must belong to the trusted registry; its input/output/policy digest is retained and checked. A changed descriptor requires operator review before automatic execution.

Each request carries an expiring assertion binding user, server audience and tools. The receiving guard checks the active actor and Origin/host protection. Tool handlers recheck connector scopes, ownership and approval. Discovery/resources/prompts expose only their documented safe metadata.

Read calls have bounded deadlines/retries. Writes consume exact-action authority transactionally and are not blindly retried after dispatch. Errors are bounded and sanitized; private bodies and credentials are excluded from traces.

Restart leaves active work interrupted or pending and dispatched operations outcome_unknown. Application SSE reconnection replays stored events without replaying MCP effects. See [client integration](../mcp/client-integration.md), [server development](../mcp/server-development.md), [compatibility](../mcp/compatibility-matrix.md) and [approvals](../security/approval-policies.md).
