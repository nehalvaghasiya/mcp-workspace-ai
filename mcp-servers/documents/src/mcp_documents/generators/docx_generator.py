from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.shared import Inches as WordInches
from docx.shared import Pt as WordPt

from mcp_documents.schemas.artifact_spec import ArtifactSpec
from mcp_documents.schemas.bullet_list import BulletList
from mcp_documents.schemas.heading import Heading
from mcp_documents.schemas.paragraph_block import ParagraphBlock


def _render_docx(spec: ArtifactSpec, path: Path) -> None:
    document = Document()
    document.core_properties.title = spec.title
    document.core_properties.author = spec.metadata.get("author", "MCP Workspace AI")
    document.core_properties.subject = spec.metadata.get("subject", "")
    document.core_properties.language = spec.metadata.get("language", "en-US")
    for section in document.sections:
        section.top_margin = section.bottom_margin = WordInches(0.75)
        section.left_margin = section.right_margin = WordInches(0.8)
        section.footer.paragraphs[0].text = f"MCP Workspace AI · {spec.template.replace('_', ' ')}"
    normal = document.styles["Normal"]
    normal.font.name = "DejaVu Sans"
    normal.font.size = WordPt(11)
    document.add_heading(spec.title, 0)
    for block in spec.blocks:
        if isinstance(block, Heading):
            document.add_heading(block.text, block.level)
        elif isinstance(block, ParagraphBlock):
            document.add_paragraph(block.text)
        elif isinstance(block, BulletList):
            for item in block.items:
                document.add_paragraph(item, style="List Bullet")
        else:
            table = document.add_table(rows=1, cols=len(block.headers))
            table.style = "Light Shading Accent 1" if spec.template != "simple" else "Table Grid"
            for cell, value in zip(table.rows[0].cells, block.headers, strict=True):
                cell.text = value
            for row in block.rows:
                for cell, value in zip(table.add_row().cells, row, strict=True):
                    cell.text = value
    document.save(str(path))
