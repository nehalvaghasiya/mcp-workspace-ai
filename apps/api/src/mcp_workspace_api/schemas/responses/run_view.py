from typing import Literal

from mcp_workspace_api.contracts import StrictModel

RunStatus = Literal[
    "queued", "running", "needs_approval", "completed", "failed", "cancelled", "interrupted"
]


class RunView(StrictModel):
    id: str
    conversation_id: str
    status: RunStatus
    error: str | None
