from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from mcp_workspace_api.contracts import (
    ToolDefinition,
    ToolResult,
)
from mcp_workspace_api.core.security import Denied
from mcp_workspace_api.db import (
    User,
)

if TYPE_CHECKING:
    from mcp_workspace_api.core.execution_context import Runtime


class ToolAdapter:
    def __init__(self, context: Runtime) -> None:
        self.context = context

    def validate_arguments(
        self, user_id: str, definition: ToolDefinition, arguments: dict[str, Any]
    ) -> BaseModel:
        context = self.context
        if "timezone" in definition.input_model.model_fields and "timezone" not in arguments:
            with context.db.session() as session:
                user = session.get(User, user_id)
                if user and not user.deleted:
                    arguments = {**arguments, "timezone": user.timezone}
        return definition.input_model.model_validate(arguments)

    async def invoke(
        self,
        user_id: str,
        name: str,
        arguments: dict[str, Any],
        run_id: str = "",
        approval: dict[str, str] | None = None,
    ) -> ToolResult:
        context = self.context
        definition = context.tools.get(name)
        if not definition:
            raise Denied("PERMISSION_DENIED", "Unknown tool")
        context.policy.authorize(user_id, definition)
        parsed = context.validate_arguments(user_id, definition, arguments)
        async with context.client(
            user_id, definition.server, run_id=run_id, approval=approval, tools=[name]
        ) as client:
            result = await client.call_tool(name, {"request": parsed.model_dump(mode="json")})
            if result.is_error:
                raise Denied("MCP_TRANSPORT_ERROR", "The MCP server rejected this request")
            return ToolResult.model_validate(result.structured_content)
