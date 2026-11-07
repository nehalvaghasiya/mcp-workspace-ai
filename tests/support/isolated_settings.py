from __future__ import annotations

from mcp_workspace_api.core.config import Settings
from pydantic_settings import SettingsConfigDict


class IsolatedSettings(Settings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")
