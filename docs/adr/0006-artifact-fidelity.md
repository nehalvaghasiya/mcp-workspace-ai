# Typed document IR and honest readback

Status: accepted for the approved core release.

Use constrained report blocks, typed worksheets/cells and slides. Render real DOCX/PDF/XLSX/PPTX plus CSV/Markdown/HTML with maintained libraries; avoid shell conversion dependencies. Atomic publication requires structural and semantic readback. Source text stays literal unless an explicitly typed safe arithmetic formula is supplied. Semantic PDF readback excludes only the known generated page-footer prefix, preserving paragraphs across page boundaries. Native Office visual rendering is separate from structure/text validation.

Evidence: source contracts and tests, docs/MCP_PROTOCOL.md, docs/SECURITY.md and the final handoff record.
