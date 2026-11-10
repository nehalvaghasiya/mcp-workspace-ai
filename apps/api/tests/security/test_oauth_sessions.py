from __future__ import annotations

import asyncio
import json
from typing import Any, cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from mcp_workspace_api.contracts import GMAIL
from mcp_workspace_api.core.security import Denied
from mcp_workspace_api.db import (
    GoogleAccount,
    OAuthState,
    now,
)
from sqlalchemy import select

from tests.support.oauth_fixtures import oauth_login, oauth_start
from tests.support.stub_oauth import StubOAuth


def test_oauth_state_browser_binding_expiry_decline_and_replay(oauth_client: TestClient) -> None:
    assert (
        oauth_client.get(
            "/api/auth/google/callback", params={"state": "missing", "code": "x"}
        ).status_code
        == 400
    )
    state = oauth_start(oauth_client)
    saved_cookie = oauth_client.cookies.get("workspace_oauth")
    assert saved_cookie is not None
    oauth_client.cookies.clear()
    assert (
        oauth_client.get(
            "/api/auth/google/callback", params={"state": state, "code": "x"}
        ).status_code
        == 400
    )
    assert not StubOAuth.exchanges
    oauth_client.cookies.set("workspace_oauth", saved_cookie, domain="testserver.local", path="/")
    db = cast(FastAPI, oauth_client.app).state.db
    with db.session() as session:
        row = session.get(OAuthState, state)
        assert row is not None
        row.expires_at = now() - 1
    assert (
        oauth_client.get(
            "/api/auth/google/callback", params={"state": state, "code": "x"}
        ).status_code
        == 400
    )
    state = oauth_start(oauth_client)
    assert (
        oauth_client.get(
            "/api/auth/google/callback", params={"state": state, "error": "access_denied"}
        ).status_code
        == 400
    )
    assert (
        oauth_client.get(
            "/api/auth/google/callback", params={"state": state, "code": "x"}
        ).status_code
        == 400
    )
    state = oauth_start(oauth_client)
    assert (
        oauth_client.get(
            "/api/auth/google/callback", params={"state": state, "code": "valid"}
        ).status_code
        == 303
    )
    assert (
        oauth_client.get(
            "/api/auth/google/callback", params={"state": state, "code": "valid"}
        ).status_code
        == 400
    )
    assert len(StubOAuth.exchanges) == 1
    assert StubOAuth.exchanges[0][1] == StubOAuth.requested[-1]["verifier"]


def test_oauth_same_account_binding_encryption_and_narrow_scope(oauth_client: TestClient) -> None:
    identity = oauth_login(oauth_client)
    state = oauth_start(oauth_client, "gmail", "write")
    StubOAuth.scope = "openid email " + GMAIL + "readonly"
    assert (
        oauth_client.get(
            "/api/auth/google/callback", params={"state": state, "code": "upgrade"}
        ).status_code
        == 303
    )
    runtime = cast(FastAPI, oauth_client.app).state.runtime
    account = runtime.account(identity["user"]["id"])
    assert "CANARY" not in account.credentials
    assert (
        runtime.vault.decrypt(account.credentials.encode()).decode().find("CANARY_REFRESH_SECRET")
        >= 0
    )
    runtime.policy.authorize(identity["user"]["id"], runtime.tools["gmail.get_message"])
    with pytest.raises(Denied) as caught:
        runtime.policy.authorize(identity["user"]["id"], runtime.tools["gmail.send_draft"])
    assert caught.value.code == "SCOPE_MISSING"
    state = oauth_start(oauth_client, "drive")
    StubOAuth.subject = "synthetic-sub-b"
    assert (
        oauth_client.get(
            "/api/auth/google/callback", params={"state": state, "code": "other-account"}
        ).status_code
        == 403
    )
    assert runtime.account(identity["user"]["id"]).subject.endswith("synthetic-sub-a")


def test_incremental_oauth_callback_cannot_restore_logged_out_session(
    oauth_client: TestClient,
) -> None:
    identity = oauth_login(oauth_client)
    state = oauth_start(oauth_client, "gmail")
    signed_out = oauth_client.post(
        "/api/auth/logout", headers={"X-CSRF-Token": identity["csrf_token"]}
    )
    assert signed_out.status_code == 200
    assert oauth_client.get("/api/session").json()["user"] is None
    callback = oauth_client.get(
        "/api/auth/google/callback", params={"state": state, "code": "late-connector-callback"}
    )
    assert callback.status_code in {400, 401, 403}
    assert oauth_client.get("/api/session").json()["user"] is None


async def test_refreshed_narrower_scope_disables_lost_capability(oauth_client: TestClient) -> None:
    identity = oauth_login(oauth_client)
    runtime = cast(FastAPI, oauth_client.app).state.runtime
    user_id = identity["user"]["id"]
    with runtime.db.session() as session:
        account = session.scalar(select(GoogleAccount).where(GoogleAccount.user_id == user_id))
        assert account is not None
        account.scopes = [GMAIL + "readonly", GMAIL + "compose"]
        account.enabled = ["gmail"]
        creds = json.loads(runtime.vault.decrypt(account.credentials.encode()))
        creds["expires_at"] = 0
        account.credentials = runtime.vault.encrypt(json.dumps(creds).encode()).decode()
    StubOAuth.scope = GMAIL + "readonly"
    assert await runtime.token(user_id) == "CANARY_REFRESHED_SECRET"
    with pytest.raises(Denied) as caught:
        runtime.policy.authorize(user_id, runtime.tools["gmail.send_draft"])
    assert caught.value.code == "SCOPE_MISSING"


async def test_disconnect_during_refresh_fences_new_token(
    oauth_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    identity = oauth_login(oauth_client)
    runtime = cast(FastAPI, oauth_client.app).state.runtime
    user_id = identity["user"]["id"]
    started, resume = asyncio.Event(), asyncio.Event()

    async def blocked_refresh(self: StubOAuth, refresh_token: str) -> dict[str, Any]:
        started.set()
        await resume.wait()
        return {
            "access_token": "CANARY_LATE_TOKEN",
            "expires_in": 3600,
            "token_type": "Bearer",
            "scope": GMAIL + "readonly",
        }

    with runtime.db.session() as session:
        account = session.scalar(select(GoogleAccount).where(GoogleAccount.user_id == user_id))
        assert account is not None
        credentials = json.loads(runtime.vault.decrypt(account.credentials.encode()))
        credentials["expires_at"] = 0
        account.credentials = runtime.vault.encrypt(json.dumps(credentials).encode()).decode()
        account.enabled = ["gmail"]
    monkeypatch.setattr(StubOAuth, "refresh", blocked_refresh)
    refresh = asyncio.create_task(runtime.token(user_id))
    try:
        await asyncio.wait_for(started.wait(), 5)
        response = oauth_client.post(
            "/api/auth/google/disconnect", headers={"X-CSRF-Token": identity["csrf_token"]}
        )
        assert response.status_code == 200, response.text
        resume.set()
        with pytest.raises(Denied):
            await refresh
    finally:
        resume.set()
        await asyncio.gather(refresh, return_exceptions=True)
