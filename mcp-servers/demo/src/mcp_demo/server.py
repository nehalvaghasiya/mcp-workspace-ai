from __future__ import annotations

from typing import Any

from mcp.server import MCPServer
from mcp_workspace_common.contracts import ToolDefinition
from mcp_workspace_common.execution.server_context import ServerContext
from mcp_workspace_common.server import build_server

from mcp_demo.tools.ping import definition as ping


def tool_definitions() -> dict[str, ToolDefinition]:
    return {item.name: item for item in [ping()]}


def create_server(runtime: ServerContext) -> MCPServer[Any]:
    return build_server("demo", tool_definitions(), runtime)
