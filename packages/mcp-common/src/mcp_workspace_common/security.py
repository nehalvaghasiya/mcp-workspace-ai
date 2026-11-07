from __future__ import annotations

import base64
import hashlib
import hmac
import json
from typing import Any

from mcp_workspace_common.clock import now
from mcp_workspace_common.errors import Denied


def secret_hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


class Signer:
    def __init__(self, secret: str) -> None:
        self.key = secret.encode()

    def issue(self, claims: dict[str, Any], ttl: int = 60) -> str:
        body = base64.urlsafe_b64encode(
            json.dumps({**claims, "exp": now() + ttl}, sort_keys=True).encode()
        ).decode()
        signature = hmac.new(self.key, body.encode(), hashlib.sha256).hexdigest()
        return body + "." + signature

    def verify(self, token: str, audience: str) -> dict[str, Any]:
        try:
            body, signature = token.split(".")
            expected = hmac.new(self.key, body.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(signature, expected):
                raise ValueError
            claims = json.loads(base64.urlsafe_b64decode(body))
            if claims["exp"] <= now() or claims["server"] != audience:
                raise ValueError
            return dict(claims)
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            raise Denied(
                "PERMISSION_DENIED", "Invalid or expired internal caller assertion"
            ) from exc
