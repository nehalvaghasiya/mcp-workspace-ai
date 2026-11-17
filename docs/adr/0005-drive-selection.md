# Narrow Drive access and domain-dependent selection

Status: accepted for the approved core release.

Use drive.file, not a silent whole-Drive grant. JS Picker needs a browser OAuth token and conflicts with the selected server-only credential rule. Implement Drive Open-with as the existing-file selection path, requiring a fully qualified domain, Drive UI configuration and drive.install. Localhost supports app-created files. Validate ids/exportIds/resource keys under the active app user through MCP; never treat the supplied Drive userId as authentication. Domain/live checks remain NOT_RUN until configured.

Evidence: source contracts and tests, docs/MCP_PROTOCOL.md, docs/SECURITY.md and the final handoff record.
