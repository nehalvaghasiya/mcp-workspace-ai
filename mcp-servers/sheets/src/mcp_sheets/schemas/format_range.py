from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from mcp_sheets.schemas.range_request import RangeRequest


class FormatRange(RangeRequest):
    bold: bool | None = None
    italic: bool | None = None
    background_color: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
    number_format: Literal["NUMBER", "DATE", "CURRENCY", "PERCENT", "TEXT"] | None = None

    @model_validator(mode="after")
    def meaningful(self) -> FormatRange:
        if all(
            value is None
            for value in (self.bold, self.italic, self.background_color, self.number_format)
        ):
            raise ValueError("Provide at least one formatting change")
        return self
