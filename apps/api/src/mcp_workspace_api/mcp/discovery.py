from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mcp_workspace_api.contracts import (
    digest,
)
from mcp_workspace_api.core.security import Denied

if TYPE_CHECKING:
    from mcp_workspace_api.core.execution_context import Runtime


class Discovery:
    def __init__(self, context: Runtime) -> None:
        self.context = context

    async def catalog(self, user_id: str) -> list[dict[str, Any]]:
        context = self.context
        catalog: list[dict[str, Any]] = []
        for server in ("gmail", "calendar", "drive", "artifact", "demo"):
            async with context.client(user_id, server) as client:
                discovered = await client.list_tools()
            for tool in discovered.tools:
                definition = context.tools.get(tool.name)
                if not definition:
                    raise Denied("TOOL_SCHEMA_CHANGED", "Server exposed an unregistered tool")
                schema = tool.input_schema
                current = digest(
                    {"input": schema, "output": tool.output_schema, "policy": definition.digest}
                )
                previous = context.schema_digests.setdefault(tool.name, current)
                if previous != current:
                    raise Denied(
                        "TOOL_SCHEMA_CHANGED",
                        "Tool schema changed; operator review is required",
                    )
                enabled = True
                try:
                    context.policy.authorize(user_id, definition)
                except Denied:
                    enabled = False
                catalog.append(
                    {
                        "name": tool.name,
                        "server": server,
                        "input_schema": schema,
                        "output_schema": tool.output_schema,
                        "risk": definition.risk,
                        "enabled": enabled,
                        "digest": current,
                        "description": definition.description,
                    }
                )
        return catalog
