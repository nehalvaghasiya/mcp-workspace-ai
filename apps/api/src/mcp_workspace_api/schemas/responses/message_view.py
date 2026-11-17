from typing import Literal

from pydantic import Field

from mcp_workspace_api.contracts import SourceRef, StrictModel
from mcp_workspace_api.schemas.responses.artifact_view import ArtifactView
from mcp_workspace_api.schemas.responses.workspace_file_view import WorkspaceFileView


class MessageView(StrictModel):
    id: str
    role: Literal["user", "assistant"]
    content: str
    sources: list[SourceRef]
    artifacts: list[ArtifactView]
    workspace_files: list[WorkspaceFileView] = Field(default_factory=list)
