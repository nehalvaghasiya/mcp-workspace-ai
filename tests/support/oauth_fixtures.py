from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from mcp_workspace_api.main import create_app

from tests.support.isolated_settings import IsolatedSettings
from tests.support.stub_oauth import StubOAuth


@pytest.fixture
def oauth_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    from mcp_workspace_api.auth import oauth as google_auth

    StubOAuth.subject = "synthetic-sub-a"
    StubOAuth.scope = "openid email profile"
    StubOAuth.exchanges = []
    StubOAuth.requested = []
    monkeypatch.setattr(google_auth, "GoogleOAuth", StubOAuth)
    settings = IsolatedSettings(
        mode="live",
        data_dir=tmp_path,
        session_secret="synthetic-session-secret-long-enough",
        token_encryption_key=Fernet.generate_key().decode(),
        google_client_id="synthetic-client",
        google_client_secret="synthetic-secret",
        llm_provider="openai_compatible",
        llm_model="synthetic-model",
    )
    with TestClient(create_app(settings), follow_redirects=False) as client:
        yield client


def oauth_start(client: TestClient, connector: str = "", access: str = "read") -> str:
    response = client.get(
        "/api/auth/google/start", params={"connector": connector, "access": access}
    )
    assert response.status_code == 307, response.text
    state = parse_qs(urlsplit(response.headers["location"]).query)["state"][0]
    assert client.cookies.get("workspace_oauth")
    return state


def oauth_login(client: TestClient) -> dict[str, Any]:
    state = oauth_start(client)
    response = client.get(
        "/api/auth/google/callback", params={"state": state, "code": "synthetic-code"}
    )
    assert response.status_code == 303, response.text
    return dict(client.get("/api/session").json())
