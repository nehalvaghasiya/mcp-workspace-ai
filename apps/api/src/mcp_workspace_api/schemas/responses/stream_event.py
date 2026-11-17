from typing import Literal

from pydantic import Field, JsonValue

from mcp_workspace_api.contracts import StrictModel


class StreamEvent(StrictModel):
    id: int = Field(ge=1)
    run_id: str
    type: Literal[
        "run.started",
        "tool.started",
        "tool.completed",
        "approval.required",
        "message.delta",
        "run.completed",
        "run.failed",
        "run.cancelled",
        "model.usage",
        "model.started",
        "model.completed",
        "model.failed",
    ]
    data: dict[str, JsonValue]
