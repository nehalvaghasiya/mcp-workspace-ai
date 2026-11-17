from typing import Literal

from pydantic import Field

from mcp_workspace_api.contracts import SourceRef, StrictModel

RunStatus = Literal[
    "queued", "running", "needs_approval", "completed", "failed", "cancelled", "interrupted"
]


class RunView(StrictModel):
    id: str
    conversation_id: str
    status: RunStatus
    error: str | None
    error_code: str | None = None
    retryable: bool = False
    retry_of: str | None = None
    read_count: int = 0
    selected_count: int | None = None
    sources: list[SourceRef] = Field(default_factory=list)
