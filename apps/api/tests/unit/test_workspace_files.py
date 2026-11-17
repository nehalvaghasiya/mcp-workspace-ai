from __future__ import annotations

import base64
from pathlib import Path

import pytest
from mcp_documents.engine import ArtifactEngine
from mcp_documents.schemas.artifact_spec import ArtifactSpec
from mcp_workspace_api.core.security import Denied
from mcp_workspace_api.db import Artifact, User
from mcp_workspace_api.db.migrate import migrate
from mcp_workspace_api.db.models.workspace_file import WorkspaceFile
from mcp_workspace_api.main import create_app
from mcp_workspace_api.services.workspace_file_service import WorkspaceFileService
from sqlalchemy import select

from tests.support.isolated_settings import IsolatedSettings


@pytest.fixture
def native_service(tmp_path: Path) -> WorkspaceFileService:
    app = create_app(
        IsolatedSettings(
            mode="mock",
            llm_provider="fake",
            data_dir=tmp_path,
            token_encryption_key="",
            session_secret="",
        )
    )
    migrate(app.state.db)
    with app.state.db.session() as session:
        session.add_all(
            [
                User(id="owner", subject="synthetic:owner", display_name="Owner"),
                User(id="other", subject="synthetic:other", display_name="Other"),
            ]
        )
    return WorkspaceFileService(app.state.runtime)


def test_native_files_are_owner_scoped_upserted_and_report_partial_results(
    native_service: WorkspaceFileService,
) -> None:
    result = {
        "id": "google-doc-123",
        "title": "First",
        "verified": True,
        "web_url": "https://evil.invalid",
    }
    first = native_service.record("owner", "", "docs", result, {})
    assert first and first.status == "ready"
    assert first.web_url == "https://docs.google.com/document/d/google-doc-123/edit"
    updated = native_service.record(
        "owner", "", "docs", {**result, "title": "Updated", "partial": True}, {}
    )
    assert updated and updated.id == first.id and updated.status == "partial"
    separate = native_service.record("other", "", "docs", result, {})
    assert separate and separate.id != first.id
    with native_service.context.db.session() as session:
        assert len(list(session.scalars(select(WorkspaceFile)))) == 2
    assert native_service.record("owner", "", "docs", {"id": "../escape"}, {}) is None
    assert native_service.record("missing", "", "docs", result, {}) is None


def test_native_files_do_not_link_another_users_artifact(
    native_service: WorkspaceFileService,
) -> None:
    with native_service.context.db.session() as session:
        artifact = Artifact(
            user_id="other",
            title="Other",
            format="pdf",
            mime_type="application/pdf",
            size=1,
            sha256="x",
            storage_key="other/file.pdf",
            sources=[],
        )
        session.add(artifact)
        session.flush()
        artifact_id = artifact.id
    row = native_service.record(
        "owner", "", "sheets", {"id": "sheet-123", "verified": True}, {"artifact_id": artifact_id}
    )
    assert row and row.artifact_id is None


def test_google_export_is_validated_owned_and_removes_binary_context(
    native_service: WorkspaceFileService, tmp_path: Path
) -> None:
    rendered = ArtifactEngine().create(
        ArtifactSpec(
            format="pdf",
            title="Export",
            blocks=[{"type": "paragraph", "text": "Real export content"}],
        ),
        tmp_path / "fixture",
    )
    result = {
        "id": "google-doc-123",
        "name": "Export.pdf",
        "mime_type": "application/pdf",
        "content_base64": base64.b64encode(rendered.path.read_bytes()).decode(),
        "sources": [
            {
                "provider": "drive",
                "resource_id": "google-doc-123",
                "title": "Source",
                "url": "https://docs.google.com/document/d/google-doc-123/edit",
                "snippet": "",
                "untrusted": True,
            }
        ],
    }
    exported = native_service.import_export("owner", "", result)
    assert "content_base64" not in result
    assert exported["validated"] and exported["format"] == "pdf"
    assert exported["sources"][0]["resource_id"] == "google-doc-123"
    with native_service.context.db.session() as session:
        row = session.get(Artifact, exported["id"])
        assert row and row.user_id == "owner"
        path = native_service.context.settings.storage / row.storage_key
        assert path.read_bytes() == rendered.path.read_bytes()
        assert path.stat().st_mode & 0o777 == 0o600


def test_invalid_export_does_not_persist_or_leak_bytes(
    native_service: WorkspaceFileService,
) -> None:
    result = {"mime_type": "application/pdf", "content_base64": "not-valid-base64"}
    with pytest.raises(Denied, match="content is invalid"):
        native_service.import_export("owner", "", result)
    assert "content_base64" not in result
    with native_service.context.db.session() as session:
        assert not list(session.scalars(select(Artifact)))
