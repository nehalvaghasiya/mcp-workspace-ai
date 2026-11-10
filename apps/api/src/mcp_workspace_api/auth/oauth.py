from __future__ import annotations

import re
import time
from typing import Any
from urllib.parse import parse_qsl

import httpx
from authlib.jose import JsonWebToken
from authlib.jose.errors import JoseError
from authlib.oauth2.client import OAuth2Client
from authlib.oauth2.rfc6749.parameters import prepare_token_request

from mcp_workspace_api.auth.oauth_error import OAuthError


class GoogleOAuth:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.client_id = client_id
        self._client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.client = client or httpx.AsyncClient(
            timeout=15, follow_redirects=False, trust_env=False
        )
        self._owns_client = client is None
        self._jwks: dict[str, Any] | None = None
        self._jwks_expires = 0.0

    def authorization_url(
        self, scopes: list[str], state: str, nonce: str, code_verifier: str
    ) -> str:
        if not state or not nonce or not re.fullmatch(r"[A-Za-z0-9._~-]{43,128}", code_verifier):
            raise OAuthError(
                "invalid_oauth_request", "State, nonce and a valid PKCE verifier are required"
            )
        oauth = OAuth2Client(
            None,
            client_id=self.client_id,
            redirect_uri=self.redirect_uri,
            scope=" ".join(sorted(set(scopes) | {"openid", "email", "profile"})),
            code_challenge_method="S256",
        )
        url, _ = oauth.create_authorization_url(
            AUTHORIZE_URL,
            state=state,
            nonce=nonce,
            code_verifier=code_verifier,
            access_type="offline",
            include_granted_scopes="true",
            prompt="select_account consent",
        )
        return str(url)

    async def _post(self, url: str, data: dict[str, str]) -> dict[str, Any]:
        try:
            response = await self.client.post(url, data=data, timeout=15, follow_redirects=False)
            if response.status_code != 200:
                raise OAuthError(
                    "oauth_reconnect_required", "Google authorization failed; reconnect the account"
                )
            if len(response.content) > 100000:
                raise OAuthError("invalid_oauth_response", "Invalid Google authorization response")
            value = response.json()
            if not isinstance(value, dict) or value.get("error"):
                raise OAuthError(
                    "oauth_reconnect_required", "Google authorization failed; reconnect the account"
                )
            return value
        except (httpx.HTTPError, ValueError) as exc:
            if isinstance(exc, OAuthError):
                raise
            raise OAuthError("oauth_unavailable", "Google authorization is unavailable") from None

    async def exchange(self, code: str, code_verifier: str) -> dict[str, Any]:
        if not code or not re.fullmatch(r"[A-Za-z0-9._~-]{43,128}", code_verifier):
            raise OAuthError(
                "invalid_oauth_request", "Authorization code and PKCE verifier are required"
            )
        body = prepare_token_request(
            "authorization_code",
            code=code,
            code_verifier=code_verifier,
            redirect_uri=self.redirect_uri,
        )
        tokens = await self._post(
            TOKEN_URL,
            dict(parse_qsl(body))
            | {"client_id": self.client_id, "client_secret": self._client_secret},
        )
        self._validate_tokens(tokens)
        return tokens

    async def refresh(self, refresh_token: str) -> dict[str, Any]:
        body = prepare_token_request("refresh_token", refresh_token=refresh_token)
        tokens = await self._post(
            TOKEN_URL,
            dict(parse_qsl(body))
            | {"client_id": self.client_id, "client_secret": self._client_secret},
        )
        self._validate_tokens(tokens)
        return tokens

    @staticmethod
    def _validate_tokens(tokens: dict[str, Any]) -> None:
        if (
            not isinstance(tokens.get("access_token"), str)
            or tokens.get("token_type", "").lower() != "bearer"
            or not isinstance(tokens.get("expires_in"), (int, float))
            or tokens["expires_in"] <= 0
        ):
            raise OAuthError(
                "invalid_oauth_response", "Google returned an incomplete token response"
            )

    async def verify_id_token(self, token: str, nonce: str) -> dict[str, Any]:
        if not nonce or not token or len(token) > 20000:
            raise OAuthError("invalid_id_token", "Google identity could not be verified")
        for attempt in range(2):
            if self._jwks is None or self._jwks_expires < time.monotonic() or attempt:
                try:
                    response = await self.client.get(JWKS_URL, timeout=15, follow_redirects=False)
                    if response.status_code != 200 or len(response.content) > 100000:
                        raise OAuthError("oidc_unavailable", "Google signing keys are unavailable")
                    keys = response.json()
                    if not isinstance(keys, dict) or not keys.get("keys"):
                        raise OAuthError("oidc_unavailable", "Google signing keys are unavailable")
                    self._jwks = keys
                    self._jwks_expires = time.monotonic() + 300
                except (httpx.HTTPError, ValueError):
                    raise OAuthError(
                        "oidc_unavailable", "Google signing keys are unavailable"
                    ) from None
            try:
                claims = JsonWebToken(["RS256"]).decode(
                    token,
                    self._jwks,
                    claims_options={
                        "iss": {
                            "essential": True,
                            "values": ["https://accounts.google.com", "accounts.google.com"],
                        },
                        "aud": {"essential": True, "value": self.client_id},
                        "exp": {"essential": True},
                        "iat": {"essential": True},
                        "sub": {"essential": True},
                        "nonce": {"essential": True, "value": nonce},
                    },
                )
                claims.validate(leeway=30)
                if (
                    not isinstance(claims["sub"], str)
                    or not claims["sub"]
                    or claims.get("azp", self.client_id) != self.client_id
                ):
                    raise OAuthError("invalid_id_token", "Google identity could not be verified")
                return dict(claims)
            except (JoseError, ValueError, TypeError, KeyError):
                if attempt:
                    raise OAuthError(
                        "invalid_id_token", "Google identity could not be verified"
                    ) from None
        raise OAuthError("invalid_id_token", "Google identity could not be verified")

    async def revoke(self, token: str) -> None:
        try:
            response = await self.client.post(
                REVOKE_URL, data={"token": token}, timeout=15, follow_redirects=False
            )
            if response.status_code not in {200, 400}:
                raise OAuthError("revoke_failed", "Google grant revocation could not be confirmed")
        except httpx.HTTPError:
            raise OAuthError(
                "revoke_failed", "Google grant revocation could not be confirmed"
            ) from None

    async def aclose(self) -> None:
        if self._owns_client:
            await self.client.aclose()


AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"  # nosec B105: public endpoint, not a credential
REVOKE_URL = "https://oauth2.googleapis.com/revoke"
JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
