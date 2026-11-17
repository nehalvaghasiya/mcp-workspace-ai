from __future__ import annotations

import secrets
from typing import TYPE_CHECKING, Any

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select

from mcp_workspace_api.core.security import secret_hash
from mcp_workspace_api.db import (
    User,
    UserSession,
    now,
)

if TYPE_CHECKING:
    from mcp_workspace_api.core.application_context import ApplicationContext


class SessionService:
    def __init__(self, context: ApplicationContext) -> None:
        self.context = context

    def identify(self, request: Request) -> tuple[User, UserSession] | None:
        context = self.context
        db = context.db
        token = request.cookies.get("workspace_session", "")
        with db.session() as session:
            row = session.scalar(
                select(UserSession).where(
                    UserSession.token_hash == secret_hash(token), UserSession.expires_at > now()
                )
            )
            user = session.get(User, row.user_id) if row else None
            if row and user and not user.deleted:
                return user, row
        return None

    def require_user(self, request: Request) -> User:
        context = self.context
        identify = context.session_service.identify
        identity = identify(request)
        if not identity:
            raise HTTPException(401, "Sign in to continue")
        user, session = identity
        if request.method in {"POST", "PATCH", "DELETE"} and not secrets.compare_digest(
            request.headers.get("X-CSRF-Token", ""), session.csrf
        ):
            raise HTTPException(403, "CSRF token is missing or invalid")
        return user

    def session_payload(self, identity: tuple[User, UserSession] | None) -> dict[str, Any]:
        context = self.context
        settings = context.settings
        user, session = identity if identity else (None, None)
        return {
            "user": {
                "id": user.id,
                "display_name": user.display_name,
                "email": user.email,
                "timezone": user.timezone,
            }
            if user
            else None,
            "csrf_token": session.csrf if session else "",
            "mode": settings.mode,
            "llm": {
                "provider": settings.llm_provider,
                "model": settings.llm_model or "FakeLLM",
                "consented": bool(
                    user
                    and user.llm_consent
                    and user.consent_provider == settings.llm_base_url + ":" + settings.llm_model
                ),
            },
        }

    def login(self, user: User) -> JSONResponse:
        context = self.context
        settings = context.settings
        db = context.db
        session_payload = context.session_service.session_payload
        token = secrets.token_urlsafe(32)
        with db.session() as session:
            row = UserSession(
                user_id=user.id,
                token_hash=secret_hash(token),
                csrf=secrets.token_urlsafe(24),
                expires_at=now() + 8 * 3600,
            )
            session.add(row)
            session.flush()
            payload = session_payload((user, row))
        response = JSONResponse(payload)
        response.set_cookie(
            "workspace_session",
            token,
            httponly=True,
            secure=settings.web_origin.startswith("https://"),
            samesite="lax",
            max_age=8 * 3600,
        )
        return response
