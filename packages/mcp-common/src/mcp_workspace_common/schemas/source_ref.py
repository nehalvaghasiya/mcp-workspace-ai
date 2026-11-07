from __future__ import annotations

from mcp_workspace_common.schemas.strict_model import StrictModel


class SourceRef(StrictModel):
    provider: str
    resource_id: str
    title: str
    url: str | None = None
    retrieved_at: str
    snippet: str = ""
    pointer: str = ""
