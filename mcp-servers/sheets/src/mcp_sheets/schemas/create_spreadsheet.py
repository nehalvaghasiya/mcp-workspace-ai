from __future__ import annotations

from mcp_documents.schemas.sheet import Sheet
from mcp_workspace_common.schemas.strict_model import StrictModel
from pydantic import Field, model_validator


class CreateSpreadsheet(StrictModel):
    title: str = Field(min_length=1, max_length=200)
    parent_id: str | None = Field(default=None, max_length=200, pattern=r"^[A-Za-z0-9_-]+$")
    sheets: list[Sheet] = Field(min_length=1, max_length=10)

    @model_validator(mode="after")
    def bounded(self) -> CreateSpreadsheet:
        if len({sheet.name.casefold() for sheet in self.sheets}) != len(self.sheets):
            raise ValueError("Sheet names must be unique")
        if sum((len(sheet.rows) + 1) * len(sheet.columns) for sheet in self.sheets) > 20000:
            raise ValueError("Spreadsheet supports at most 20000 initial cells")
        if len(self.model_dump_json().encode()) > 500000:
            raise ValueError("Spreadsheet content exceeds 500000 bytes")
        return self
