from __future__ import annotations

import os
import shutil
import sqlite3
from pathlib import Path

from mcp_workspace_api.core.config import Settings
from mcp_workspace_api.operations.backup_error import WorkspaceBackupError


def _artifact_tree(directory: Path) -> None:
    if directory.is_symlink() or (directory.exists() and not directory.is_dir()):
        raise WorkspaceBackupError("Artifact storage must be a regular directory without symlinks")
    if directory.exists() and any(path.is_symlink() for path in directory.rglob("*")):
        raise WorkspaceBackupError("Artifact storage must not contain symlinks")


def _sqlite_snapshot(source: Path, destination: Path) -> None:
    # Reserve the new file exclusively. A concurrent process must never turn a
    # fresh-only restore into an overwrite of an existing database.
    descriptor = os.open(destination, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(descriptor)
    with (
        sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True) as original,
        sqlite3.connect(destination) as copied,
    ):
        original.backup(copied)


def backup_workspace(settings: Settings, destination: Path) -> None:
    """Snapshot a stopped app's DB and artifacts into a new private directory."""
    source = settings.storage / "workspace.db"
    artifacts = settings.storage / "artifacts"
    if not source.is_file() or source.is_symlink():
        raise WorkspaceBackupError("An existing regular workspace database is required")
    if destination.resolve().is_relative_to(settings.storage):
        raise WorkspaceBackupError("Backup destination must be outside workspace storage")
    _artifact_tree(artifacts)
    try:
        destination.mkdir(parents=True, exist_ok=False, mode=0o700)
        _sqlite_snapshot(source, destination / "workspace.db")
        if artifacts.exists():
            shutil.copytree(artifacts, destination / "artifacts")
    except (OSError, sqlite3.Error):
        raise WorkspaceBackupError(
            "Backup failed; use a new destination and inspect any partial backup. Existing data was not replaced"
        ) from None


def restore_workspace(settings: Settings, source: Path) -> None:
    """Restore to fresh storage only, with the operator's original vault key."""
    from cryptography.fernet import Fernet, InvalidToken

    database = source / "workspace.db"
    artifacts = source / "artifacts"
    target_database = settings.storage / "workspace.db"
    target_artifacts = settings.storage / "artifacts"
    if not database.is_file() or database.is_symlink():
        raise WorkspaceBackupError("Backup must contain a regular workspace database")
    if settings.storage.is_relative_to(source.resolve()):
        raise WorkspaceBackupError("Restore destination must be outside the backup directory")
    if any(path.exists() or path.is_symlink() for path in (target_database, target_artifacts)):
        raise WorkspaceBackupError(
            "Restore requires fresh storage with no workspace database or artifact directory"
        )
    _artifact_tree(artifacts)
    try:
        # Fail before creating restored data when the operator supplied a wrong
        # key. Mock credentials remain literal and never require decryption.
        with sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True) as backup:
            for (credentials,) in backup.execute("SELECT credentials FROM google_accounts"):
                if credentials != "mock":
                    Fernet(settings.token_encryption_key.encode()).decrypt(credentials.encode())
        settings.storage.mkdir(parents=True, exist_ok=True, mode=0o700)
        _sqlite_snapshot(database, target_database)
        if artifacts.exists():
            shutil.copytree(artifacts, target_artifacts)
    except (InvalidToken, ValueError, UnicodeError):
        raise WorkspaceBackupError(
            "Backup credentials require the original configured TOKEN_ENCRYPTION_KEY; no restored data was created"
        ) from None
    except (OSError, sqlite3.Error):
        raise WorkspaceBackupError(
            "Restore failed; inspect the fresh destination for partial data before retrying. Existing data was not replaced"
        ) from None
