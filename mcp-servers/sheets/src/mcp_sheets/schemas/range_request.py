from __future__ import annotations

from pydantic import Field, field_validator

from mcp_sheets.providers.ranges import parse_range
from mcp_sheets.schemas.spreadsheet_id import SpreadsheetId


class RangeRequest(SpreadsheetId):
    range: str = Field(min_length=1, max_length=200)

    @field_validator("range")
    @classmethod
    def bounded_range(cls, value: str) -> str:
        parse_range(value)
        return value
