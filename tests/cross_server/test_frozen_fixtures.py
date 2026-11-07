from __future__ import annotations

import hashlib
import json
from pathlib import Path

from mcp_workspace_api.connectors import (
    synthetic_workspace,
)


def test_fixture_manifest_and_counts() -> None:
    directory = Path(__file__).resolve().parents[1] / "fixtures" / "synthetic"
    manifest = json.loads((directory / "manifest.json").read_text())
    assert (
        hashlib.sha256((directory / "workspace.json").read_bytes()).hexdigest()
        == manifest["workspace.json"]
    )
    state = json.loads((directory / "workspace.json").read_text())
    assert state == synthetic_workspace()
    assert len(state["messages"]) == 32
    assert len(state["events"]) == 20
    assert len(state["files"]) == 22
