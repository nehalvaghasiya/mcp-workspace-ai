from typing import Any

from mcp.server import MCPServer
from mcp_workspace_common.contracts import ToolDefinition
from mcp_workspace_common.execution.server_context import ServerContext
from mcp_workspace_common.server import build_server

from mcp_google_docs.tools.create_document import definition as create_document
from mcp_google_docs.tools.get_document import definition as get_document
from mcp_google_docs.tools.update_document import definition as update_document


def tool_definitions() -> dict[str, ToolDefinition]:
    return {item.name: item for item in (get_document(), create_document(), update_document())}


def create_server(runtime: ServerContext) -> MCPServer[Any]:
    return build_server("docs", tool_definitions(), runtime)
