from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING

from sqlalchemy import select

from mcp_workspace_api.core.security import Denied
from mcp_workspace_api.db import (
    GoogleAccount,
    User,
    now,
)

if TYPE_CHECKING:
    from mcp_workspace_api.core.execution_context import Runtime


class TokenVault:
    def __init__(self, context: Runtime) -> None:
        self.context = context

    def account(self, user_id: str) -> GoogleAccount:
        context = self.context
        with context.db.session() as session:
            account = session.scalar(select(GoogleAccount).where(GoogleAccount.user_id == user_id))
            if not account:
                raise Denied("CONNECTOR_NOT_AUTHORIZED", "Connect Google first")
            return account

    async def token(self, user_id: str) -> str:
        context = self.context
        async with context.write_locks.setdefault("refresh:" + user_id, asyncio.Lock()):
            return await context._refresh_token(user_id)

    async def _refresh_token(self, user_id: str) -> str:
        context = self.context
        from mcp_workspace_api.auth.oauth import GoogleOAuth

        account = context.account(user_id)
        credentials = json.loads(context.vault.decrypt(account.credentials.encode()))
        if credentials.get("expires_at", 0) < now() + 60:
            if not credentials.get("refresh_token"):
                raise Denied("CONNECTOR_NOT_AUTHORIZED", "Google access expired; reconnect")
            oauth = GoogleOAuth(
                context.settings.google_client_id,
                context.settings.google_client_secret,
                context.settings.google_redirect_uri,
            )
            try:
                refreshed = await oauth.refresh(credentials["refresh_token"])
            except Exception:
                with context.db.session() as session:
                    row = session.get(GoogleAccount, account.id)
                    if row:
                        row.enabled = []
                raise Denied(
                    "CONNECTOR_NOT_AUTHORIZED", "Google access expired or was revoked; reconnect"
                ) from None
            finally:
                await oauth.aclose()
            credentials.update(refreshed)
            credentials["expires_at"] = now() + refreshed.get("expires_in", 3600)
            with context.db.session() as session:
                row = session.get(GoogleAccount, account.id)
                user = session.get(User, user_id)
                if not row or not user or user.deleted:
                    raise Denied(
                        "CONNECTOR_NOT_AUTHORIZED", "Google access was disconnected during refresh"
                    )
                row.credentials = context.vault.encrypt(json.dumps(credentials).encode()).decode()
                row.key_version = context.settings.token_key_version
                if "scope" in refreshed:
                    row.scopes = refreshed["scope"].split()
        return str(credentials["access_token"])
