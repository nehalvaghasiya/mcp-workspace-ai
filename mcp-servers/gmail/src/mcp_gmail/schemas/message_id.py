from __future__ import annotations

from typing import Literal

from mcp_workspace_common.schemas.strict_model import StrictModel
from pydantic import Field


class MessageId(StrictModel):
    message_id: str = Field(min_length=1, max_length=256)
    format: Literal["full", "metadata", "text"] = "full"
