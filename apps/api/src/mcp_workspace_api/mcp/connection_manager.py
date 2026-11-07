from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

import httpx2
from mcp import Client
from mcp.client.streamable_http import streamable_http_client

if TYPE_CHECKING:
    from mcp_workspace_api.core.execution_context import Runtime


class ConnectionManager:
    def __init__(self, context: Runtime) -> None:
        self.context = context

    def adapter(self, user_id: str) -> Any:
        context = self.context
        from mcp_workspace_api.connectors import GoogleWorkspace, MockWorkspace

        if user_id not in context.adapters:
            if context.settings.mode == "mock":
                context.adapters[user_id] = MockWorkspace(
                    context.settings.storage / "fixtures", user_id
                )
            else:
                context.adapters[user_id] = GoogleWorkspace(lambda: context.token(user_id))
        return context.adapters[user_id]

    @asynccontextmanager
    async def client(
        self,
        user_id: str,
        server: str,
        *,
        run_id: str = "",
        approval: dict[str, str] | None = None,
        tools: list[str] | None = None,
    ) -> AsyncIterator[Client]:
        context = self.context
        token = context.signer.issue(
            {
                "user_id": user_id,
                "server": server,
                "tools": tools or ["read"],
                "run_id": run_id,
                "approval": approval,
            }
        )

        @asynccontextmanager
        async def transport() -> AsyncIterator[Any]:
            async with httpx2.AsyncClient(
                headers={"Authorization": "Bearer " + token}, timeout=context.settings.tool_timeout
            ) as http:
                async with streamable_http_client(
                    f"{context.settings.api_url}/mcp/{server}/", http_client=http
                ) as streams:
                    yield streams

        async with Client(
            transport(), read_timeout_seconds=context.settings.tool_timeout
        ) as client:
            yield client
