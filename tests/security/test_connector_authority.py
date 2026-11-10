from __future__ import annotations

import json
from typing import Any

import pytest
from mcp_workspace_api.core.security import Denied
from mcp_workspace_api.db import (
    Approval,
)

from tests.support import Browser, LiveServer
from tests.support.security_actions import DRAFT, authorized_action, mcp_call


async def test_disconnect_revokes_combined_grant_pending_authority(
    live_server: LiveServer, browser: Browser
) -> None:
    run_id, approval = await authorized_action(
        live_server, browser.user_id, "gmail.create_draft", DRAFT
    )
    response = await browser.http.post("/api/auth/google/disconnect")
    assert response.status_code == 200
    assert response.json()["affected_connectors"] == ["gmail", "calendar", "drive"]
    assert all(not x["enabled"] for x in (await browser.http.get("/api/connectors")).json())
    with live_server.runtime.db.session() as session:
        row = session.get(Approval, approval["id"])
        assert row is not None and row.status == "revoked"
    with pytest.raises(Denied):
        live_server.runtime.policy.authorize(
            browser.user_id, live_server.runtime.tools["gmail.create_draft"]
        )


async def test_drive_open_respects_disabled_connector(
    live_server: LiveServer, browser: Browser, monkeypatch: pytest.MonkeyPatch
) -> None:
    adapter = live_server.runtime.adapter(browser.user_id)
    calls = 0
    original = adapter.call

    async def counted(*args: Any) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        return dict(await original(*args))

    monkeypatch.setattr(adapter, "call", counted)
    assert (
        await browser.http.patch("/api/connectors/drive", json={"enabled": False})
    ).status_code == 200
    response = await browser.http.get(
        "/api/auth/google/drive-open",
        params={"state": json.dumps({"action": "open", "ids": ["proposal"]})},
    )
    assert response.status_code == 403
    assert calls == 0


async def test_upload_owned_artifact_to_approved_folder_snapshot(
    live_server: LiveServer, browser: Browser
) -> None:
    artifact = await mcp_call(
        live_server,
        browser.user_id,
        "artifact.create_markdown",
        {
            "format": "markdown",
            "title": "Owned upload",
            "blocks": [{"type": "paragraph", "text": "Synthetic upload content"}],
        },
    )
    args = {"artifact_id": artifact["data"]["id"], "folder_id": "folder-projects"}
    run_id, approval = await authorized_action(
        live_server, browser.user_id, "drive.upload_artifact", args
    )
    result = await mcp_call(
        live_server, browser.user_id, "drive.upload_artifact", args, run_id, approval
    )
    assert result["status"] == "success", result
    assert result["data"]["parents"] == ["folder-projects"]
