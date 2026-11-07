from __future__ import annotations

from typing import Any

import httpx


class StubModel:
    requests: list[dict[str, Any]] = []

    def __init__(self, **kwargs: Any) -> None:
        pass

    async def __aenter__(self) -> StubModel:
        return self

    async def __aexit__(self, *args: Any) -> None:
        return None

    async def post(self, url: str, **kwargs: Any) -> httpx.Response:
        self.requests.append(kwargs)
        return httpx.Response(
            200, json={"choices": [{"message": {"content": "Cited synthetic answer"}}]}
        )
