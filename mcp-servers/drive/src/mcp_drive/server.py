from __future__ import annotations

from typing import Any

from mcp.server import MCPServer
from mcp_workspace_common.contracts import ToolDefinition
from mcp_workspace_common.execution.server_context import ServerContext
from mcp_workspace_common.server import build_server

from mcp_drive.tools.copy_file import definition as copy_file
from mcp_drive.tools.create_folder import definition as create_folder
from mcp_drive.tools.export_file import definition as export_file
from mcp_drive.tools.find_operation import definition as find_operation
from mcp_drive.tools.get_file_metadata import definition as get_file_metadata
from mcp_drive.tools.list_drives import definition as list_drives
from mcp_drive.tools.list_files import definition as list_files
from mcp_drive.tools.move_file import definition as move_file
from mcp_drive.tools.read_file import definition as read_file
from mcp_drive.tools.rename_file import definition as rename_file
from mcp_drive.tools.search_files import definition as search_files
from mcp_drive.tools.share_file import definition as share_file
from mcp_drive.tools.trash_file import definition as trash_file
from mcp_drive.tools.upload_file import definition as upload_file

LIVE_ONLY_TOOLS = {
    "drive.find_operation",
    "drive.list_drives",
    "drive.rename_file",
    "drive.copy_file",
    "drive.trash_file",
    "drive.share_file",
    "drive.move_file",
    "drive.export_file",
}


def tool_definitions(include_live: bool = False) -> dict[str, ToolDefinition]:
    definitions = [
        search_files(),
        get_file_metadata(),
        read_file(),
        list_files(),
        upload_file(),
        create_folder(),
    ]
    if include_live:
        definitions.extend(
            [
                list_drives(),
                find_operation(),
                export_file(),
                copy_file(),
                rename_file(),
                move_file(),
                share_file(),
                trash_file(),
            ]
        )
    return {item.name: item for item in definitions}


def create_server(runtime: ServerContext) -> MCPServer[Any]:
    return build_server(
        "drive", tool_definitions(include_live=runtime.settings.mode == "live"), runtime
    )
