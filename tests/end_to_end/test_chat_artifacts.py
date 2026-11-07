from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path
from uuid import uuid4

from mcp_documents.artifacts import ArtifactEngine
from mcp_workspace_api.db import Operation
from sqlalchemy import select

from tests.support import Browser, LiveServer
from tests.support.api_actions import approved_action


async def test_four_format_workflow_sources_trace_downloads_and_sse(
    live_server: LiveServer, browser: Browser, tmp_path: Path
) -> None:
    conversation, run_id = await browser.start(
        "Create all four versions of the same report from Northstar launch emails, meetings, and Drive proposal"
    )
    run = await browser.wait(conversation, run_id)
    assert run["status"] == "completed", run
    response = await browser.http.get(f"/api/conversations/{conversation}")
    assistant = [
        message for message in response.json()["messages"] if message["role"] == "assistant"
    ][-1]
    assert {source["provider"] for source in assistant["sources"]} == {"gmail", "calendar", "drive"}
    assert all(source["resource_id"] and source["title"] for source in assistant["sources"])
    assert {artifact["format"] for artifact in assistant["artifacts"]} == {
        "docx",
        "pdf",
        "xlsx",
        "pptx",
    }
    for artifact in assistant["artifacts"]:
        downloaded = await browser.http.get(artifact["download_url"])
        assert downloaded.status_code == 200
        assert "attachment" in downloaded.headers["content-disposition"]
        assert downloaded.headers["content-type"].startswith(artifact["mime_type"])
        assert len(downloaded.content) == artifact["size"]
        assert hashlib.sha256(downloaded.content).hexdigest() == artifact["sha256"]
        path = tmp_path / f"download.{artifact['format']}"
        path.write_bytes(downloaded.content)
        assert ArtifactEngine().validate(path, artifact["format"])["valid"]
        metadata = (await browser.http.get(f"/api/artifacts/{artifact['id']}")).json()
        assert metadata["sources"] and metadata["validated"]
    trace = (await browser.http.get(f"/api/runs/{run_id}/trace")).json()
    tools = {entry["tool"] for entry in trace}
    assert {
        "gmail.search_messages",
        "calendar.list_events",
        "drive.read_file",
        "artifact.create_pdf",
        "artifact.create_pptx",
    } <= tools
    completed = [entry for entry in trace if entry["type"] == "tool.completed"]
    assert completed and all(entry["elapsed_ms"] >= 0 for entry in completed)
    assert all(entry["status"] == "success" for entry in completed)
    stream = await browser.http.get(f"/api/runs/{run_id}/events")
    assert stream.status_code == 200
    events = [
        json.loads(line.removeprefix("data: "))
        for line in stream.text.splitlines()
        if line.startswith("data: ")
    ]
    assert events[-1]["type"] == "run.completed"
    ids = [event["id"] for event in events]
    assert ids == sorted(set(ids))
    cursor = ids[-2]
    resumed = await browser.http.get(
        f"/api/runs/{run_id}/events", headers={"Last-Event-ID": str(cursor)}
    )
    assert all(
        json.loads(line.removeprefix("data: "))["id"] > cursor
        for line in resumed.text.splitlines()
        if line.startswith("data: ")
    )


async def test_duplicate_request_id_is_idempotent_and_conflicting_reuse_rejected(
    browser: Browser,
) -> None:
    conversation = await browser.conversation()
    request_id = uuid4().hex
    payload = {"content": "Which tools are available?", "request_id": request_id}
    first, duplicate = await asyncio.gather(
        browser.http.post(f"/api/conversations/{conversation}/messages", json=payload),
        browser.http.post(f"/api/conversations/{conversation}/messages", json=payload),
    )
    assert first.status_code == duplicate.status_code == 200
    assert first.json()["id"] == duplicate.json()["id"]
    run = await browser.wait(conversation, first.json()["id"])
    assert run["status"] == "completed", run
    conflict = await browser.http.post(
        f"/api/conversations/{conversation}/messages",
        json={**payload, "content": "Different request"},
    )
    assert conflict.status_code == 409
    detail = (await browser.http.get(f"/api/conversations/{conversation}")).json()
    assert len(detail["runs"]) == 1
    assert len([message for message in detail["messages"] if message["role"] == "user"]) == 1


async def test_all_eight_google_writes_require_exact_approval_and_execute_once(
    live_server: LiveServer, browser: Browser
) -> None:
    draft = await approved_action(
        live_server,
        browser,
        "gmail.create_draft",
        {
            "to": ["test-recipient@example.invalid"],
            "subject": "Synthetic decisions",
            "body_text": "Review the Northstar launch decisions.",
        },
    )
    await approved_action(live_server, browser, "gmail.send_draft", {"draft_id": draft["draft_id"]})
    await approved_action(
        live_server,
        browser,
        "gmail.apply_labels",
        {"message_ids": ["msg-001"], "add": ["STARRED"], "remove": []},
    )
    event = await approved_action(
        live_server,
        browser,
        "calendar.create_event",
        {
            "calendar_id": "primary",
            "title": "Controlled synthetic event",
            "start": "2026-11-12T14:00:00-06:00",
            "end": "2026-11-12T14:30:00-06:00",
            "timezone": "America/Chicago",
            "attendees": ["test-recipient@example.invalid"],
        },
    )
    await approved_action(
        live_server,
        browser,
        "calendar.update_event",
        {
            "calendar_id": "primary",
            "event_id": event["id"],
            "changes": {"title": "Explicitly approved update"},
        },
    )
    await approved_action(
        live_server,
        browser,
        "calendar.cancel_event",
        {"calendar_id": "primary", "event_id": event["id"]},
    )
    folder = await approved_action(
        live_server,
        browser,
        "drive.create_folder",
        {"name": "Controlled test folder", "parent_id": "root"},
    )
    async with live_server.mcp(browser.user_id, "artifact") as client:
        rendered = await client.call_tool(
            "artifact.create_docx", {"request": {"format": "docx", "title": "Controlled upload"}}
        )
    await approved_action(
        live_server,
        browser,
        "drive.upload_artifact",
        {
            "artifact_id": rendered.structured_content["data"]["id"],
            "folder_id": folder["id"],
            "target_name": "Approved report.docx",
        },
    )
    state = live_server.runtime.adapter(browser.user_id)._load()
    assert len(state["sent"]) == 1
    with live_server.runtime.db.session() as session:
        operations = list(
            session.scalars(select(Operation).where(Operation.user_id == browser.user_id))
        )
        assert len(operations) == 8 and all(
            operation.status == "completed" for operation in operations
        )
