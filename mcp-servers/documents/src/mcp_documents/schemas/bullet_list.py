from __future__ import annotations

from typing import Literal

from pydantic import Field

from mcp_documents.schemas.strict_model import StrictModel
from mcp_documents.schemas.text import Text


class BulletList(StrictModel):
    type: Literal["bullet_list"]
    items: list[Text] = Field(min_length=1, max_length=100)
