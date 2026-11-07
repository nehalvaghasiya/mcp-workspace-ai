from __future__ import annotations

import html
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from mcp_documents.exceptions.artifact_error import ArtifactError
from mcp_documents.renderers.fonts import _pdf_fonts
from mcp_documents.schemas.artifact_spec import ArtifactSpec
from mcp_documents.schemas.bullet_list import BulletList
from mcp_documents.schemas.heading import Heading
from mcp_documents.schemas.paragraph_block import ParagraphBlock
from mcp_documents.utils.conversion import _block_text


def _render_pdf(spec: ArtifactSpec, path: Path) -> None:
    regular, bold = _pdf_fonts()
    supported = pdfmetrics.getFont(regular).face.charToGlyph
    for text in [spec.title, *[text for block in spec.blocks for text in _block_text(block)]]:
        if any(ord(character) not in supported for character in text if not character.isspace()):
            raise ArtifactError("PDF font does not support a requested Unicode character")
    body = ParagraphStyle(
        "Body", fontName=regular, fontSize=10, leading=15, spaceAfter=9, alignment=TA_LEFT
    )
    heading = ParagraphStyle(
        "Heading",
        parent=body,
        fontName=bold,
        fontSize=16,
        leading=21,
        spaceBefore=12,
        spaceAfter=10,
    )
    title = ParagraphStyle("Title", parent=heading, fontSize=23, leading=29, spaceAfter=20)
    cell_style = ParagraphStyle("Cell", parent=body, fontSize=8, leading=11, spaceAfter=0)

    def paragraph(text: str, style: ParagraphStyle = body) -> Paragraph:
        return Paragraph(html.escape(text).replace("\n", "<br/>"), style)

    story: list[object] = [paragraph(spec.title, title)]
    for block in spec.blocks:
        if isinstance(block, Heading):
            story.append(paragraph(block.text, heading))
        elif isinstance(block, ParagraphBlock):
            story.append(paragraph(block.text))
        elif isinstance(block, BulletList):
            story.extend(paragraph("• " + item) for item in block.items)
        else:
            data = [
                [paragraph(text, cell_style) for text in row]
                for row in [block.headers, *block.rows]
            ]
            table = Table(
                data,
                colWidths=[(A4[0] - 100) / len(block.headers)] * len(block.headers),
                repeatRows=1,
                hAlign="LEFT",
            )
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e9eef7")),
                        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#bcc7d5")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            story.extend([table, Spacer(1, 10)])

    def footer(canvas: Canvas, document: SimpleDocTemplate) -> None:
        canvas.setFont(regular, 8)
        canvas.drawRightString(A4[0] - 50, 27, f"Page {document.page}")

    document = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=45,
        bottomMargin=45,
        title=spec.title,
        author=spec.metadata.get("author", "MCP Workspace AI"),
        subject=spec.metadata.get("subject", ""),
    )
    document.build(story, onFirstPage=footer, onLaterPages=footer)
