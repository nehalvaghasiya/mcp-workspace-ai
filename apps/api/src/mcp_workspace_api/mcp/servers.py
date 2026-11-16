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
    servers = {
        "gmail": gmail_server(runtime),
        "calendar": calendar_server(runtime),
        "drive": drive_server(runtime),
        "artifact": document_server(runtime),
    }
    if runtime.settings.mode == "live":
        from mcp_google_docs.server import create_server as docs_server
        from mcp_sheets.server import create_server as sheets_server
        from mcp_slides.server import create_server as slides_server

        servers.update(
            docs=docs_server(runtime), sheets=sheets_server(runtime), slides=slides_server(runtime)
        )
    else:
        servers["demo"] = demo_server(runtime)
    return servers
