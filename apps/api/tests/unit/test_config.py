from __future__ import annotations

import base64
from pathlib import Path

import pytest
from cryptography.fernet import Fernet

from tests.support.isolated_settings import IsolatedSettings


@pytest.mark.parametrize(
    "key", ["synthetic-invalid-key", base64.urlsafe_b64encode(b"short").decode()]
)
def test_mock_invalid_key_uses_a_stable_local_key(
    tmp_path: Path, caplog: pytest.LogCaptureFixture, key: str
) -> None:
    settings = IsolatedSettings(
        mode="mock", data_dir=tmp_path, llm_provider="fake", token_encryption_key=key
    )
    settings.prepare()
    encrypted = Fernet(settings.token_encryption_key.encode()).encrypt(b"synthetic-payload")

    restarted = IsolatedSettings(
        mode="mock", data_dir=tmp_path, llm_provider="fake", token_encryption_key=key
    )
    restarted.prepare()
    assert (
        Fernet(restarted.token_encryption_key.encode()).decrypt(encrypted) == b"synthetic-payload"
    )
    assert "TOKEN_ENCRYPTION_KEY" in caplog.text
    assert "mock" in caplog.text
    assert key not in caplog.text


@pytest.mark.parametrize("mode", ["mock", "live"])
def test_valid_configured_key_is_preserved(tmp_path: Path, mode: str) -> None:
    key = Fernet.generate_key().decode()
    settings = IsolatedSettings(
        mode=mode,
        data_dir=tmp_path,
        llm_provider="fake",
        session_secret="synthetic-session-secret",
        token_encryption_key=key,
    )
    settings.prepare()
    assert settings.token_encryption_key == key


@pytest.mark.parametrize(
    "key", ["synthetic-invalid-key", base64.urlsafe_b64encode(b"short").decode()]
)
def test_live_invalid_key_fails_before_touching_storage(tmp_path: Path, key: str) -> None:
    settings = IsolatedSettings(
        mode="live",
        data_dir=tmp_path,
        session_secret="synthetic-session-secret",
        token_encryption_key=key,
    )
    with pytest.raises(ValueError, match="TOKEN_ENCRYPTION_KEY.*Fernet") as error:
        settings.prepare()
    assert key not in str(error.value)
    assert settings.token_encryption_key == key
    assert not settings.storage.exists()


@pytest.mark.parametrize("session_secret, key", [("", ""), ("synthetic-session-secret", "")])
def test_live_missing_secrets_do_not_create_storage(
    tmp_path: Path, session_secret: str, key: str
) -> None:
    settings = IsolatedSettings(
        mode="live",
        data_dir=tmp_path,
        session_secret=session_secret,
        token_encryption_key=key,
    )
    with pytest.raises(ValueError, match="Live mode requires"):
        settings.prepare()
    assert not settings.storage.exists()
