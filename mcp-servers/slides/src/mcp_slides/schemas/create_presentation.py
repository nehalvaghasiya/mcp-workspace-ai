from __future__ import annotations

from mcp_documents.schemas.slide import Slide
from mcp_workspace_common.schemas.strict_model import StrictModel
from pydantic import Field, model_validator


class CreatePresentation(StrictModel):
    title: str = Field(min_length=1, max_length=200)
    parent_id: str | None = Field(default=None, max_length=200, pattern=r"^[A-Za-z0-9_-]+$")
    slides: list[Slide] = Field(min_length=1, max_length=40)

    @model_validator(mode="after")
    def bounded(self) -> CreatePresentation:
        if len(self.model_dump_json().encode()) > 500000:
            raise ValueError("Presentation content exceeds 500000 bytes")
        return self
