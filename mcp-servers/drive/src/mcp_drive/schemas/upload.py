from __future__ import annotations

from mcp_workspace_common.schemas.strict_model import StrictModel
from pydantic import Field


class Upload(StrictModel):
    artifact_id: str
    folder_id: str | None = None
    target_name: str | None = Field(default=None, max_length=200)
