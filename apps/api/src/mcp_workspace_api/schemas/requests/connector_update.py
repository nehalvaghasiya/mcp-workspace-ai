from __future__ import annotations

from mcp_workspace_api.contracts import StrictModel


class ConnectorUpdate(StrictModel):
    enabled: bool
