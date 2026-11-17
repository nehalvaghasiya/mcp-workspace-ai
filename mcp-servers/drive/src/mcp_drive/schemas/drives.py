from __future__ import annotations

from mcp_workspace_common.schemas.strict_model import StrictModel
from pydantic import Field


class Drives(StrictModel):
    max_results: int = Field(default=20, ge=1, le=100)
    page_token: str | None = Field(default=None, max_length=2048)
