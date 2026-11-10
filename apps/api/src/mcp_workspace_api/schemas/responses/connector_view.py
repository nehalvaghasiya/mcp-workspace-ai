from typing import Literal

from mcp_workspace_api.contracts import StrictModel


class ConnectorView(StrictModel):
    id: str
    name: str
    status: str
    scopes: list[str]
    enabled: bool
    mode: Literal["mock", "live"]
