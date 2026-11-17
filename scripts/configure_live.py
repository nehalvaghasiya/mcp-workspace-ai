"""Activate existing real credentials without printing or replacing them."""

from __future__ import annotations

import os
import secrets
import sqlite3
from pathlib import Path

from cryptography.fernet import Fernet
from dotenv import dotenv_values, set_key

ROOT = Path(__file__).resolve().parents[1]


def configure(path: Path) -> None:
    if not path.is_file():
        raise SystemExit("Create the project .env with Google OAuth and LLM credentials first")
    values = dotenv_values(path)
    required = ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "LLM_API_KEY", "LLM_MODEL")
    missing = [name for name in required if not values.get(name)]
    if missing:
        raise SystemExit("Missing configuration: " + ", ".join(missing))
    directory = Path(values.get("DATA_DIR") or ".local")
    if not directory.is_absolute():
        directory = ROOT / directory
    key = values.get("TOKEN_ENCRYPTION_KEY") or ""
    try:
        Fernet(key.encode())
    except ValueError:
        database = directory / "live" / "workspace.db"
        if database.is_file():
            with sqlite3.connect(f"file:{database}?mode=ro", uri=True) as connection:
                exists = connection.execute(
                    "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='google_accounts'"
                ).fetchone()[0]
                if (
                    exists
                    and connection.execute(
                        "SELECT count(*) FROM google_accounts WHERE credentials != 'mock'"
                    ).fetchone()[0]
                ):
                    raise SystemExit(
                        "Existing live credentials require their original valid encryption key. Restore that key or use the documented vault recovery flow; no credentials were changed."
                    ) from None
        key = Fernet.generate_key().decode()
    updates = {
        "MODE": "live",
        "LLM_PROVIDER": "openai_compatible",
        "TOKEN_ENCRYPTION_KEY": key,
    }
    if len(values.get("SESSION_SECRET") or "") < 32:
        updates["SESSION_SECRET"] = secrets.token_urlsafe(48)
    if not values.get("DATA_DIR"):
        updates["DATA_DIR"] = ".local"
    for name, value in updates.items():
        set_key(path, name, value)
    os.chmod(path, 0o600)
    print(
        "Live mode enabled. Google/model credentials preserved; encryption key validated and stored privately."
    )


if __name__ == "__main__":
    configure(ROOT / ".env")
