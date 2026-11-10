from __future__ import annotations

from pydantic import Field

from mcp_workspace_api.contracts import StrictModel
from mcp_workspace_api.db import (
    uid,
)


class NewMessage(StrictModel):
    content: str = Field(min_length=1, max_length=8000)
    request_id: str = Field(default_factory=uid, max_length=100)
