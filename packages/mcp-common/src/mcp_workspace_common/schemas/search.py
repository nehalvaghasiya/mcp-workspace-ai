from __future__ import annotations

from pydantic import Field

from mcp_workspace_common.schemas.strict_model import StrictModel


class Search(StrictModel):
    query: str = Field(min_length=1, max_length=1000)
    max_results: int = Field(default=10, ge=1, le=50)
    page_token: str | None = Field(default=None, max_length=200)
