# One package and a modular monolith

Status: accepted for the approved core release.

Use one uv-managed distributable package, one React app, SQLite with Alembic, and five independently addressable MCP modules in one process. This adjusts the suggested multi-package workspace layout to meet the explicit minimal-code requirement. Keep adapter and transport boundaries real. In-process locks and workers support a single API worker; multiple-worker/distributed deployment is not claimed verified.

Evidence: source contracts and tests, docs/MCP_PROTOCOL.md, docs/SECURITY.md and the final handoff record.
