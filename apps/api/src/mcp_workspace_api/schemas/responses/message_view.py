from typing import Literal

from mcp_workspace_api.contracts import SourceRef, StrictModel
from mcp_workspace_api.schemas.responses.artifact_view import ArtifactView


class MessageView(StrictModel):
    id: str
    role: Literal["user", "assistant"]
    content: str
    sources: list[SourceRef]
    artifacts: list[ArtifactView]
