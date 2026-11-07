from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
from mcp_workspace_api.connectors import (
    ConnectorError,
    GoogleWorkspace,
    MockWorkspace,
)

from tests.support.connector_fixtures import token


async def test_gmail_queries_pagination_and_thread(workspace: MockWorkspace) -> None:
    first = await workspace.call(
        "gmail", "search_messages", {"query": "is:unread newer_than:7d launch", "max_results": 2}
    )
    second = await workspace.call(
        "gmail",
        "search_messages",
        {
            "query": "is:unread newer_than:7d launch",
            "max_results": 2,
            "page_token": first["next_page_token"],
        },
    )
    assert len(first["messages"]) == 2
    assert first["messages"][0]["id"] != second["messages"][0]["id"]
    assert first["sources"][0]["synthetic"]
    thread = await workspace.call("gmail", "get_thread", {"thread_id": "thread-01"})
    assert len(thread["messages"]) == 4
    assert "INJECTION" in thread["messages"][-1]["text"] or any(
        "INJECTION" in m["text"] for m in thread["messages"]
    )
    assert not (
        await workspace.call("gmail", "search_messages", {"query": "from:nobody@example.invalid"})
    )["messages"]


async def test_gmail_draft_snapshot_persistence_and_isolation(tmp_path: Path) -> None:
    workspace = MockWorkspace(tmp_path, "user-a")
    draft = await workspace.call(
        "gmail",
        "create_draft",
        {
            "to": ["test-recipient@example.invalid"],
            "subject": "Decisions",
            "body_text": "Budget $24000",
            "reply_to_message_id": "msg-001",
        },
    )
    args = {"draft_id": draft["id"]}
    snapshot = await workspace.snapshot("gmail", "send_draft", args)
    assert snapshot["thread_id"] == "thread-01"
    assert snapshot["message"]["to"] == "test-recipient@example.invalid"
    assert MockWorkspace(tmp_path, "user-a")._load()["drafts"]
    with pytest.raises(ConnectorError, match="not found"):
        await MockWorkspace(tmp_path, "user-b").snapshot("gmail", "send_draft", args)
    with pytest.raises(ConnectorError, match="snapshot"):
        await workspace.call("gmail", "send_draft", args)
    sent = await workspace.call("gmail", "send_draft", args | {"_snapshot": snapshot})
    assert sent["status"] == "sent"
    assert len(workspace._load()["sent"]) == 1
    with pytest.raises(ConnectorError):
        await workspace.call("gmail", "send_draft", args | {"_snapshot": snapshot})
    assert len(workspace._load()["sent"]) == 1


async def test_live_send_atomic_full_approved_mime_and_stale_block() -> None:
    raw = "VG86IHRlc3RAZXhhbXBsZS5pbnZhbGlkDQoNCkFwcHJvdmVk"
    requests: list[httpx.Request] = []
    changed = False

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.method == "GET":
            return httpx.Response(
                200,
                json={
                    "id": "draft-1",
                    "message": {"raw": raw + ("Cg==" if changed else ""), "threadId": "thread-1"},
                },
            )
        body = json.loads(request.content)
        assert body == {"id": "draft-1", "message": {"raw": raw, "threadId": "thread-1"}}
        return httpx.Response(200, json={"id": "sent-1"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        workspace = GoogleWorkspace(token, client)
        args = {"draft_id": "draft-1"}
        snapshot = await workspace.snapshot("gmail", "send_draft", args)
        assert (await workspace.call("gmail", "send_draft", args | {"_snapshot": snapshot}))[
            "status"
        ] == "sent"
        assert sum(r.method == "POST" for r in requests) == 1
        changed = True
        with pytest.raises(ConnectorError):
            await workspace.call("gmail", "send_draft", args | {"_snapshot": snapshot})
        assert sum(r.method == "POST" for r in requests) == 1
