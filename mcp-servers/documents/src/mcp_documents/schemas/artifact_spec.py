from __future__ import annotations

from typing import Annotated, Literal

from pydantic import AfterValidator, Field, model_validator

from mcp_documents.constants import MAX_ROWS, MAX_SLIDES, MAX_SPEC_BYTES, ArtifactFormat, Template
from mcp_documents.schemas.report_block import ReportBlock
from mcp_documents.schemas.sheet import Sheet
from mcp_documents.schemas.slide import Slide
from mcp_documents.schemas.strict_model import StrictModel
from mcp_documents.schemas.table_block import TableBlock
from mcp_documents.schemas.text import Label
from mcp_documents.utils.text import _plain_text


class ArtifactSpec(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    format: ArtifactFormat
    title: Label
    template: Template = "simple"
    metadata: dict[Label, Annotated[str, Field(max_length=1_000), AfterValidator(_plain_text)]] = (
        Field(default_factory=dict, max_length=16)
    )
    blocks: list[ReportBlock] = Field(default_factory=list, max_length=100)
    sheets: list[Sheet] = Field(default_factory=list, max_length=10)
    slides: list[Slide] = Field(default_factory=list, max_length=MAX_SLIDES)

    @model_validator(mode="after")
    def bounded(self) -> ArtifactSpec:
        if len(self.model_dump_json().encode("utf-8")) > MAX_SPEC_BYTES:
            raise ValueError("Artifact specification exceeds 500000 bytes")
        names = [sheet.name.casefold() for sheet in self.sheets]
        if len(names) != len(set(names)):
            raise ValueError("Worksheet names must be unique, ignoring case")
        if sum(len(sheet.rows) * len(sheet.columns) for sheet in self.sheets) > 20_000:
            raise ValueError("Artifact supports at most 20000 spreadsheet cells")
        if (
            sum(len(block.rows) for block in self.blocks if isinstance(block, TableBlock))
            > MAX_ROWS
        ):
            raise ValueError("Artifact supports at most 1000 report table rows")
        if self.format == "csv" and len(self.sheets) > 1:
            raise ValueError("CSV supports one worksheet")
        if self.sheets and self.format not in {"xlsx", "csv"}:
            raise ValueError("Worksheets require XLSX or CSV format")
        if self.slides and self.format != "pptx":
            raise ValueError("Slides require PPTX format")
        if self.slides and self.blocks or self.sheets and self.blocks:
            raise ValueError("Choose report blocks or format-specific content")
        return self
