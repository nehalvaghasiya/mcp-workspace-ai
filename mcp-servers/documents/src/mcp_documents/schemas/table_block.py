from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from mcp_documents.constants import MAX_ROWS
from mcp_documents.schemas.strict_model import StrictModel
from mcp_documents.schemas.text import Label, TableText


class TableBlock(StrictModel):
    type: Literal["table"]
    headers: list[Label] = Field(min_length=1, max_length=20)
    rows: list[list[TableText]] = Field(default_factory=list, max_length=MAX_ROWS)

    @model_validator(mode="after")
    def rectangular(self) -> TableBlock:
        if any(len(row) != len(self.headers) for row in self.rows):
            raise ValueError("Every table row must match its headers")
        return self
