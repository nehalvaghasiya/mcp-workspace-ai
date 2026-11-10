from __future__ import annotations

import base64
import hashlib
import time
from typing import Any
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest
from authlib.jose import JsonWebKey, JsonWebToken
from mcp_workspace_api.auth.oauth import GoogleOAuth, OAuthError


def test_authorization_url_pkce_nonce_incremental_scopes() -> None:
    oauth = GoogleOAuth("client-id", "fake-client-secret", "http://localhost:8000/callback")
    verifier = "a" * 64
    url = oauth.authorization_url(
        ["https://www.googleapis.com/auth/drive.file"], "state", "nonce", verifier
    )
    query = parse_qs(urlsplit(url).query)
    assert query["state"] == ["state"] and query["nonce"] == ["nonce"]
    assert query["code_challenge"] == [
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    ]
    assert query["code_challenge_method"] == ["S256"]
    assert query["include_granted_scopes"] == ["true"]
    assert "openid" in query["scope"][0]
    assert "fake-client-secret" not in url
    with pytest.raises(OAuthError):
        oauth.authorization_url([], "", "nonce", verifier)


async def test_exchange_refresh_revoke_without_httpx2() -> None:
    forms = []

    def handler(request: httpx.Request) -> httpx.Response:
        form = parse_qs(request.content.decode())
        forms.append(form)
        if request.url.path == "/revoke":
            assert form["token"] == ["fake-refresh"]
            return httpx.Response(200)
        assert form["client_secret"] == ["fake-secret"]
        return httpx.Response(
            200,
            json={
                "access_token": "fake-access",
                "refresh_token": "fake-refresh",
                "token_type": "Bearer",
                "expires_in": 3600,
                "scope": "openid email",
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        oauth = GoogleOAuth("client", "fake-secret", "http://localhost:8000/callback", client)
        assert (await oauth.exchange("code", "a" * 64))["access_token"] == "fake-access"
        assert forms[0]["code_verifier"] == ["a" * 64]
        assert forms[0]["redirect_uri"] == ["http://localhost:8000/callback"]
        await oauth.refresh("fake-refresh")
        assert forms[1]["grant_type"] == ["refresh_token"]
        await oauth.revoke("fake-refresh")


async def test_oauth_errors_hide_provider_secret() -> None:
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda r: httpx.Response(400, text="CANARY_REFRESH_TOKEN"))
    ) as client:
        oauth = GoogleOAuth("client", "fake-secret", "http://localhost/callback", client)
        with pytest.raises(OAuthError) as caught:
            await oauth.refresh("CANARY_REFRESH_TOKEN")
        assert caught.value.code == "oauth_reconnect_required"
        assert "CANARY" not in str(caught.value)


@pytest.fixture
def signing_key() -> Any:
    return JsonWebKey.generate_key("RSA", 2048, is_private=True, options={"kid": "synthetic-key"})


@pytest.mark.parametrize(
    "override,valid",
    [
        ({}, True),
        ({"aud": "other-client"}, False),
        ({"iss": "https://attacker.invalid"}, False),
        ({"nonce": "wrong"}, False),
        ({"exp": 1}, False),
        ({"azp": "other-client"}, False),
        ({"sub": ""}, False),
    ],
)
async def test_oidc_signature_audience_issuer_expiry_nonce(
    signing_key: Any, override: dict[str, Any], valid: bool
) -> None:
    claims = {
        "iss": "https://accounts.google.com",
        "aud": "client",
        "sub": "synthetic-google-sub",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()),
        "nonce": "nonce",
        "email": "demo@example.invalid",
        "email_verified": True,
    } | override
    token = (
        JsonWebToken(["RS256"])
        .encode({"alg": "RS256", "kid": "synthetic-key"}, claims, signing_key)
        .decode()
    )
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(200, json={"keys": [signing_key.as_dict(is_private=False)]})
        )
    ) as client:
        oauth = GoogleOAuth("client", "fake-secret", "http://localhost/callback", client)
        if valid:
            assert (await oauth.verify_id_token(token, "nonce"))["sub"] == "synthetic-google-sub"
        else:
            with pytest.raises(OAuthError):
                await oauth.verify_id_token(token, "nonce")


async def test_oidc_rejects_wrong_signing_key(signing_key: Any) -> None:
    attacker = JsonWebKey.generate_key(
        "RSA", 2048, is_private=True, options={"kid": "synthetic-key"}
    )
    token = (
        JsonWebToken(["RS256"])
        .encode(
            {"alg": "RS256", "kid": "synthetic-key"},
            {
                "iss": "https://accounts.google.com",
                "aud": "client",
                "sub": "user",
                "exp": int(time.time()) + 3600,
                "iat": int(time.time()),
                "nonce": "nonce",
            },
            attacker,
        )
        .decode()
    )
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(200, json={"keys": [signing_key.as_dict(is_private=False)]})
        )
    ) as client:
        with pytest.raises(OAuthError, match="could not be verified"):
            await GoogleOAuth(
                "client", "fake-secret", "http://localhost/callback", client
            ).verify_id_token(token, "nonce")
