# Independent client and cross-app workflow

Start `make dev`. Obtain a short-lived synthetic assertion with `uv run workspace-ai token demo`, and set it privately as WORKSPACE_MCP_TOKEN. Then run:

```sh
uv run python examples/multi-server-workflows/independent_mcp_client.py demo --transport http
uv run python examples/multi-server-workflows/independent_mcp_client.py demo --transport stdio
```

The client uses the official SDK, prints only protocol/tool/result metadata and requires the same authorized storage/context. Credentials stay in the environment, not command arguments. Other supported namespaces have bounded read examples.

The preserved [Northstar trace](expected-traces/northstar.json) records an actual baseline workflow through Gmail, Calendar, Drive and Artifact. New execution is verified separately; source relocation does not manufacture a fresh protocol run.
