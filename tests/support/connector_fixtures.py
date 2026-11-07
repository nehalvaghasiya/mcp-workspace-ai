from __future__ import annotations

from pathlib import Path

import pytest
from mcp_workspace_api.connectors import (
    MockWorkspace,
)


@pytest.fixture
def workspace(tmp_path: Path) -> MockWorkspace:
    return MockWorkspace(tmp_path, "user-a")


async def token() -> str:
    return "CANARY_FAKE_ACCESS_TOKEN"
