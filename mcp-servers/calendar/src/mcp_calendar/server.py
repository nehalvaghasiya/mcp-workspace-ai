from __future__ import annotations

from typing import Any

from mcp.server import MCPServer
from mcp_workspace_common.contracts import ToolDefinition
from mcp_workspace_common.execution.server_context import ServerContext
from mcp_workspace_common.server import build_server

from mcp_calendar.tools.check_availability import definition as check_availability
from mcp_calendar.tools.create_event import definition as create_event
from mcp_calendar.tools.delete_event import definition as delete_event
from mcp_calendar.tools.get_event import definition as get_event
from mcp_calendar.tools.list_calendars import definition as list_calendars
from mcp_calendar.tools.list_events import definition as list_events
from mcp_calendar.tools.update_event import definition as update_event


def tool_definitions() -> dict[str, ToolDefinition]:
    return {
        item.name: item
        for item in [
            list_calendars(),
            list_events(),
            get_event(),
            check_availability(),
            create_event(),
            update_event(),
            delete_event(),
        ]
    }


def create_server(runtime: ServerContext) -> MCPServer[Any]:
    return build_server("calendar", tool_definitions(), runtime)
