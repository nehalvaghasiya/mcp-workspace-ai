from __future__ import annotations

from pydantic import Field

from mcp_drive.schemas.file_id import FileId


class CopyFile(FileId):
    name: str = Field(min_length=1, max_length=200)
    folder_id: str | None = Field(default=None, min_length=1, max_length=256)
