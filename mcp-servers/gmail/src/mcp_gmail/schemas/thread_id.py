from __future__ import annotations

from mcp_workspace_common.schemas.strict_model import StrictModel
from pydantic import Field


class ThreadId(StrictModel):
    thread_id: str = Field(min_length=1, max_length=256)
    max_messages: int = Field(default=20, ge=1, le=50)
