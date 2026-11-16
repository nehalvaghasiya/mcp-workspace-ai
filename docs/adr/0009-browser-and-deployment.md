# Hash navigation and a static nonroot runtime

Status: accepted for the approved core release.

Use hash navigation to keep the browser small and serve the built frontend without a server-side routing dependency. OAuth/Drive callbacks return to /#connectors. Containers build frontend assets and a locked uv environment, run nonroot, persist only app storage, and publish loopback by default. Internal MCP endpoints are private host interfaces, not an externally exposed OAuth resource server. Public release, hosting and Google verification are separate authorized work.

Evidence: source contracts and tests, docs/MCP_PROTOCOL.md, docs/SECURITY.md and the final handoff record.
