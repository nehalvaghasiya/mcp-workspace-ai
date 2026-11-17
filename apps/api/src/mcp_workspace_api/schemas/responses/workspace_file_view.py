from typing import Literal

from mcp_workspace_api.contracts import StrictModel


class WorkspaceFileView(StrictModel):
    id: str
    google_file_id: str
    kind: Literal["docs", "sheets", "slides"]
    title: str
    mime_type: str
    web_url: str
    revision: str
    status: Literal["ready", "partial", "unverified"]
    artifact_id: str | None = None
    run_id: str | None = None
    created_at: str
    updated_at: str
