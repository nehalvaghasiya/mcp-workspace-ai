"""Load project configuration without unrelated inherited storage overrides."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import dotenv_values

from mcp_workspace_api.core.config import Settings


def load_settings() -> Settings:
    directory = os.environ.get("WORKSPACE_DATA_DIR") or dotenv_values(".env").get("DATA_DIR")
    return Settings(data_dir=Path(directory)) if directory else Settings()


def validate_live_configuration(settings: Settings) -> None:
    if settings.mode != "live":
        return
    if settings.llm_provider != "openai_compatible":
        raise ValueError(
            "Live mode requires LLM_PROVIDER=openai_compatible; FakeLLM is only for tests and explicit demos"
        )
    missing = [
        name
        for name, value in (
            ("LLM_MODEL", settings.llm_model),
            ("LLM_API_KEY", settings.llm_api_key),
            ("GOOGLE_CLIENT_ID", settings.google_client_id),
            ("GOOGLE_CLIENT_SECRET", settings.google_client_secret),
        )
        if not value
    ]
    if missing:
        raise ValueError("Live configuration is missing: " + ", ".join(missing))
