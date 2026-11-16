from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

import httpx
from mcp_calendar.providers.google import GoogleCalendar
from mcp_drive.providers.google import GoogleDrive
from mcp_gmail.providers.google import GoogleGmail
from mcp_google_docs.providers.google import GoogleDocs
from mcp_sheets.providers.google import GoogleSheets
from mcp_slides.providers.google import GoogleSlides
from mcp_workspace_common.errors import ConnectorError
from mcp_workspace_common.providers.google_client import GoogleClient


class GoogleWorkspace:
    def __init__(
        self,
        token_provider: Callable[[], Awaitable[str]],
        client: httpx.AsyncClient | None = None,
        on_result: Callable[[str | None, str], None] | None = None,
    ) -> None:
        self.transport = GoogleClient(token_provider, client)
        self._request = self.transport.request
        self.on_result = on_result
        self.providers: dict[str, Any] = {
            "gmail": GoogleGmail(self.transport),
            "calendar": GoogleCalendar(self.transport),
            "drive": GoogleDrive(self.transport),
            "docs": GoogleDocs(self.transport),
            "sheets": GoogleSheets(self.transport),
            "slides": GoogleSlides(self.transport),
        }

    async def call(self, server: str, tool: str, args: dict[str, Any]) -> dict[str, Any]:
        if server not in self.providers:
            raise ConnectorError("unknown_tool", "Unknown workspace tool")
        try:
            result = dict(await self.providers[server].call(tool, args))
        except ConnectorError as error:
            if self.on_result:
                self.on_result(error.code, server)
            raise
        if self.on_result:
            self.on_result(None, server)
        return result

    async def snapshot(self, server: str, tool: str, args: dict[str, Any]) -> dict[str, Any]:
        try:
            return (
                dict(await self.providers[server].snapshot(tool, args))
                if server in self.providers
                else {}
            )
        except ConnectorError as error:
            if self.on_result:
                self.on_result(error.code, server)
            raise

    async def aclose(self) -> None:
        await self.transport.aclose()
