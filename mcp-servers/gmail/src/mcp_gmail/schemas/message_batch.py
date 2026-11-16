from typing import Literal

from mcp_workspace_common.contracts import StrictModel
from pydantic import Field


class MessageBatch(StrictModel):
    message_ids: list[str] = Field(min_length=1, max_length=20)
    format: Literal["full", "text"] = "full"
