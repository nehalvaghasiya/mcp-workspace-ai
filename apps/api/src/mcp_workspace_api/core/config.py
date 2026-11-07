from __future__ import annotations

import base64
import hashlib
import os
import secrets
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", hide_input_in_errors=True)
    mode: Literal["mock", "live"] = "mock"
    data_dir: Path = Path(".local")
    web_dist_dir: Path = Path("apps/web/dist")
    api_url: str = "http://127.0.0.1:8000"
    web_origin: str = "http://localhost:5173"
    session_secret: str = ""
    token_encryption_key: str = ""
    token_key_version: str = Field(
        default="v1", min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_.-]+$"
    )
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/auth/google/callback"
    llm_provider: Literal["fake", "openai_compatible"] = "fake"
    llm_model: str = ""
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    max_tool_calls: int = Field(default=24, ge=1, le=100)
    run_timeout: int = Field(default=180, ge=1, le=600)
    tool_timeout: int = Field(default=30, ge=1, le=120)
    approval_ttl: int = Field(default=300, ge=15, le=900)
    retention_days: int = Field(default=30, ge=1, le=3650)
    max_artifact_bytes: int = Field(default=10 * 1024 * 1024, ge=1024, le=10 * 1024 * 1024)
    max_user_artifacts: int = Field(default=100, ge=1, le=10000)
    max_user_artifact_bytes: int = Field(default=100 * 1024 * 1024, ge=1024)

    @field_validator("llm_base_url")
    @classmethod
    def provider_endpoint(cls, value: str) -> str:
        url = urlsplit(value)
        if (
            url.scheme not in {"http", "https"}
            or not url.hostname
            or url.username
            or url.password
            or url.query
            or url.fragment
        ):
            raise ValueError(
                "Model endpoint must be an HTTP(S) base URL without credentials, query or fragment"
            )
        return value.rstrip("/")

    @property
    def storage(self) -> Path:
        return self.data_dir.resolve() / self.mode

    def prepare(self) -> None:
        if self.mode == "mock" and self.llm_provider != "fake":
            raise ValueError("Mock mode requires FakeLLM and never contacts a model provider")
        self.storage.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.mode == "live" and (not self.session_secret or not self.token_encryption_key):
            raise ValueError("Live mode requires SESSION_SECRET and TOKEN_ENCRYPTION_KEY")
        if not self.session_secret:
            path = self.storage / "secret"
            if not path.exists():
                fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                with os.fdopen(fd, "w") as stream:
                    stream.write(secrets.token_hex(32))
            self.session_secret = path.read_text().strip()
        if not self.token_encryption_key:
            self.token_encryption_key = base64.urlsafe_b64encode(
                hashlib.sha256((self.session_secret + ":vault").encode()).digest()
            ).decode()
