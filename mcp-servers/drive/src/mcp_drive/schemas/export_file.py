from __future__ import annotations

from typing import Literal

from mcp_drive.schemas.file_id import FileId


class ExportFile(FileId):
    mime_type: Literal[
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "text/csv",
        "text/plain",
    ] = "application/pdf"
