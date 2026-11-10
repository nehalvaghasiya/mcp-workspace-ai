from __future__ import annotations

import json
import secrets
from typing import TYPE_CHECKING, Any

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import delete, select

from mcp_workspace_api.contracts import CAL, DRIVE, GMAIL
from mcp_workspace_api.core.security import Denied, secret_hash
from mcp_workspace_api.db import (
    GoogleAccount,
    OAuthState,
    User,
    UserSession,
    now,
    uid,
)
from mcp_workspace_api.schemas.responses import (
    SessionView,
)

if TYPE_CHECKING:
    from mcp_workspace_api.core.application_context import ApplicationContext


def register(app: FastAPI, context: ApplicationContext) -> None:
    settings = context.settings
    db = context.db
    runtime = context.runtime
    app = context.app
    identify = context.session_service.identify
    require_user = context.session_service.require_user
    session_payload = context.session_service.session_payload
    login = context.session_service.login

    @app.get("/api/session", response_model=SessionView)
    async def current_session(request: Request) -> dict[str, Any]:
        return session_payload(identify(request))

    @app.post("/api/auth/demo")
    async def demo(request: Request) -> JSONResponse:
        if settings.mode != "mock":
            raise HTTPException(404, "Demo login is disabled")
        existing = identify(request)
        if existing:
            return JSONResponse(session_payload(existing))
        with db.session() as session:
            user = User(
                subject="demo:" + uid(), display_name="Northstar explorer", llm_consent=False
            )
            session.add(user)
            session.flush()
            session.add(
                GoogleAccount(
                    user_id=user.id,
                    subject=user.subject,
                    credentials="mock",
                    scopes=[],
                    enabled=["gmail", "calendar", "drive"],
                )
            )
        return login(user)

    @app.post("/api/auth/logout")
    async def logout(request: Request, user: User = Depends(require_user)) -> JSONResponse:
        with db.session() as session:
            session.execute(
                delete(UserSession).where(
                    UserSession.user_id == user.id,
                    UserSession.token_hash
                    == secret_hash(request.cookies.get("workspace_session", "")),
                )
            )
            session.execute(delete(OAuthState).where(OAuthState.user_id == user.id))
        response = JSONResponse({"status": "signed_out"})
        response.delete_cookie("workspace_session")
        return response

    oauth_client = context.connection_service.oauth_client

    @app.get("/api/auth/google/start")
    async def oauth_start(
        request: Request, connector: str = "", access: str = "read"
    ) -> RedirectResponse:
        if settings.mode != "live":
            raise HTTPException(400, "Switch server MODE to live before connecting a real account")
        identity = identify(request)
        if connector and not identity:
            raise HTTPException(401, "Sign in before connecting a provider")
        scopes: dict[str, list[str]] = {
            "": [],
            "gmail": [GMAIL + "readonly"],
            "calendar": [CAL + "events.readonly", CAL + "calendarlist.readonly", CAL + "freebusy"],
            "drive": [DRIVE],
            "drive_open": [DRIVE, "https://www.googleapis.com/auth/drive.install"],
        }
        if connector not in scopes or access not in {"read", "write"}:
            raise HTTPException(400, "Unknown connector or permission")
        requested = scopes[connector]
        if access == "write" and connector == "gmail":
            requested = [GMAIL + "readonly", GMAIL + "compose", GMAIL + "modify"]
        elif access == "write" and connector == "calendar":
            requested = scopes[connector] + [CAL + "events"]
        browser, state, nonce, verifier = (secrets.token_urlsafe(48) for _ in range(4))
        with db.session() as session:
            session.add(
                OAuthState(
                    id=state,
                    browser_hash=secret_hash(browser),
                    user_id=identity[0].id if identity else None,
                    nonce=nonce,
                    verifier=verifier,
                    connector=connector,
                    expires_at=now() + 300,
                )
            )
        oauth = oauth_client()
        try:
            response = RedirectResponse(oauth.authorization_url(requested, state, nonce, verifier))
        finally:
            await oauth.aclose()
        response.set_cookie(
            "workspace_oauth",
            browser,
            httponly=True,
            secure=settings.web_origin.startswith("https://"),
            samesite="lax",
            max_age=300,
        )
        return response

    @app.get("/api/auth/google/callback")
    async def oauth_callback(
        request: Request, state: str = "", code: str = "", error: str = ""
    ) -> JSONResponse:
        with db.session() as session:
            row = session.get(OAuthState, state)
            if (
                not row
                or row.expires_at < now()
                or not secrets.compare_digest(
                    row.browser_hash, secret_hash(request.cookies.get("workspace_oauth", ""))
                )
            ):
                raise HTTPException(400, "Invalid, expired, or reused OAuth state")
            saved: dict[str, Any] = {
                "nonce": row.nonce,
                "verifier": row.verifier,
                "user_id": row.user_id,
                "connector": row.connector,
            }
            session.delete(row)
        if error or not code:
            raise HTTPException(400, "Google authorization was declined; reconnect when ready")
        identity = identify(request)
        if saved["user_id"] and (not identity or identity[0].id != saved["user_id"]):
            raise HTTPException(
                403, "The session that requested connector access is no longer active"
            )
        oauth = oauth_client()
        try:
            tokens = await oauth.exchange(code, saved["verifier"])
            claims = await oauth.verify_id_token(tokens.get("id_token", ""), saved["nonce"])
        except Exception:
            raise HTTPException(400, "Google authorization could not be verified") from None
        finally:
            await oauth.aclose()
        subject = "https://accounts.google.com:" + claims["sub"]
        with db.session() as session:
            if saved["user_id"]:
                user = session.get(User, saved["user_id"])
                if not user or user.deleted or user.subject != subject:
                    raise HTTPException(403, "Connect the same Google account used to sign in")
            else:
                user = session.scalar(select(User).where(User.subject == subject))
                if user and user.deleted:
                    raise HTTPException(403, "This local account was deleted")
                if not user:
                    user = User(
                        subject=subject,
                        display_name=claims.get("name", "Workspace user"),
                        email=claims.get("email", "") if claims.get("email_verified") else "",
                    )
                    session.add(user)
                    session.flush()
            account = session.scalar(select(GoogleAccount).where(GoogleAccount.user_id == user.id))
            old = json.loads(runtime.vault.decrypt(account.credentials.encode())) if account else {}
            credentials = {**old, **tokens, "expires_at": now() + tokens.get("expires_in", 3600)}
            scopes = tokens.get("scope", "").split()
            enabled = list(account.enabled) if account else []
            connector = saved["connector"].replace("_open", "")
            if connector and connector not in enabled:
                enabled.append(connector)
            encrypted = runtime.vault.encrypt(json.dumps(credentials).encode()).decode()
            if account:
                account.credentials, account.scopes, account.enabled = encrypted, scopes, enabled
                account.key_version = settings.token_key_version
            else:
                session.add(
                    GoogleAccount(
                        user_id=user.id,
                        subject=subject,
                        credentials=encrypted,
                        scopes=scopes,
                        enabled=enabled,
                        key_version=settings.token_key_version,
                    )
                )
        response = login(user)
        response.status_code = 303
        response.headers["location"] = settings.web_origin + "/#connectors"
        response.delete_cookie("workspace_oauth")
        return response

    @app.post("/api/auth/google/disconnect")
    async def google_disconnect(user: User = Depends(require_user)) -> dict[str, Any]:
        return await context.connection_service.google_disconnect(user)

    @app.get("/api/auth/google/drive-open")
    async def drive_open(state: str, user: User = Depends(require_user)) -> RedirectResponse:
        try:
            value = json.loads(state)
            ids = value.get("ids", []) + value.get("exportIds", [])
            if value.get("action") != "open" or not ids or len(ids) > 20:
                raise ValueError
            keys = value.get("resourceKeys", {})
        except (ValueError, TypeError):
            raise HTTPException(400, "Invalid Drive open request") from None
        # Drive's userId is untrusted; the authenticated app identity determines access.
        for file_id in ids:
            result = await runtime.invoke(
                user.id,
                "drive.get_file_metadata",
                {"file_id": file_id, "resource_key": keys.get(file_id)},
            )
            if result.status != "success":
                raise Denied(result.code or "PERMISSION_DENIED", "; ".join(result.warnings))
        return RedirectResponse(settings.web_origin + "/#connectors", status_code=303)
