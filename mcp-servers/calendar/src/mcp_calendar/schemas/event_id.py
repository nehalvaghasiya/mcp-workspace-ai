from __future__ import annotations

from mcp_workspace_common.schemas.strict_model import StrictModel
from pydantic import Field


class EventId(StrictModel):
    calendar_id: str = "primary"
    event_id: str = Field(min_length=1, max_length=256)
