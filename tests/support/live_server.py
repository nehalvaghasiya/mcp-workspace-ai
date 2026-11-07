from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

import httpx
import httpx2
from fastapi import FastAPI
from mcp import Client
from mcp.client.streamable_http import streamable_http_client
from mcp_workspace_api.core.config import Settings
from mcp_workspace_api.core.execution_context import Runtime

from tests.support.browser import Browser


@dataclass
class LiveServer:
    app: FastAPI
    settings: Settings

    @property
    def runtime(self) -> Runtime:
        return self.app.state.runtime

    @property
    def url(self) -> str:
        return self.settings.api_url

    @asynccontextmanager
    async def browser(self) -> AsyncIterator[Browser]:
        async with httpx.AsyncClient(base_url=self.url, timeout=30) as http:
            response = await http.post(
                "/api/auth/demo", headers={"Origin": self.settings.web_origin}
            )
            assert response.status_code == 200, response.text
            payload = response.json()
            http.headers.update(
                {"X-CSRF-Token": payload["csrf_token"], "Origin": self.settings.web_origin}
            )
            yield Browser(http=http, user_id=payload["user"]["id"], csrf=payload["csrf_token"])

    @asynccontextmanager
    async def mcp(
        self,
        user_id: str,
        namespace: str,
        *,
        tools: list[str] | None = None,
        run_id: str = "",
        approval: dict[str, str] | None = None,
    ) -> AsyncIterator[Client]:
        authority = (
            tools
            if tools is not None
            else [name for name in self.runtime.tools if name.startswith(namespace + ".")]
        )
        token = self.runtime.signer.issue(
            {
                "user_id": user_id,
                "server": namespace,
                "tools": authority,
                "run_id": run_id,
                "approval": approval,
            }
        )

        @asynccontextmanager
        async def transport() -> AsyncIterator[Any]:
            async with httpx2.AsyncClient(
                headers={"Authorization": "Bearer " + token}, timeout=10
            ) as http:
                async with streamable_http_client(
                    f"{self.url}/mcp/{namespace}/", http_client=http
                ) as streams:
                    yield streams

        async with Client(transport(), read_timeout_seconds=10) as client:
            yield client
