from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select, update

from mcp_workspace_api.db import (
    Approval,
    GoogleAccount,
    User,
)
from mcp_workspace_api.schemas.requests.connector_update import ConnectorUpdate
from mcp_workspace_api.schemas.responses import (
    ConnectorView,
)

if TYPE_CHECKING:
    from mcp_workspace_api.core.application_context import ApplicationContext


def register(app: FastAPI, context: ApplicationContext) -> None:
    settings = context.settings
    db = context.db
    app = context.app
    require_user = context.session_service.require_user

    @app.get("/api/connectors", response_model=list[ConnectorView])
    async def connectors(user: User = Depends(require_user)) -> list[dict[str, Any]]:
        with db.session() as session:
            account = session.scalar(select(GoogleAccount).where(GoogleAccount.user_id == user.id))
        return [
            {
                "id": name,
                "name": {"gmail": "Gmail", "calendar": "Google Calendar", "drive": "Google Drive"}[
                    name
                ],
                "status": ("mock" if settings.mode == "mock" else "connected")
                if account and name in account.enabled
                else "not_connected",
                "scopes": account.scopes if account else [],
                "enabled": bool(account and name in account.enabled),
                "mode": settings.mode,
            }
            for name in ("gmail", "calendar", "drive")
        ]

    @app.patch("/api/connectors/{connector}")
    async def connector_switch(
        connector: str, body: ConnectorUpdate, user: User = Depends(require_user)
    ) -> dict[str, str]:
        if connector not in {"gmail", "calendar", "drive"}:
            raise HTTPException(404, "Connector not found")
        with db.session() as session:
            account = session.scalar(select(GoogleAccount).where(GoogleAccount.user_id == user.id))
            if not account:
                raise HTTPException(409, "Connect Google first")
            account.enabled = sorted(
                (set(account.enabled) | {connector})
                if body.enabled
                else (set(account.enabled) - {connector})
            )
            session.execute(
                update(Approval)
                .where(
                    Approval.user_id == user.id,
                    Approval.tool.like(connector + ".%"),
                    Approval.status.in_(["pending", "approved"]),
                )
                .values(status="revoked")
            )
        return {"status": "enabled" if body.enabled else "disabled"}
