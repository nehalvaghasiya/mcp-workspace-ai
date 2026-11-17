from __future__ import annotations

from pydantic import Field

from mcp_drive.schemas.file_id import FileId


class RenameFile(FileId):
    name: str = Field(min_length=1, max_length=200)
