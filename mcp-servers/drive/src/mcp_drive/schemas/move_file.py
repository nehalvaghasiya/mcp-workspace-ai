from __future__ import annotations

from pydantic import Field

from mcp_drive.schemas.file_id import FileId


class MoveFile(FileId):
    folder_id: str = Field(min_length=1, max_length=256)
