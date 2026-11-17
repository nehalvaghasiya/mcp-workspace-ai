from typing import Literal

from pydantic import Field

from mcp_sheets.schemas.range_request import RangeRequest


class AddChart(RangeRequest):
    title: str = Field(min_length=1, max_length=200)
    chart_type: Literal["COLUMN", "BAR", "LINE", "AREA"] = "COLUMN"
    header_rows: int = Field(default=1, ge=0, le=1)
    anchor_row: int = Field(default=0, ge=0, le=999999)
    anchor_column: int = Field(default=0, ge=0, le=16383)
