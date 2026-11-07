# Gmail MCP package

This package owns the gmail tools, schemas and providers. The API composition root supplies the trusted execution context; handlers execute through the official SDK. Use `workspace-ai mcp gmail --transport stdio` for the authenticated standalone entrypoint. No tool grants approval to itself. Public tool names and schemas remain unchanged by package layout.
