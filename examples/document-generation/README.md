# Validated document generation

The [generated directory](generated/) preserves the four actual Northstar DOCX/PDF/XLSX/PPTX baseline downloads and their [manifest](generated/manifest.json). Files and checksums are unchanged by the source-layout migration. Structural/semantic readback is distinct from native Office visual review, which remains NOT_RUN.

To reproduce, ask “Review Northstar launch emails, calendar meetings and Drive proposal; create PDF Word Excel PowerPoint reports.” Inspect source cards, artifact provenance and four server namespaces. `uv run python scripts/generate_examples.py` captures fresh output from a running mock API; a new capture has its own IDs/timestamps.

The document package also supports CSV, Markdown and sanitized HTML. Formula strings are safe literal cells unless explicitly typed as allowlisted arithmetic; server-side formula calculation and native document conversion are not implied.
