from __future__ import annotations

from mcp_workspace_common.schemas.strict_model import StrictModel
from pydantic import Field


class Folder(StrictModel):
    folder_id: str = "root"
    max_results: int = Field(default=20, ge=1, le=50)
    page_token: str | None = None
    drive_id: str | None = Field(default=None, min_length=1, max_length=256)
