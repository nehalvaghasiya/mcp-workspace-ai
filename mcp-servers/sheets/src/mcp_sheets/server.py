from typing import Any

from mcp.server import MCPServer
from mcp_workspace_common.contracts import ToolDefinition
from mcp_workspace_common.execution.server_context import ServerContext
from mcp_workspace_common.server import build_server

from mcp_sheets.tools.add_chart import definition as add_chart
from mcp_sheets.tools.add_sheet import definition as add_sheet
from mcp_sheets.tools.append_rows import definition as append_rows
from mcp_sheets.tools.create_spreadsheet import definition as create_spreadsheet
from mcp_sheets.tools.format_range import definition as format_range
from mcp_sheets.tools.get_spreadsheet import definition as get_spreadsheet
from mcp_sheets.tools.read_range import definition as read_range
from mcp_sheets.tools.write_range import definition as write_range


def tool_definitions() -> dict[str, ToolDefinition]:
    return {
        item.name: item
        for item in (
            get_spreadsheet(),
            read_range(),
            create_spreadsheet(),
            write_range(),
            append_rows(),
            format_range(),
            add_chart(),
            add_sheet(),
        )
    }


def create_server(runtime: ServerContext) -> MCPServer[Any]:
    return build_server("sheets", tool_definitions(), runtime)
