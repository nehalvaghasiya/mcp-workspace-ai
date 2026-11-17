from typing import Any

from mcp.server import MCPServer
from mcp_workspace_common.contracts import ToolDefinition
from mcp_workspace_common.execution.server_context import ServerContext
from mcp_workspace_common.server import build_server

from mcp_slides.tools.create_presentation import definition as create_presentation
from mcp_slides.tools.get_presentation import definition as get_presentation
from mcp_slides.tools.update_presentation import definition as update_presentation


def tool_definitions() -> dict[str, ToolDefinition]:
    return {
        item.name: item
        for item in (get_presentation(), create_presentation(), update_presentation())
    }


def create_server(runtime: ServerContext) -> MCPServer[Any]:
    return build_server("slides", tool_definitions(), runtime)
