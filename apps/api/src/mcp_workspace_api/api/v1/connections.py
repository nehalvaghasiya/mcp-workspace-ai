from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi import Depends, FastAPI, HTTPException
from mcp_workspace_common.scopes import (
    GOOGLE_SERVICES,
    READ_SCOPES,
    expanded_scopes,
    scope_options_satisfied,
)
from sqlalchemy import select, update

from mcp_workspace_api.core.presenters import timestamp
from mcp_workspace_api.db import (
    Approval,
    GoogleAccount,
    User,
)
from mcp_workspace_api.schemas.requests.connector_update import ConnectorUpdate
from mcp_workspace_api.schemas.responses import (
    ConnectorView,
)
from mcp_workspace_api.services.connection_status import connection_status

if TYPE_CHECKING:
    from mcp_workspace_api.core.application_context import ApplicationContext


def register(app: FastAPI, context: ApplicationContext) -> None:
    settings = context.settings
    db = context.db
    runtime = context.runtime
    app = context.app
    require_user = context.session_service.require_user

    @app.get("/api/connectors", response_model=list[ConnectorView])
    async def connectors(user: User = Depends(require_user)) -> list[dict[str, Any]]:
        with db.session() as session:
            account = session.scalar(select(GoogleAccount).where(GoogleAccount.user_id == user.id))
        names = GOOGLE_SERVICES if settings.mode == "live" else ("gmail", "calendar", "drive")
        granted = expanded_scopes(account.scopes if account else [])
        return [
            {
                "id": name,
                "name": {
                    "gmail": "Gmail",
                    "calendar": "Google Calendar",
                    "drive": "Google Drive",
                    "docs": "Google Docs",
                    "sheets": "Google Sheets",
                    "slides": "Google Slides",
                }[name],
                "status": connection_status(
                    account,
                    name,
                    mock=settings.mode == "mock",
                    missing=set(READ_SCOPES[name]) - granted,
                )[0],
                "scopes": account.scopes if account else [],
                "enabled": bool(account and name in account.enabled),
                "mode": settings.mode,
                "available_capabilities": [
                    tool.name
                    for tool in runtime.tools.values()
                    if tool.server == name
                    and account
                    and name in account.enabled
                    and (
                        settings.mode == "mock"
                        or scope_options_satisfied(
                            account.scopes, tool.scopes, tool.scope_alternatives
                        )
                    )
                ],
                "missing_scopes": sorted(set(READ_SCOPES[name]) - granted)
                if settings.mode == "live"
                else [],
                "last_error": connection_status(
                    account,
                    name,
                    mock=settings.mode == "mock",
                    missing=set(READ_SCOPES[name]) - granted,
                )[1],
                "last_checked_at": timestamp(account.connection_checked_at)
                if account and account.connection_checked_at
                else None,
            }
            for name in names
        ]

    @app.patch("/api/connectors/{connector}")
    async def connector_switch(
        connector: str, body: ConnectorUpdate, user: User = Depends(require_user)
    ) -> dict[str, str]:
        if connector not in GOOGLE_SERVICES:
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
