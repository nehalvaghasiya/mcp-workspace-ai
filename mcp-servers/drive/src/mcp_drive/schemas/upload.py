from __future__ import annotations

from typing import Literal

from mcp_workspace_common.schemas.strict_model import StrictModel
from pydantic import Field


class Upload(StrictModel):
    artifact_id: str
    folder_id: str | None = None
    target_name: str | None = Field(default=None, max_length=200)
    convert_to_google_type: (
        Literal[
            "application/vnd.google-apps.document",
            "application/vnd.google-apps.spreadsheet",
            "application/vnd.google-apps.presentation",
        ]
        | None
    ) = None
