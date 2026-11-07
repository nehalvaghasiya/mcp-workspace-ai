from __future__ import annotations

import re
from typing import Annotated

from pydantic import AfterValidator, Field, model_validator

from mcp_documents.constants import MAX_ROWS
from mcp_documents.schemas.spreadsheet_cell import SpreadsheetCell
from mcp_documents.schemas.strict_model import StrictModel
from mcp_documents.schemas.text import Label
from mcp_documents.utils.text import _plain_text


class Sheet(StrictModel):
    name: Annotated[str, Field(min_length=1, max_length=31), AfterValidator(_plain_text)]
    columns: list[Label] = Field(min_length=1, max_length=50)
    rows: list[list[SpreadsheetCell]] = Field(default_factory=list, max_length=MAX_ROWS)

    @model_validator(mode="after")
    def valid_sheet(self) -> Sheet:
        if (
            re.search(r"[\[\]:*?/\\]", self.name)
            or self.name.startswith("'")
            or self.name.endswith("'")
        ):
            raise ValueError("Unsafe worksheet name")
        if any(len(row) != len(self.columns) for row in self.rows):
            raise ValueError("Every sheet row must match its columns")
        return self
