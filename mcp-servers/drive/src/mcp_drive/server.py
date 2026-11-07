from __future__ import annotations

from typing import Any

from mcp.server import MCPServer
from mcp_workspace_common.contracts import ToolDefinition
from mcp_workspace_common.execution.server_context import ServerContext
from mcp_workspace_common.server import build_server

from mcp_drive.tools.create_folder import definition as create_folder
from mcp_drive.tools.get_file_metadata import definition as get_file_metadata
from mcp_drive.tools.list_files import definition as list_files
from mcp_drive.tools.read_file import definition as read_file
from mcp_drive.tools.search_files import definition as search_files
from mcp_drive.tools.upload_file import definition as upload_file


def tool_definitions() -> dict[str, ToolDefinition]:
    return {
        item.name: item
        for item in [
            search_files(),
            get_file_metadata(),
            read_file(),
            list_files(),
            upload_file(),
            create_folder(),
        ]
    }


def create_server(runtime: ServerContext) -> MCPServer[Any]:
    return build_server("drive", tool_definitions(), runtime)
