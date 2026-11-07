from __future__ import annotations

from mcp_documents.exceptions.artifact_error import ArtifactError
from mcp_documents.schemas.artifact_spec import ArtifactSpec
from mcp_documents.schemas.formula_cell import FormulaCell
from mcp_documents.schemas.table_block import TableBlock
from mcp_documents.utils.conversion import _block_text, _cell_text, _sheets, _slides
from mcp_documents.utils.text import _csv_literal, _markdown_text, _normalize
from mcp_documents.validators.inspection import _Inspection


def verify_semantics(spec: ArtifactSpec, result: _Inspection) -> None:
    if spec.format in {"xlsx", "csv"}:
        expected = []
        expected_formulas: list[str] = []
        for sheet in _sheets(spec):
            rows = [
                list(sheet.columns),
                *[[_cell_text(cell) for cell in row] for row in sheet.rows],
            ]
            if spec.format == "csv":
                rows = [[_csv_literal(cell) for cell in row] for row in rows]
            expected.append(rows)
            expected_formulas.extend(
                cell.value for row in sheet.rows for cell in row if isinstance(cell, FormulaCell)
            )
        if (
            expected != result.sheets
            or spec.format == "xlsx"
            and expected_formulas != result.formulas
        ):
            raise ArtifactError("Spreadsheet semantic readback failed")
        return
    if spec.format == "pptx":
        slides = _slides(spec)
        if result.summary["slides"] != len(slides):
            raise ArtifactError("Presentation slide readback failed")
        expected_text = [
            text for slide in slides for text in [slide.title, slide.body, *slide.bullets] if text
        ]
        expected_tables = [
            [table.headers, *table.rows] for slide in slides for table in slide.tables
        ]
        if expected_tables != result.tables:
            raise ArtifactError("Presentation table readback failed")
        if [slide.notes for slide in slides if slide.notes] != result.notes:
            raise ArtifactError("Presentation notes readback failed")
    else:
        expected_text = [
            spec.title,
            *[text for block in spec.blocks for text in _block_text(block)],
        ]
        if spec.format == "docx":
            expected_tables = [
                [block.headers, *block.rows]
                for block in spec.blocks
                if isinstance(block, TableBlock)
            ]
            if expected_tables != result.tables:
                raise ArtifactError("Document table readback failed")
    actual = _normalize(
        "\n".join(result.texts + [text for table in result.tables for row in table for text in row])
    )
    for text in expected_text:
        # Markdown source deliberately escapes punctuation; compare after unescaping.
        normalized = _normalize(text)
        if spec.format == "markdown":
            normalized = _normalize(_markdown_text(text))
        if normalized and normalized not in actual:
            raise ArtifactError("Artifact text semantic readback failed")
    if spec.format in {"docx", "pdf", "pptx"} and result.summary.get("title") != spec.title:
        raise ArtifactError("Artifact metadata readback failed")
