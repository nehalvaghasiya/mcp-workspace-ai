from __future__ import annotations

from typing import Annotated

from mcp_documents.schemas.slide import Slide
from pydantic import Field, model_validator

from mcp_slides.schemas.presentation_id import PresentationId
from mcp_slides.schemas.shape_text import ShapeText
from mcp_slides.schemas.text_replacement import TextReplacement

ObjectId = Annotated[str, Field(min_length=5, max_length=200, pattern=r"^[A-Za-z0-9_:-]+$")]


class UpdatePresentation(PresentationId):
    replace_text: list[TextReplacement] = Field(default_factory=list, max_length=100)
    shape_text: list[ShapeText] = Field(default_factory=list, max_length=100)
    append_slides: list[Slide] = Field(default_factory=list, max_length=40)
    delete_slide_ids: list[ObjectId] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def meaningful(self) -> UpdatePresentation:
        if not any((self.replace_text, self.shape_text, self.append_slides, self.delete_slide_ids)):
            raise ValueError("Provide a supported presentation change")
        if len(self.model_dump_json().encode()) > 500000:
            raise ValueError("Presentation changes exceed 500000 bytes")
        return self
