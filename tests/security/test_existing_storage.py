"""Open an actual checkpoint-generated database without resetting private state."""

import json
import shutil
import sqlite3
from pathlib import Path

from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from mcp_workspace_api.core.config import Settings
from mcp_workspace_api.db import GoogleAccount, Operation
from mcp_workspace_api.main import create_app

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures/legacy-storage"


def test_checkpoint_database_preserves_identity_vault_files_and_pending_actions(
    tmp_path: Path,
) -> None:
    manifest = json.loads((FIXTURE / "manifest.json").read_text())
    storage = tmp_path / "mock"
    storage.mkdir()
    with sqlite3.connect(storage / "workspace.db") as database:
        database.executescript((FIXTURE / "workspace.sql").read_text())
    destination = storage / "artifacts/legacy-owner/legacy.csv"
    destination.parent.mkdir(parents=True)
    shutil.copyfile(FIXTURE / "legacy.csv", destination)
    settings = Settings(
        _env_file=None,
        mode="mock",
        llm_provider="fake",
        data_dir=tmp_path,
        session_secret="synthetic-legacy-session-key",
        token_encryption_key=manifest["encryption_key"],
    )
    app = create_app(settings)
    with TestClient(app) as client:
        client.cookies.set("workspace_session", manifest["session_cookie"])
        client.headers["X-CSRF-Token"] = manifest["csrf"]
        assert client.get("/api/session").json()["user"]["id"] == "legacy-owner"
        conversation = client.get("/api/conversations/legacy-conversation").json()
        assert conversation["messages"][0]["content"] == "Retained synthetic answer"
        assert {row["id"]: row["status"] for row in conversation["runs"]} == {
            "legacy-running": "interrupted",
            "legacy-pending": "needs_approval",
        }
        assert (
            client.get("/api/artifacts/legacy-artifact/download").content
            == (FIXTURE / "legacy.csv").read_bytes()
        )
        with app.state.db.session() as session:
            account = session.get(GoogleAccount, "legacy-account")
            assert account is not None and account.key_version == "legacy-v1"
            credentials = json.loads(
                Fernet(manifest["encryption_key"].encode()).decrypt(account.credentials.encode())
            )
            assert credentials["access_token"] == "CANARY_LEGACY_ACCESS"
            operation = session.get(Operation, "legacy-operation")
            assert operation is not None and operation.status == "outcome_unknown"
        approvals = {row["id"]: row for row in client.get("/api/approvals").json()}
        assert approvals["legacy-approval"]["status"] == "pending"
        assert approvals["legacy-approval"]["arguments"]["body_text"] == "Retained exact body"
        assert (
            client.post(
                "/api/approvals/legacy-consumed/decide", json={"decision": "approve"}
            ).status_code
            == 409
        )
        assert (
            client.post(
                "/api/approvals/legacy-approval/decide", json={"decision": "reject"}
            ).status_code
            == 200
        )
        assert not app.state.runtime.tasks and not app.state.runtime.adapters
