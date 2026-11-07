from __future__ import annotations

from mcp_workspace_common.schemas.strict_model import StrictModel
from pydantic import Field


class FileId(StrictModel):
    file_id: str = Field(min_length=1, max_length=256)
    resource_key: str | None = Field(default=None, max_length=256, pattern=r"^[A-Za-z0-9_-]+$")
