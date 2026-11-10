from __future__ import annotations

from typing import Literal

from mcp_workspace_api.contracts import StrictModel


class Decision(StrictModel):
    decision: Literal["approve", "reject"]
