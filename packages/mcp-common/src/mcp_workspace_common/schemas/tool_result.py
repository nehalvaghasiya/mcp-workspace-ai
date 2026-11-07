from __future__ import annotations

from typing import Literal

from pydantic import Field, JsonValue

from mcp_workspace_common.schemas.source_ref import SourceRef
from mcp_workspace_common.schemas.strict_model import StrictModel


class ToolResult(StrictModel):
    status: Literal["success", "error"] = "success"
    data: dict[str, JsonValue] = Field(default_factory=dict)
    sources: list[SourceRef] = Field(default_factory=list)
    has_more: bool = False
    next_page_token: str | None = None
    warnings: list[str] = Field(default_factory=list)
    operation_id: str = ""
    code: str | None = None
