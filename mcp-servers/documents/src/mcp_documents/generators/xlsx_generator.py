from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

from mcp_documents.schemas.artifact_spec import ArtifactSpec
from mcp_documents.schemas.date_cell import DateCell
from mcp_documents.schemas.string_cell import StringCell
from mcp_documents.utils.conversion import _sheets


def _render_xlsx(spec: ArtifactSpec, path: Path) -> None:
    workbook = Workbook()
    workbook.remove(workbook.active)
    workbook.properties.title = spec.title
    workbook.properties.creator = spec.metadata.get("author", "MCP Workspace AI")
    for sheet_spec in _sheets(spec):
        sheet = workbook.create_sheet(sheet_spec.name)
        for column, header in enumerate(sheet_spec.columns, 1):
            cell = sheet.cell(1, column, header)
            cell.data_type = "s"
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(
                "solid", fgColor="244563" if spec.template == "simple" else "305E89"
            )
            sheet.column_dimensions[get_column_letter(column)].width = min(
                45, max(16, len(header) + 4)
            )
        for row_index, row in enumerate(sheet_spec.rows, 2):
            for column, value in enumerate(row, 1):
                cell = sheet.cell(row_index, column, value.value)
                if isinstance(value, StringCell):
                    cell.data_type = "s"
                elif isinstance(value, DateCell):
                    cell.number_format = "yyyy-mm-dd"
        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = sheet.dimensions
    workbook.save(path)
    workbook.close()
