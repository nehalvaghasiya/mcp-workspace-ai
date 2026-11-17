from __future__ import annotations

from mcp_workspace_common.schemas.strict_model import StrictModel
from pydantic import Field


class Attachment(StrictModel):
    message_id: str = Field(min_length=1, max_length=256)
    attachment_id: str = Field(min_length=1, max_length=256)
    max_chars: int = Field(default=20000, ge=1, le=100000)
