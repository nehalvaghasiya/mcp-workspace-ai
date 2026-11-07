from __future__ import annotations

from typing import Literal

from pydantic import Field

from mcp_drive.schemas.file_id import FileId


class ReadFile(FileId):
    max_chars: int = Field(default=20000, ge=1, le=20000)
    extraction_mode: Literal["text"] = "text"
