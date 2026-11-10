from __future__ import annotations

import re

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from mcp_workspace_api.db import Database, GoogleAccount
from mcp_workspace_api.operations.rotation_error import RotationError


def rotate_credentials(database: Database, old_key: str, new_key: str, key_version: str) -> int:
    """Re-encrypt every real credential atomically while the app is stopped.

    The operator must replace TOKEN_ENCRYPTION_KEY and TOKEN_KEY_VERSION before
    restarting. This function does not persist or print either encryption key.
    """
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", key_version):
        raise RotationError("Key version must be a nonempty identifier of at most 64 characters")
    try:
        original = Fernet(old_key.encode())
        replacement = Fernet(new_key.encode())
    except (ValueError, TypeError, UnicodeError):
        raise RotationError(
            "Provide valid original and replacement credential encryption keys"
        ) from None
    count = 0
    try:
        with database.session() as session:
            accounts = session.scalars(
                select(GoogleAccount).order_by(GoogleAccount.id).with_for_update()
            )
            for account in accounts:
                if account.credentials == "mock":
                    continue
                plaintext = original.decrypt(account.credentials.encode())
                account.credentials = replacement.encrypt(plaintext).decode()
                account.key_version = key_version
                count += 1
    except (InvalidToken, UnicodeError, SQLAlchemyError):
        raise RotationError(
            "Credential rotation failed; no credentials changed. Check the original key and vault integrity"
        ) from None
    return count
