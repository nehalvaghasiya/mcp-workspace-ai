from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from mcp_workspace_common.hashing import digest
from mcp_workspace_common.schemas.risk import Risk
from mcp_workspace_common.schemas.tool_result import ToolResult


class ToolDefinition(BaseModel):
    name: str
    description: str
    input_model: Any
    risk: Risk = Risk.READ
    scopes: tuple[str, ...] = ()

    @property
    def server(self) -> str:
        return self.name.split(".")[0]

    @property
    def digest(self) -> str:
        return digest(
            {
                "name": self.name,
                "input": self.input_model.model_json_schema(),
                "output": ToolResult.model_json_schema(),
                "risk": self.risk,
                "scopes": self.scopes,
            }
        )
