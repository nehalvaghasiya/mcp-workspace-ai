from pydantic import Field

from mcp_sheets.schemas.spreadsheet_id import SpreadsheetId


class AddSheet(SpreadsheetId):
    title: str = Field(min_length=1, max_length=31, pattern=r"^[^\[\]:*?/\\]+$")
    row_count: int = Field(default=1000, ge=1, le=10000)
    column_count: int = Field(default=26, ge=1, le=100)
