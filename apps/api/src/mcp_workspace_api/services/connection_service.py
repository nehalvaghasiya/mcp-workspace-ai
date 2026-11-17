from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from fastapi import HTTPException
from mcp_workspace_common.scopes import GOOGLE_SERVICES
from sqlalchemy import delete, select, update

from mcp_workspace_api.db import (
    Approval,
    GoogleAccount,
    User,
)

if TYPE_CHECKING:
    from mcp_workspace_api.core.application_context import ApplicationContext


class ConnectionService:
    def __init__(self, context: ApplicationContext) -> None:
        self.context = context

    async def google_disconnect(self, user: User) -> dict[str, Any]:
        context = self.context
        settings = context.settings
        db = context.db
        runtime = context.runtime
        confirmed = settings.mode == "mock"
        with db.session() as session:
            account = session.scalar(select(GoogleAccount).where(GoogleAccount.user_id == user.id))
        if account and settings.mode == "live":
            credentials = json.loads(runtime.vault.decrypt(account.credentials.encode()))
            oauth = self.oauth_client()
            try:
                await oauth.revoke(credentials.get("refresh_token") or credentials["access_token"])
                confirmed = True
            except Exception:
                confirmed = False
            finally:
                await oauth.aclose()
        with db.session() as session:
            session.execute(delete(GoogleAccount).where(GoogleAccount.user_id == user.id))
            session.execute(
                update(Approval)
                .where(Approval.user_id == user.id, Approval.status.in_(["pending", "approved"]))
                .values(status="revoked")
            )
        adapter = runtime.adapters.pop(user.id, None)
        if adapter:
            await adapter.aclose()
        return {
            "status": "disconnected",
            "revocation_confirmed": confirmed,
            "affected_connectors": list(GOOGLE_SERVICES)
            if settings.mode == "live"
            else ["gmail", "calendar", "drive"],
        }

    def oauth_client(self) -> Any:
        settings = self.context.settings
        from mcp_workspace_api.auth.oauth import GoogleOAuth

        if not settings.google_client_id or not settings.google_client_secret:
            raise HTTPException(
                503, "Configure Google OAuth on the server; the mock demo needs no credentials"
            )
        return GoogleOAuth(
            settings.google_client_id, settings.google_client_secret, settings.google_redirect_uri
        )
