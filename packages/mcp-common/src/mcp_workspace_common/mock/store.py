from __future__ import annotations

import asyncio
import hashlib
import json
import uuid
from pathlib import Path
from typing import Any

from mcp_workspace_common.mock.fixtures import synthetic_workspace
from mcp_workspace_common.mock.lookup import _find

_LOCKS: dict[str, asyncio.Lock] = {}


class MockStore:
    def __init__(self, root: Path, user_id: str) -> None:
        self.directory = root / "mock_workspace" / hashlib.sha256(user_id.encode()).hexdigest()
        self.path = self.directory / "state.json"
        self.lock = _LOCKS.setdefault(str(self.path.resolve()), asyncio.Lock())

    def _load(self) -> dict[str, Any]:
        return json.loads(self.path.read_text()) if self.path.exists() else synthetic_workspace()

    def _save(self, state: dict[str, Any]) -> None:
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        temporary = self.directory / f"state-{uuid.uuid4().hex}.tmp"
        temporary.write_text(json.dumps(state), encoding="utf-8")
        temporary.chmod(0o600)
        temporary.replace(self.path)

    _find = staticmethod(_find)
