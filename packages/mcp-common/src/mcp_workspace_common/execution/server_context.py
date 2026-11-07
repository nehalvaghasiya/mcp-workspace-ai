from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel

from mcp_workspace_common.contracts import ToolDefinition, ToolResult
from mcp_workspace_common.security import Signer


class ServerContext(Protocol):
    signer: Signer
    settings: Any
    tools: dict[str, ToolDefinition]

    def user_available(self, user_id: str) -> bool: ...
    async def execute(self, name: str, request: BaseModel) -> ToolResult: ...
