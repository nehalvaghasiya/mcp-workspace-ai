from __future__ import annotations

from typing import Literal

from pydantic import Field

from mcp_drive.schemas.file_id import FileId


class ShareFile(FileId):
    email: str = Field(min_length=3, max_length=320, pattern=r"^[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+$")
    role: Literal["reader", "commenter", "writer"] = "reader"
    send_notification: bool = True
