from typing import Literal

from pydantic import JsonValue

from mcp_workspace_api.contracts import StrictModel


class ApprovalView(StrictModel):
    id: str
    run_id: str
    tool: str
    arguments: dict[str, JsonValue]
    summary: dict[str, JsonValue]
    status: Literal["pending", "approved", "rejected", "consumed", "expired", "revoked"]
    expires_at: str
    action_digest: str
