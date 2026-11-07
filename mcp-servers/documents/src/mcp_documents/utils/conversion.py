from __future__ import annotations

from mcp_documents.constants import MAX_ROWS, MAX_SLIDES
from mcp_documents.exceptions.artifact_error import ArtifactError
from mcp_documents.schemas.artifact_spec import ArtifactSpec
from mcp_documents.schemas.bullet_list import BulletList
from mcp_documents.schemas.date_cell import DateCell
from mcp_documents.schemas.heading import Heading
from mcp_documents.schemas.number_cell import NumberCell
from mcp_documents.schemas.report_block import ReportBlock
from mcp_documents.schemas.sheet import Sheet
from mcp_documents.schemas.slide import Slide
from mcp_documents.schemas.spreadsheet_cell import SpreadsheetCell
from mcp_documents.schemas.string_cell import StringCell
from mcp_documents.schemas.table_block import TableBlock


def _block_text(block: ReportBlock) -> list[str]:
    if isinstance(block, TableBlock):
        return [text for row in [block.headers, *block.rows] for text in row]
    if isinstance(block, BulletList):
        return block.items
    return [block.text]


def _sheets(spec: ArtifactSpec) -> list[Sheet]:
    if spec.sheets:
        return spec.sheets
    # Report-to-sheet conversion preserves every report fact as literal text.
    lines = [spec.title, *[text for block in spec.blocks for text in _block_text(block)]]
    if len(lines) > MAX_ROWS:
        raise ArtifactError("Report exceeds spreadsheet row limit")
    return [
        Sheet(
            name="Report",
            columns=["Content"],
            rows=[[StringCell(type="string", value=line)] for line in lines],
        )
    ]


def _slides(spec: ArtifactSpec) -> list[Slide]:
    if spec.slides:
        return spec.slides
    slides = [Slide(title=spec.title[:120], body=spec.title if len(spec.title) > 120 else "")]
    for block in spec.blocks:
        if isinstance(block, TableBlock):
            slides.append(Slide(title="Table", tables=[block]))
        elif isinstance(block, Heading):
            slides.append(
                Slide(title=block.text[:120], body=block.text if len(block.text) > 120 else "")
            )
        else:
            text = "\n".join(_block_text(block))
            for offset in range(0, len(text), 1_200):
                slides.append(Slide(title=spec.title[:120], body=text[offset : offset + 1_200]))
    if len(slides) > MAX_SLIDES:
        raise ArtifactError("Report exceeds presentation slide limit")
    return slides


def _cell_text(cell: SpreadsheetCell) -> str:
    if isinstance(cell, DateCell):
        return cell.value.isoformat()
    if isinstance(cell, NumberCell):
        return format(cell.value, ".15g")
    return cell.value
