from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi import FastAPI

from mcp_workspace_api.core.runtime_identity import runtime_identity

if TYPE_CHECKING:
    from mcp_workspace_api.core.application_context import ApplicationContext


def register(app: FastAPI, context: ApplicationContext) -> None:
    servers = context.servers
    settings = context.settings
    db = context.db
    app = context.app

    @app.get("/api/health")
    async def health() -> dict[str, Any]:
        return {
            "status": "ok",
            "mode": settings.mode,
            "version": "0.1.0",
            "application": "mcp-workspace-ai",
            "instance_id": runtime_identity(settings),
        }

    @app.get("/api/ready")
    async def ready() -> dict[str, Any]:
        from sqlalchemy import text

        with db.session() as session:
            session.execute(text("SELECT 1"))
        return {"status": "ready", "database": "ok", "mcp": list(servers)}
