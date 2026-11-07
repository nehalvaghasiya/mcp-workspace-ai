import json
from importlib.resources import files
from typing import Any

from mcp_workspace_common.constants import DEMO_NOW

__all__ = ["synthetic_workspace", "DEMO_NOW"]


def synthetic_workspace() -> dict[str, Any]:
    """Load a fresh copy of the frozen Northstar fixture from the installed package."""
    return dict(
        json.loads(files("mcp_workspace_common.mock").joinpath("assets/workspace.json").read_text())
    )
