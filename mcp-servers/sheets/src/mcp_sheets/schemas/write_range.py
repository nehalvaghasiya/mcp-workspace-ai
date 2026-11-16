from __future__ import annotations

import math
from typing import Annotated

from mcp_documents.schemas.spreadsheet_cell import SpreadsheetCell
from pydantic import Field, model_validator

from mcp_sheets.providers.ranges import parse_range
from mcp_sheets.schemas.range_request import RangeRequest

type CellValue = SpreadsheetCell | str | bool | Annotated[float, Field(allow_inf_nan=False)] | None


class WriteRange(RangeRequest):
    values: list[list[CellValue]] = Field(min_length=1, max_length=1000)

    @model_validator(mode="after")
    def bounded(self) -> WriteRange:
        _, start_row, end_row, start_col, end_col = parse_range(self.range)
        width = len(self.values[0])
        if not width or width > end_col - start_col or len(self.values) > end_row - start_row:
            raise ValueError("Values must fit inside the approved range")
        if any(len(row) != width for row in self.values):
            raise ValueError("Rows must have the same number of cells")
        if len(self.model_dump_json().encode()) > 500000:
            raise ValueError("Spreadsheet update exceeds 500000 bytes")
        for row in self.values:
            for cell in row:
                if isinstance(cell, float) and not math.isfinite(cell):
                    raise ValueError("Numeric cells must be finite")
                if isinstance(cell, str) and len(cell) > 50000:
                    raise ValueError("Cell text exceeds 50000 characters")
        return self
