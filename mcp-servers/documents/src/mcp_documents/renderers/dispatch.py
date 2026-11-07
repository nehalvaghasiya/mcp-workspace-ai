from __future__ import annotations

from pathlib import Path

from mcp_documents.generators.csv_generator import _render_csv
from mcp_documents.generators.docx_generator import _render_docx
from mcp_documents.generators.html_generator import _render_html
from mcp_documents.generators.markdown_generator import _render_markdown
from mcp_documents.generators.pdf_generator import _render_pdf
from mcp_documents.generators.pptx_generator import _render_pptx
from mcp_documents.generators.xlsx_generator import _render_xlsx
from mcp_documents.schemas.artifact_spec import ArtifactSpec


def render_artifact(spec: ArtifactSpec, path: Path) -> None:
    if spec.format == "docx":
        _render_docx(spec, path)
    elif spec.format == "pdf":
        _render_pdf(spec, path)
    elif spec.format == "xlsx":
        _render_xlsx(spec, path)
    elif spec.format == "pptx":
        _render_pptx(spec, path)
    elif spec.format == "csv":
        _render_csv(spec, path)
    elif spec.format == "markdown":
        path.write_text(_render_markdown(spec), encoding="utf-8")
    else:
        path.write_text(_render_html(spec), encoding="utf-8")
