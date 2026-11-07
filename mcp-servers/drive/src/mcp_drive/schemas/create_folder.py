from __future__ import annotations

from mcp_workspace_common.schemas.strict_model import StrictModel
from pydantic import Field


class CreateFolder(StrictModel):
    name: str = Field(min_length=1, max_length=200)
    parent_id: str | None = None
