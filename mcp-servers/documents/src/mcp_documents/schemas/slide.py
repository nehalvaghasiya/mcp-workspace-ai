from __future__ import annotations

import textwrap
from typing import Annotated

from pydantic import AfterValidator, Field, model_validator

from mcp_documents.schemas.strict_model import StrictModel
from mcp_documents.schemas.table_block import TableBlock
from mcp_documents.schemas.text import Text
from mcp_documents.utils.text import _plain_text


class Slide(StrictModel):
    title: Annotated[str, Field(min_length=1, max_length=120), AfterValidator(_plain_text)]
    body: Annotated[str, Field(max_length=1_500), AfterValidator(_plain_text)] = ""
    bullets: list[Annotated[str, Field(max_length=240), AfterValidator(_plain_text)]] = Field(
        default_factory=list, max_length=8
    )
    tables: list[TableBlock] = Field(default_factory=list, max_length=1)
    notes: Text | None = None

    @model_validator(mode="after")
    def fits_slide(self) -> Slide:
        if len(self.body) + sum(map(len, self.bullets)) > 2_000:
            raise ValueError("Slide body exceeds supported layout capacity")
        if self.body.count("\n") + sum(item.count("\n") + 1 for item in self.bullets) > 18:
            raise ValueError("Slide has too many explicit lines for its layout")
        for table in self.tables:
            if len(table.rows) > 8 or len(table.headers) > 6:
                raise ValueError("Slide tables support at most 8 rows and 6 columns")
            if any(len(cell) > 80 for row in [table.headers, *table.rows] for cell in row):
                raise ValueError("Slide table cells support at most 80 characters")
            if len(self.body) + sum(map(len, self.bullets)) > 500:
                raise ValueError("Text above a slide table must be concise")
            characters_per_line = max(12, 140 // len(table.headers))
            lines = sum(
                max(max(1, len(textwrap.wrap(cell, characters_per_line))) for cell in row)
                for row in [table.headers, *table.rows]
            )
            if lines > 14:
                raise ValueError("Slide table text exceeds supported layout capacity")
        return self
