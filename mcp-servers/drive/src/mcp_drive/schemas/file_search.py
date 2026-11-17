from __future__ import annotations

from mcp_workspace_common.schemas.search import Search
from pydantic import Field


class FileSearch(Search):
    mime_types: list[str] = Field(default_factory=list, max_length=10)
    parent_id: str | None = None
    drive_id: str | None = Field(default=None, min_length=1, max_length=256)
