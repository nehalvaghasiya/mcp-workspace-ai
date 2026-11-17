from typing import Literal

from pydantic import Field

from mcp_workspace_api.contracts import StrictModel


class ConnectorView(StrictModel):
    id: str
    name: str
    status: str
    scopes: list[str]
    enabled: bool
    mode: Literal["mock", "live"]
    available_capabilities: list[str] = Field(default_factory=list)
    missing_scopes: list[str] = Field(default_factory=list)
    last_error: str | None = None
    last_checked_at: str | None = None
