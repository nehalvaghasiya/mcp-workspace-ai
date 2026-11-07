from __future__ import annotations

from typing import Literal

from mcp_documents.schemas.strict_model import StrictModel
from mcp_documents.schemas.text import Text


class ParagraphBlock(StrictModel):
    type: Literal["paragraph"]
    text: Text
