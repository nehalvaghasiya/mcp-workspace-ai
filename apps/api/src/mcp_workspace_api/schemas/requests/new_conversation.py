from __future__ import annotations

from pydantic import Field

from mcp_workspace_api.contracts import StrictModel


class NewConversation(StrictModel):
    title: str = Field(default="New conversation", min_length=1, max_length=200)
