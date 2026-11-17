from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from cryptography.fernet import Fernet, InvalidToken
from mcp_workspace_api.cli import WorkspaceBackupError, backup_workspace, restore_workspace
from mcp_workspace_api.cli import commands as cli
from mcp_workspace_api.core.config import Settings
from mcp_workspace_api.core.security import RotationError, rotate_credentials
from mcp_workspace_api.db import Artifact, Database, GoogleAccount, User
from mcp_workspace_api.db import migrate as security
from mcp_workspace_api.db.migrate import migrate
from sqlalchemy import inspect, select, text

from tests.support.isolated_settings import IsolatedSettings


@pytest.fixture
def vault(tmp_path: Path) -> Iterator[tuple[Database, str, str]]:
    database = Database(f"sqlite:///{tmp_path / 'vault.db'}")
    migrate(database)
    original, replacement = Fernet.generate_key().decode(), Fernet.generate_key().decode()
    with database.session() as session:
        for index in range(3):
            user = User(id=f"user-{index}", subject=f"synthetic-sub-{index}")
            session.add(user)
            session.flush()
            payload = json.dumps(
                {
                    "access_token": f"CANARY_ACCESS_{index}",
                    "refresh_token": f"CANARY_REFRESH_{index}",
                }
            ).encode()
            session.add(
                GoogleAccount(
                    id=f"account-{index}",
                    user_id=user.id,
                    subject=user.subject,
                    credentials="mock"
                    if index == 2
                    else Fernet(original.encode()).encrypt(payload).decode(),
                    key_version="v1",
                    scopes=[],
                    enabled=[],
                )
            )
    try:
        yield database, original, replacement
    finally:
        database.engine.dispose()


def records(database: Database) -> list[tuple[str, str, str]]:
    with database.session() as session:
        return [
            (row.id, row.credentials, row.key_version)
            for row in session.scalars(select(GoogleAccount).order_by(GoogleAccount.id))
        ]


def test_rotation_reencrypts_all_real_credentials_and_preserves_mock(
    vault: tuple[Database, str, str],
) -> None:
    database, original, replacement = vault
    before = records(database)
    assert rotate_credentials(database, original, replacement, "rotation-2026-11") == 2
    after = records(database)
    for old, new in zip(before[:2], after[:2], strict=True):
        assert old[1] != new[1]
        assert Fernet(original.encode()).decrypt(old[1].encode()) == Fernet(
            replacement.encode()
        ).decrypt(new[1].encode())
        assert new[2] == "rotation-2026-11"
        with pytest.raises(InvalidToken):
            Fernet(original.encode()).decrypt(new[1].encode())
    assert before[2] == after[2] and after[2][1] == "mock"


def test_rotation_invalid_later_record_rolls_back_every_row(
    vault: tuple[Database, str, str],
) -> None:
    database, original, replacement = vault
    with database.session() as session:
        row = session.get(GoogleAccount, "account-1")
        assert row is not None
        row.credentials = Fernet(Fernet.generate_key()).encrypt(b"CANARY_OTHER_KEY").decode()
    before = records(database)
    with pytest.raises(RotationError) as caught:
        rotate_credentials(database, original, replacement, "v2")
    assert records(database) == before
    assert "CANARY" not in str(caught.value) and original not in str(caught.value)


@pytest.mark.parametrize("which", ["original", "replacement"])
def test_invalid_key_fails_without_disclosure_or_changes(
    vault: tuple[Database, str, str], which: str
) -> None:
    database, original, replacement = vault
    before = records(database)
    with pytest.raises(RotationError) as caught:
        rotate_credentials(
            database,
            "CANARY_INVALID_KEY" if which == "original" else original,
            "CANARY_INVALID_KEY" if which == "replacement" else replacement,
            "v2",
        )
    assert "CANARY_INVALID_KEY" not in str(caught.value)
    assert records(database) == before


@pytest.mark.parametrize("version", ["", "x" * 65, "../v2", "v2\nsecret"])
def test_version_validation_is_bounded(vault: tuple[Database, str, str], version: str) -> None:
    database, original, replacement = vault
    before = records(database)
    with pytest.raises(RotationError):
        rotate_credentials(database, original, replacement, version)
    assert records(database) == before


def test_key_version_migration_sqlite_upgrade_and_batch_downgrade(
    vault: tuple[Database, str, str],
) -> None:
    database, _, _ = vault
    before = records(database)
    config = Config()
    config.set_main_option("script_location", str(Path(security.__file__).parent / "migrations"))
    with database.engine.begin() as connection:
        config.attributes["connection"] = connection
        command.downgrade(config, "0001")
    assert "key_version" not in {
        column["name"] for column in inspect(database.engine).get_columns("google_accounts")
    }
    with database.engine.connect() as connection:
        assert list(
            connection.execute(text("SELECT id, credentials FROM google_accounts ORDER BY id"))
        ) == [(row[0], row[1]) for row in before]
    migrate(database)
    assert records(database) == before


def source_workspace(tmp_path: Path, key: str) -> tuple[Settings, Database, str]:
    settings = IsolatedSettings(
        mode="live",
        data_dir=tmp_path / "source",
        session_secret="synthetic-session-secret",
        token_encryption_key=key,
        token_key_version="original-version",
    )
    settings.prepare()
    database = Database(f"sqlite:///{settings.storage / 'workspace.db'}")
    migrate(database)
    with database.session() as session:
        user = User(id="synthetic-owner", subject="synthetic-sub")
        session.add(user)
        session.flush()
        session.add(
            GoogleAccount(
                id="synthetic-account",
                user_id=user.id,
                subject=user.subject,
                credentials=Fernet(key.encode())
                .encrypt(b'{"refresh_token":"CANARY_BACKUP_SECRET"}')
                .decode(),
                key_version="original-version",
                scopes=[],
                enabled=[],
            )
        )
        path = settings.storage / "artifacts" / user.id / "report.md"
        path.parent.mkdir(parents=True)
        path.write_text("Synthetic portable artifact")
        session.add(
            Artifact(
                user_id=user.id,
                title="Report",
                format="markdown",
                mime_type="text/markdown",
                storage_key=str(path.relative_to(settings.storage)),
                size=path.stat().st_size,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                sources=[],
            )
        )
    return settings, database, "artifacts/synthetic-owner/report.md"


def target_settings(tmp_path: Path, key: str) -> Settings:
    settings = IsolatedSettings(
        mode="live",
        data_dir=tmp_path / "restored",
        session_secret="synthetic-new-session-secret",
        token_encryption_key=key,
        token_key_version="original-version",
    )
    settings.prepare()
    return settings


def test_backup_restore_keeps_ciphertext_versions_and_artifact_bytes(tmp_path: Path) -> None:
    key = Fernet.generate_key().decode()
    settings, original, storage_key = source_workspace(tmp_path, key)
    try:
        expected = records(original)
        backup = tmp_path / "backup"
        backup_workspace(settings, backup)
        restored = target_settings(tmp_path, key)
        restore_workspace(restored, backup)
        database = Database(f"sqlite:///{restored.storage / 'workspace.db'}")
        try:
            assert records(database) == expected
            assert (
                Fernet(key.encode()).decrypt(records(database)[0][1].encode())
                == b'{"refresh_token":"CANARY_BACKUP_SECRET"}'
            )
            assert (restored.storage / storage_key).read_bytes() == (
                settings.storage / storage_key
            ).read_bytes()
        finally:
            database.engine.dispose()
    finally:
        original.engine.dispose()


@pytest.mark.parametrize("existing", ["workspace.db", "artifacts"])
def test_restore_refuses_existing_data_without_overwrite(tmp_path: Path, existing: str) -> None:
    key = Fernet.generate_key().decode()
    settings, database, _ = source_workspace(tmp_path, key)
    try:
        backup = tmp_path / "backup"
        backup_workspace(settings, backup)
        restored = target_settings(tmp_path, key)
        path = restored.storage / existing
        if existing == "artifacts":
            path.mkdir()
            path = path / "preserve.txt"
        path.write_bytes(b"EXISTING_SYNTHETIC_DATA")
        with pytest.raises(WorkspaceBackupError, match="fresh storage"):
            restore_workspace(restored, backup)
        assert path.read_bytes() == b"EXISTING_SYNTHETIC_DATA"
    finally:
        database.engine.dispose()


def test_restore_wrong_key_creates_no_restored_data(tmp_path: Path) -> None:
    key = Fernet.generate_key().decode()
    settings, database, _ = source_workspace(tmp_path, key)
    try:
        backup = tmp_path / "backup"
        backup_workspace(settings, backup)
        restored = target_settings(tmp_path, Fernet.generate_key().decode())
        with pytest.raises(WorkspaceBackupError, match="original configured"):
            restore_workspace(restored, backup)
        assert not (restored.storage / "workspace.db").exists()
        assert not (restored.storage / "artifacts").exists()
    finally:
        database.engine.dispose()


def test_backup_refuses_existing_destination_and_symlink_artifact(tmp_path: Path) -> None:
    key = Fernet.generate_key().decode()
    settings, database, _ = source_workspace(tmp_path, key)
    try:
        backup = tmp_path / "backup"
        backup.mkdir()
        marker = backup / "preserve.txt"
        marker.write_text("Existing backup")
        with pytest.raises(WorkspaceBackupError):
            backup_workspace(settings, backup)
        assert marker.read_text() == "Existing backup"
        outside = tmp_path / "outside.txt"
        outside.write_text("Synthetic secret")
        (settings.storage / "artifacts" / "unsafe-link").symlink_to(outside)
        with pytest.raises(WorkspaceBackupError, match="symlinks"):
            backup_workspace(settings, tmp_path / "new-backup")
        assert not (tmp_path / "new-backup").exists()
    finally:
        database.engine.dispose()


def test_rotation_cli_reads_key_from_environment_and_never_prints_secrets(
    vault: tuple[Database, str, str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    database, original, replacement = vault
    settings = IsolatedSettings(data_dir=tmp_path, token_encryption_key=original)
    settings.prepare()
    # The isolated fixture DB is the only DB exposed to the command.
    monkeypatch.setattr(cli, "load_settings", lambda: settings)
    monkeypatch.setattr(cli, "Database", lambda url: database)
    monkeypatch.setenv("NEW_TOKEN_ENCRYPTION_KEY", replacement)
    (settings.storage / "workspace.db").touch()
    monkeypatch.setattr("sys.argv", ["workspace-ai", "rotate-key", "--key-version", "v2-cli"])
    cli.main()
    output = capsys.readouterr()
    assert "Rotated 2 credential records" in output.out
    assert "TOKEN_KEY_VERSION" in output.out and "v2-cli" in output.out
    assert all(
        secret not in output.out + output.err
        for secret in [original, replacement, "CANARY_ACCESS", "CANARY_REFRESH"]
    )
    assert records(database)[0][2] == "v2-cli"


def test_rotation_cli_requires_new_key_environment(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv("NEW_TOKEN_ENCRYPTION_KEY", raising=False)
    monkeypatch.setattr("sys.argv", ["workspace-ai", "rotate-key"])
    with pytest.raises(SystemExit, match="NEW_TOKEN_ENCRYPTION_KEY"):
        cli.main()
    assert not capsys.readouterr().out


def test_backup_restore_cli_lifecycle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    key = Fernet.generate_key().decode()
    settings, database, storage_key = source_workspace(tmp_path, key)
    try:
        backup = tmp_path / "cli-backup"
        monkeypatch.setattr(cli, "load_settings", lambda: settings)
        monkeypatch.setattr("sys.argv", ["workspace-ai", "backup", str(backup)])
        cli.main()
        restored = target_settings(tmp_path, key)
        monkeypatch.setattr(cli, "load_settings", lambda: restored)
        monkeypatch.setattr("sys.argv", ["workspace-ai", "restore", str(backup)])
        cli.main()
        assert (restored.storage / storage_key).is_file()
        output = capsys.readouterr()
        assert "restored to fresh storage" in output.out
        assert (
            key not in output.out + output.err
            and "CANARY_BACKUP_SECRET" not in output.out + output.err
        )
    finally:
        database.engine.dispose()
