from __future__ import annotations

from typing import Literal

from pydantic import Field

from mcp_documents.schemas.strict_model import StrictModel
from mcp_documents.schemas.text import Label


class Heading(StrictModel):
    type: Literal["heading"]
    text: Label
    level: int = Field(default=1, ge=1, le=3)
