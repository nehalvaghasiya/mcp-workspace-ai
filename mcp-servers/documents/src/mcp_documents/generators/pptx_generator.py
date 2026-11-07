from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

from mcp_documents.schemas.artifact_spec import ArtifactSpec
from mcp_documents.utils.conversion import _slides


def _render_pptx(spec: ArtifactSpec, path: Path) -> None:
    presentation = Presentation()
    presentation.slide_width, presentation.slide_height = Inches(13.333), Inches(7.5)
    presentation.core_properties.title = spec.title
    presentation.core_properties.author = spec.metadata.get("author", "MCP Workspace AI")
    for number, slide_spec in enumerate(_slides(spec), 1):
        slide = presentation.slides.add_slide(presentation.slide_layouts[6])
        title = slide.shapes.add_textbox(Inches(0.6), Inches(0.35), Inches(12.1), Inches(1))
        title.text_frame.word_wrap = True
        title.text = slide_spec.title
        for paragraph in title.text_frame.paragraphs:
            paragraph.font.name = "DejaVu Sans"
            paragraph.font.size = Pt(30)
            paragraph.font.bold = True
            paragraph.font.color.rgb = RGBColor.from_string("244563")
        content = slide.shapes.add_textbox(
            Inches(0.65), Inches(1.55), Inches(12), Inches(2 if slide_spec.tables else 5.1)
        )
        frame = content.text_frame
        frame.word_wrap = True
        lines = ([slide_spec.body] if slide_spec.body else []) + [
            "• " + item for item in slide_spec.bullets
        ]
        for index, text in enumerate(lines):
            paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
            paragraph.text = text
            paragraph.font.name = "DejaVu Sans"
            length = sum(map(len, lines))
            paragraph.font.size = Pt(18 if length < 800 else 14 if length < 1_400 else 12)
            paragraph.space_after = Pt(10)
        for table_spec in slide_spec.tables:
            table = slide.shapes.add_table(
                len(table_spec.rows) + 1,
                len(table_spec.headers),
                Inches(0.65),
                Inches(3.5),
                Inches(12),
                Inches(3),
            ).table
            for row_index, row in enumerate([table_spec.headers, *table_spec.rows]):
                for column, text in enumerate(row):
                    cell = table.cell(row_index, column)
                    cell.text = text
                    for paragraph in cell.text_frame.paragraphs:
                        paragraph.font.size = Pt(10)
                        paragraph.font.bold = row_index == 0
        page = slide.shapes.add_textbox(Inches(11.5), Inches(7.03), Inches(1.2), Inches(0.25))
        page.text = str(number)
        if slide_spec.notes:
            notes = slide.notes_slide.notes_text_frame
            if notes is not None:
                notes.text = slide_spec.notes
    presentation.save(str(path))
