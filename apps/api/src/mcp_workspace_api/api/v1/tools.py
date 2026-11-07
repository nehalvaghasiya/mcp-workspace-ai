from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi import Depends, FastAPI

from mcp_workspace_api.db import (
    User,
)
from mcp_workspace_api.schemas.responses import (
    ServerView,
    ToolView,
)

if TYPE_CHECKING:
    from mcp_workspace_api.core.application_context import ApplicationContext


def register(app: FastAPI, context: ApplicationContext) -> None:
    servers = context.servers
    runtime = context.runtime
    app = context.app
    require_user = context.session_service.require_user

    @app.get("/api/mcp/servers", response_model=list[ServerView])
    async def server_status(user: User = Depends(require_user)) -> list[dict[str, str]]:
        result = []
        for name in servers:
            try:
                async with runtime.client(user.id, name) as client:
                    version = client.protocol_version
                    result.append(
                        {
                            "id": name,
                            "name": f"Workspace {name}",
                            "transport": "streamable_http",
                            "protocol_version": version,
                            "status": "connected",
                        }
                    )
            except Exception:
                result.append(
                    {
                        "id": name,
                        "name": f"Workspace {name}",
                        "transport": "streamable_http",
                        "protocol_version": "unknown",
                        "status": "unavailable",
                    }
                )
        return result

    @app.get("/api/mcp/tools", response_model=list[ToolView])
    async def tools(user: User = Depends(require_user)) -> list[dict[str, Any]]:
        return await runtime.catalog(user.id)
