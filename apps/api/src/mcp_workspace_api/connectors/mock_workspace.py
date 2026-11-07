from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from mcp_calendar.providers.mock import MockCalendar
from mcp_drive.providers.mock import MockDrive
from mcp_gmail.providers.mock import MockGmail
from mcp_workspace_common.errors import ConnectorError
from mcp_workspace_common.mock.store import MockStore


class MockWorkspace(MockStore):
    def __init__(self, root: Path, user_id: str) -> None:
        super().__init__(root, user_id)
        self.providers: dict[str, Any] = {
            "gmail": MockGmail(),
            "calendar": MockCalendar(),
            "drive": MockDrive(),
        }

    async def call(self, server: str, tool: str, args: dict[str, Any]) -> dict[str, Any]:
        async with self.lock:
            state = self._load()
            if server not in self.providers:
                raise ConnectorError("unknown_tool", "Unknown workspace tool")
            result, write = self.providers[server].call(state, tool, args)
            if write:
                self._save(state)
            return copy.deepcopy(result) | {"synthetic": True}

    async def snapshot(self, server: str, tool: str, args: dict[str, Any]) -> dict[str, Any]:
        async with self.lock:
            return (
                self.providers[server].snapshot(self._load(), tool, args)
                if server in self.providers
                else {}
            )

    async def aclose(self) -> None:
        return None
