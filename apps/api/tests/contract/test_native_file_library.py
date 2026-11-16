from __future__ import annotations

import httpx
from mcp_workspace_api.db.models.workspace_file import WorkspaceFile
from mcp_workspace_api.services.workspace_file_service import WorkspaceFileService
from sqlalchemy import select

from tests.support import Browser, LiveServer


async def test_native_library_requires_session_and_enforces_owner_boundaries(
    live_server: LiveServer, browser: Browser
) -> None:
    service = WorkspaceFileService(live_server.runtime)
    row = service.record(
        browser.user_id, "", "docs", {"id": "owned-doc-123", "title": "Owned", "verified": True}, {}
    )
    assert row
    listing = await browser.http.get("/api/workspace-files")
    assert listing.status_code == 200
    assert listing.json()[0]["google_file_id"] == "owned-doc-123"
    assert (await browser.http.get(f"/api/workspace-files/{row.id}")).status_code == 200
    async with live_server.browser() as other:
        assert (await other.http.get("/api/workspace-files")).json() == []
        assert (await other.http.get(f"/api/workspace-files/{row.id}")).status_code == 404
    async with httpx.AsyncClient(base_url=live_server.url) as anonymous:
        assert (await anonymous.get("/api/workspace-files")).status_code == 401


async def test_native_library_filters_and_validates_pagination(
    live_server: LiveServer, browser: Browser
) -> None:
    service = WorkspaceFileService(live_server.runtime)
    for server in ("docs", "sheets", "slides"):
        service.record(browser.user_id, "", server, {"id": f"{server}-123", "verified": True}, {})
    filtered = await browser.http.get("/api/workspace-files", params={"kind": "sheets"})
    assert filtered.status_code == 200
    assert [row["kind"] for row in filtered.json()] == ["sheets"]
    assert len((await browser.http.get("/api/workspace-files?limit=1&offset=1")).json()) == 1
    assert (await browser.http.get("/api/workspace-files?limit=101")).status_code == 422
    assert (await browser.http.get("/api/workspace-files?kind=unknown")).status_code == 422


async def test_local_account_deletion_removes_native_file_tracking(
    live_server: LiveServer, browser: Browser
) -> None:
    service = WorkspaceFileService(live_server.runtime)
    service.record(browser.user_id, "", "docs", {"id": "owned-doc-123", "verified": True}, {})
    response = await browser.http.delete("/api/account")
    assert response.status_code == 200
    assert response.json()["remote_resources_deleted"] is False
    with live_server.runtime.db.session() as session:
        assert not list(
            session.scalars(select(WorkspaceFile).where(WorkspaceFile.user_id == browser.user_id))
        )
