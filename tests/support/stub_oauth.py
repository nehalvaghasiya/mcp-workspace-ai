from __future__ import annotations

from typing import Any
from urllib.parse import urlencode


class StubOAuth:
    subject = "synthetic-sub-a"
    scope = "openid email profile"
    exchanges: list[tuple[str, str]] = []
    requested: list[dict[str, Any]] = []

    def __init__(self, *args: Any) -> None:
        pass

    def authorization_url(self, scopes: list[str], state: str, nonce: str, verifier: str) -> str:
        self.requested.append(
            {"scopes": scopes, "state": state, "nonce": nonce, "verifier": verifier}
        )
        return "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(
            {"state": state, "nonce": nonce}
        )

    async def exchange(self, code: str, code_verifier: str) -> dict[str, Any]:
        self.exchanges.append((code, code_verifier))
        return {
            "access_token": "CANARY_ACCESS_SECRET",
            "refresh_token": "CANARY_REFRESH_SECRET",
            "id_token": "fake-id-token",
            "expires_in": 3600,
            "token_type": "Bearer",
            "scope": self.scope,
        }

    async def verify_id_token(self, token: str, nonce: str) -> dict[str, Any]:
        assert token == "fake-id-token" and nonce == self.requested[-1]["nonce"]
        return {
            "sub": self.subject,
            "name": "Synthetic login",
            "email": "demo@example.invalid",
            "email_verified": True,
        }

    async def refresh(self, refresh_token: str) -> dict[str, Any]:
        assert refresh_token == "CANARY_REFRESH_SECRET"
        return {
            "access_token": "CANARY_REFRESHED_SECRET",
            "expires_in": 3600,
            "token_type": "Bearer",
            "scope": self.scope,
        }

    async def revoke(self, token: str) -> None:
        assert token in {"CANARY_REFRESH_SECRET", "CANARY_ACCESS_SECRET"}

    async def aclose(self) -> None:
        return None
