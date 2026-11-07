from typing import Any

from mcp.server import MCPServer
from mcp_calendar.server import create_server as calendar_server
from mcp_demo.server import create_server as demo_server
from mcp_documents.server import create_server as document_server
from mcp_drive.server import create_server as drive_server
from mcp_gmail.server import create_server as gmail_server
from mcp_workspace_common.mcp.guard import Guard as Guard
from mcp_workspace_common.mcp.protected_http import ProtectedHTTP as ProtectedHTTP


def build_servers(runtime: Any) -> dict[str, MCPServer[Any]]:
    return {
        "gmail": gmail_server(runtime),
        "calendar": calendar_server(runtime),
        "drive": drive_server(runtime),
        "artifact": document_server(runtime),
        "demo": demo_server(runtime),
    }
