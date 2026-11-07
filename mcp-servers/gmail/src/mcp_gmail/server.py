from __future__ import annotations

from typing import Any

from mcp.server import MCPServer
from mcp_workspace_common.contracts import ToolDefinition
from mcp_workspace_common.execution.server_context import ServerContext
from mcp_workspace_common.server import build_server

from mcp_gmail.tools.create_draft import definition as create_draft
from mcp_gmail.tools.list_labels import definition as list_labels
from mcp_gmail.tools.manage_labels import definition as manage_labels
from mcp_gmail.tools.read_email import definition as read_email
from mcp_gmail.tools.search_emails import definition as search_emails
from mcp_gmail.tools.send_email import definition as send_email
from mcp_gmail.tools.summarize_thread import definition as summarize_thread


def tool_definitions() -> dict[str, ToolDefinition]:
    return {
        item.name: item
        for item in [
            search_emails(),
            read_email(),
            summarize_thread(),
            list_labels(),
            create_draft(),
            send_email(),
            manage_labels(),
        ]
    }


def create_server(runtime: ServerContext) -> MCPServer[Any]:
    return build_server("gmail", tool_definitions(), runtime)
