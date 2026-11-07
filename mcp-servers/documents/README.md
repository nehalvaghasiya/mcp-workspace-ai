# Documents MCP package

The package implements the existing **artifact** MCP namespace. It creates DOCX,
PDF, XLSX, PPTX, CSV, Markdown and sanitized HTML, then validates structural and
semantic readback before atomic publication. The API owns user authorization,
metadata, quotas and downloads; handlers receive the shared application context.

The public Python entry point is `mcp_documents.artifacts.ArtifactEngine`.
`mcp_documents.server.create_server(runtime)` builds the official-SDK server;
`tool_definitions()` exposes its ten canonical definitions. The host CLI retains
`workspace-ai mcp artifact --transport stdio`.

Schemas, format generators, validators and resources have separate owners. Each
handwritten class is defined in one file. Licensed DejaVu fonts are installed as
package resources; their notices are included beside the font files.

Native Office conversion remains deferred. No conversion placeholder is
registered. Structural readback does not establish identical visual layout in
every native Office viewer; that review remains a separate check.
