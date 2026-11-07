from __future__ import annotations

from typing import Literal

from pydantic import Field

from mcp_documents.schemas.strict_model import StrictModel


class NumberCell(StrictModel):
    type: Literal["number"]
    value: float = Field(allow_inf_nan=False)
