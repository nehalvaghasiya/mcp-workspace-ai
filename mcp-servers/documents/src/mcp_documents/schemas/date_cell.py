from __future__ import annotations

from datetime import date
from typing import Literal

from mcp_documents.schemas.strict_model import StrictModel


class DateCell(StrictModel):
    type: Literal["date"]
    value: date
