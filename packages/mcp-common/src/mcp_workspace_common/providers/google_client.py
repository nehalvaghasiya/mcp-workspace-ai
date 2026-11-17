from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from typing import Any
from urllib.parse import urlsplit

import httpx

from mcp_workspace_common.errors import ConnectorError
from mcp_workspace_common.extraction import MAX_FILE_BYTES


class GoogleClient:
    def __init__(
        self, token_provider: Callable[[], Awaitable[str]], client: httpx.AsyncClient | None = None
    ) -> None:
        self.token_provider = token_provider
        self.client = client or httpx.AsyncClient(
            timeout=15, follow_redirects=False, trust_env=False
        )
        self._owns_client = client is None

    async def request(
        self, method: str, url: str, *, read: bool = False, binary: bool = False, **kwargs: Any
    ) -> Any:
        parsed = urlsplit(url)
        if (
            parsed.scheme != "https"
            or parsed.hostname
            not in {
                "gmail.googleapis.com",
                "www.googleapis.com",
                "docs.googleapis.com",
                "sheets.googleapis.com",
                "slides.googleapis.com",
            }
            or parsed.port not in {None, 443}
        ):
            raise ConnectorError("unsafe_url", "Provider URL is not allowed")
        request_headers = dict(kwargs.pop("headers", {}))
        for attempt in range(3 if read else 1):
            token = await self.token_provider()
            headers = request_headers | {"Authorization": f"Bearer {token}"}
            try:
                async with self.client.stream(
                    method, url, headers=headers, timeout=15, follow_redirects=False, **kwargs
                ) as response:
                    if response.status_code == 401:
                        raise ConnectorError(
                            "auth_required", "Google connection expired; reconnect"
                        )
                    if response.status_code == 403:
                        raise ConnectorError(
                            "permission_denied",
                            "Google permission or granted scope is insufficient",
                        )
                    if response.status_code == 404:
                        raise ConnectorError("not_found", "Resource not found or inaccessible")
                    if response.status_code in {409, 412}:
                        raise ConnectorError(
                            "stale_action", "Provider resource changed; request a fresh approval"
                        )
                    if read and response.status_code in {429, 500, 502, 503, 504} and attempt < 2:
                        await asyncio.sleep(0.05 * 2**attempt)
                        continue
                    if response.status_code >= 500 and not read:
                        raise ConnectorError(
                            "outcome_unknown",
                            "Google write outcome is unknown; reconcile before retrying",
                        )
                    if response.status_code == 429:
                        raise ConnectorError("rate_limited", "Google quota exceeded; retry later")
                    if response.status_code >= 300:
                        raise ConnectorError("provider_error", "Google rejected the request")
                    parts: list[bytes] = []
                    size = 0
                    async for chunk in response.aiter_bytes():
                        size += len(chunk)
                        if size > MAX_FILE_BYTES:
                            raise ConnectorError(
                                "response_too_large" if read else "outcome_unknown",
                                "Provider response exceeds 10 MiB limit"
                                if read
                                else "Google write outcome is unknown; reconcile before retrying",
                            )
                        parts.append(chunk)
                    content = b"".join(parts)
                    if binary:
                        return content
                    if not content:
                        return {}
                    value = json.loads(content)
                    if not isinstance(value, dict):
                        raise ConnectorError(
                            "invalid_provider_response" if read else "outcome_unknown",
                            "Invalid Google response"
                            if read
                            else "Google write outcome is unknown; reconcile before retrying",
                        )
                    return value
            except httpx.HTTPError:
                if not read:
                    raise ConnectorError(
                        "outcome_unknown",
                        "Google write outcome is unknown; reconcile before retrying",
                    ) from None
                if attempt == 2:
                    raise ConnectorError(
                        "provider_unavailable", "Google is temporarily unavailable"
                    ) from None
                await asyncio.sleep(0.05 * 2**attempt)
            except (json.JSONDecodeError, UnicodeDecodeError):
                raise ConnectorError(
                    "invalid_provider_response" if read else "outcome_unknown",
                    "Invalid Google response"
                    if read
                    else "Google write outcome is unknown; reconcile before retrying",
                ) from None
        raise ConnectorError("provider_unavailable", "Google is temporarily unavailable")

    async def aclose(self) -> None:
        if self._owns_client:
            await self.client.aclose()
