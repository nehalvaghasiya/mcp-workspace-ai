# Independent MCP Inspector

The pre-reorganization executed reference is Inspector **2.5.0**, separately installed from the backend. Start `make dev` first. Keep the same working directory and DATA_DIR for the HTTP server and the stdio subprocess.

```sh
mkdir -p /tmp/workspace-inspector
pnpm --dir /tmp/workspace-inspector add --ignore-scripts --save-exact @modelcontextprotocol/inspector@2.5.0
uv run python scripts/inspector_proof.py --inspector /tmp/workspace-inspector/node_modules/.bin/mcp-inspector --output demo/evidence/inspector-proof.json
```

Use the pinned executable printed by `uv run python scripts/bootstrap_pnpm.py` if pnpm is not on PATH. Inspector is a separate temporary tool installation, not a project dependency.

The script creates a synthetic CLI user, obtains a short-lived assertion, and invokes Inspector's connection probe, `tools/list`, `tools/call`, `resources/list` and `prompts/list` for each transport. It requires protocol 2026-07-28 and a successful structured Demo result. A failing command exits nonzero; the saved JSON contains only status metadata.

The temporary Inspector configuration has mode 0600. Credentials are passed through its headers/environment configuration, never as command-line arguments. Inspector token persistence is disabled and the temporary directory is removed. Do not paste the configuration, assertion, or environment into an issue or screenshot.

For interactive inspection, use a private configuration with the same `streamable-http` or `stdio` server definition and `protocolEra: modern`. The HTTP URL is `http://127.0.0.1:8000/mcp/demo/`; the stdio executable is the installed `workspace-ai` command with arguments `mcp demo --transport stdio`. `WORKSPACE_MCP_TOKEN` must be set privately for stdio. See the script for the exact configuration accepted by the pinned Inspector version.

The captured baseline [10 successful observations](../../demo/evidence/baseline/inspector-proof.json) cover Demo, while the official-client protocol tests exercise all registered tools and five HTTP servers. The [independent Python client](../../examples/multi-server-workflows/independent_mcp_client.py) is a smaller alternative without an Inspector dependency.
