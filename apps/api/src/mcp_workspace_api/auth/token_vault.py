from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING

from cryptography.fernet import InvalidToken
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
        try:
            credentials = json.loads(context.vault.decrypt(account.credentials.encode()))
            if not isinstance(credentials, dict):
                raise ValueError
        except (InvalidToken, ValueError, UnicodeError):
            self.record_connection_result(user_id, "auth_required")
            raise Denied(
                "CONNECTOR_NOT_AUTHORIZED",
                "Stored Google authorization is unavailable; reconnect Google",
            ) from None
        if credentials.get("expires_at", 0) < now() + 60:
            if not credentials.get("refresh_token"):
                self.record_connection_result(user_id, "auth_required")
                raise Denied("CONNECTOR_NOT_AUTHORIZED", "Google access expired; reconnect")
            oauth = GoogleOAuth(
                context.settings.google_client_id,
                context.settings.google_client_secret,
                context.settings.google_redirect_uri,
            )
            try:
                refreshed = await oauth.refresh(credentials["refresh_token"])
            except Exception as error:
                if getattr(error, "code", "") == "oauth_unavailable":
                    self.record_connection_result(user_id, "provider_unavailable")
                    raise Denied(
                        "PROVIDER_UNAVAILABLE",
                        "Google is temporarily unavailable; retry the connection",
                    ) from None
                self.record_connection_result(user_id, "auth_required")
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
                row.connection_error = ""
                row.connection_checked_at = now()
        token = credentials.get("access_token")
        if not isinstance(token, str) or not token:
            self.record_connection_result(user_id, "auth_required")
            raise Denied(
                "CONNECTOR_NOT_AUTHORIZED", "Google authorization is incomplete; reconnect Google"
            )
        return token

    def record_connection_result(
        self, user_id: str, error_code: str | None, connector: str = ""
    ) -> None:
        if error_code not in {
            None,
            "auth_required",
            "permission_denied",
            "provider_unavailable",
            "rate_limited",
        }:
            return
        with self.context.db.session() as session:
            account = session.scalar(select(GoogleAccount).where(GoogleAccount.user_id == user_id))
            if not account:
                return
            account.connection_checked_at = now()
            if error_code == "auth_required":
                account.connection_error = error_code
            elif error_code is None:
                account.connection_error = ""
            elif not connector:
                account.connection_error = error_code
            if connector:
                errors = dict(account.connector_errors or {})
                if error_code:
                    errors[connector] = error_code
                else:
                    errors.pop(connector, None)
                account.connector_errors = errors
