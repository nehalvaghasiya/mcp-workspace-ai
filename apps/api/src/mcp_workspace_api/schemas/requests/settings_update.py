from __future__ import annotations

from mcp_workspace_api.contracts import StrictModel


class SettingsUpdate(StrictModel):
    llm_consent: bool | None = None
    timezone: str | None = None
