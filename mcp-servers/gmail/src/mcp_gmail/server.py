from __future__ import annotations

from typing import Any

from mcp.server import MCPServer
from mcp_workspace_common.contracts import ToolDefinition
from mcp_workspace_common.execution.server_context import ServerContext
from mcp_workspace_common.server import build_server

from mcp_gmail.tools.archive_message import definition as archive_message
from mcp_gmail.tools.create_draft import definition as create_draft
from mcp_gmail.tools.get_attachment import definition as get_attachment
from mcp_gmail.tools.get_draft import definition as get_draft
from mcp_gmail.tools.list_labels import definition as list_labels
from mcp_gmail.tools.manage_labels import definition as manage_labels
from mcp_gmail.tools.read_email import definition as read_email
from mcp_gmail.tools.read_messages import definition as read_messages
from mcp_gmail.tools.search_emails import definition as search_emails
from mcp_gmail.tools.send_email import definition as send_email
from mcp_gmail.tools.summarize_thread import definition as summarize_thread
from mcp_gmail.tools.trash_message import definition as trash_message
from mcp_gmail.tools.untrash_message import definition as untrash_message
from mcp_gmail.tools.update_draft import definition as update_draft

LIVE_ONLY_TOOLS = {
    "gmail.get_messages",
    "gmail.trash_message",
    "gmail.untrash_message",
    "gmail.get_draft",
    "gmail.update_draft",
    "gmail.get_attachment",
    "gmail.archive_message",
}


def tool_definitions(include_live: bool = False) -> dict[str, ToolDefinition]:
    definitions = [
        search_emails(),
        read_email(),
        summarize_thread(),
        list_labels(),
        create_draft(),
        send_email(),
        manage_labels(),
    ]
    if include_live:
        definitions.extend(
            [
                read_messages(),
                get_draft(),
                update_draft(),
                get_attachment(),
                archive_message(),
                trash_message(),
                untrash_message(),
            ]
        )
    return {item.name: item for item in definitions}


def create_server(runtime: ServerContext) -> MCPServer[Any]:
    return build_server(
        "gmail", tool_definitions(include_live=runtime.settings.mode == "live"), runtime
    )
