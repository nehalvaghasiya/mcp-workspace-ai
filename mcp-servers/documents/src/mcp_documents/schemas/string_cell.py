from __future__ import annotations

from typing import Literal

from mcp_documents.schemas.strict_model import StrictModel
from mcp_documents.schemas.text import TableText


class StringCell(StrictModel):
    type: Literal["string"]
    value: TableText
