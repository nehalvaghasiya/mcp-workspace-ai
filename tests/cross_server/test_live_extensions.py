from __future__ import annotations

import base64
import json
from email import message_from_bytes

import httpx
import pytest
from mcp_workspace_api.connectors import ConnectorError, GoogleWorkspace

from tests.support.connector_fixtures import token


async def test_gmail_update_draft_checks_snapshot_and_preserves_thread() -> None:
    calls: list[httpx.Request] = []
    raw = base64.urlsafe_b64encode(b"To: a@example.invalid\r\nSubject: old\r\n\r\nold").decode()

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal raw
        calls.append(request)
        if request.method == "PUT":
            data = json.loads(request.content)
            assert data["id"] == "draft-1"
            assert data["message"]["threadId"] == "thread-1"
            message = message_from_bytes(base64.urlsafe_b64decode(data["message"]["raw"]))
            assert message["Subject"] == "Revised"
            raw = data["message"]["raw"]
            return httpx.Response(200, json={"id": "draft-1", "message": {"id": "msg-1"}})
        return httpx.Response(
            200, json={"id": "draft-1", "message": {"raw": raw, "threadId": "thread-1"}}
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        workspace = GoogleWorkspace(token, client)
        args = {
            "draft_id": "draft-1",
            "to": ["a@example.invalid"],
            "subject": "Revised",
            "body_text": "Updated\nMultiple lines are preserved.",
        }
        snapshot = await workspace.snapshot("gmail", "update_draft", args)
        result = await workspace.call("gmail", "update_draft", args | {"_snapshot": snapshot})
        assert result["draft_id"] == "draft-1"
        assert len([r for r in calls if r.method == "PUT"]) == 1
        with pytest.raises(ConnectorError, match="snapshot"):
            await workspace.call("gmail", "update_draft", args)


async def test_gmail_attachment_validates_owned_message_and_extracts_bounded_text() -> None:
    content = b"Real attachment content"

    def handle(request: httpx.Request) -> httpx.Response:
        if "/attachments/" in request.url.path:
            return httpx.Response(
                200, json={"size": len(content), "data": base64.urlsafe_b64encode(content).decode()}
            )
        return httpx.Response(
            200,
            json={
                "id": "msg-1",
                "payload": {
                    "parts": [
                        {
                            "filename": "notes.txt",
                            "mimeType": "text/plain",
                            "body": {"attachmentId": "attachment-1", "size": len(content)},
                        }
                    ]
                },
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        workspace = GoogleWorkspace(token, client)
        result = await workspace.call(
            "gmail",
            "get_attachment",
            {"message_id": "msg-1", "attachment_id": "attachment-1", "max_chars": 8},
        )
        assert result["filename"] == "notes.txt"
        assert result["text"] == "Real att" and result["truncated"]
        with pytest.raises(ConnectorError, match="not found"):
            await workspace.call(
                "gmail", "get_attachment", {"message_id": "msg-1", "attachment_id": "other"}
            )


async def test_drive_search_covers_shared_drive_and_pagination() -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        assert request.url.params["supportsAllDrives"] == "true"
        assert request.url.params["includeItemsFromAllDrives"] == "true"
        assert request.url.params["corpora"] == "drive"
        assert request.url.params["driveId"] == "team-drive"
        assert request.url.params["pageToken"] == "next"
        return httpx.Response(
            200,
            json={"files": [{"id": "existing-file", "name": "Existing"}], "nextPageToken": "after"},
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        result = await GoogleWorkspace(token, client).call(
            "drive", "search_files", {"drive_id": "team-drive", "page_token": "next"}
        )
        assert result["next_page_token"] == "after"
        assert "existing-file" == result["files"][0]["id"]
        assert "app-created" not in result.get("scope_note", "")


async def test_drive_move_binds_source_and_destination_then_reads_back() -> None:
    source = {
        "id": "file-1",
        "name": "Report",
        "version": "7",
        "parents": ["old"],
        "capabilities": {"canEdit": True},
    }
    destination = {
        "id": "new",
        "mimeType": "application/vnd.google-apps.folder",
        "version": "3",
        "capabilities": {"canAddChildren": True},
    }
    calls: list[httpx.Request] = []
    moved = False

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal moved
        calls.append(request)
        if request.method == "PATCH":
            assert request.url.params["addParents"] == "new"
            assert request.url.params["removeParents"] == "old"
            moved = True
            return httpx.Response(200, json=source | {"parents": ["new"], "version": "8"})
        return httpx.Response(
            200,
            json=destination
            if request.url.path.endswith("/new")
            else source | ({"parents": ["new"], "version": "8"} if moved else {}),
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        workspace = GoogleWorkspace(token, client)
        args = {"file_id": "file-1", "folder_id": "new"}
        snapshot = await workspace.snapshot("drive", "move_file", args)
        result = await workspace.call("drive", "move_file", args | {"_snapshot": snapshot})
        assert result["parents"] == ["new"]
        assert len([r for r in calls if r.method == "PATCH"]) == 1
        with pytest.raises(ConnectorError, match="changed"):
            await workspace.call("drive", "move_file", args | {"_snapshot": snapshot})
        assert len([r for r in calls if r.method == "PATCH"]) == 1


async def test_drive_sharing_is_explicit_and_does_not_transfer_ownership() -> None:
    from mcp_drive.schemas.share_file import ShareFile
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ShareFile(file_id="file", email="a@example.invalid", role="owner")
    with pytest.raises(ValidationError):
        ShareFile(file_id="file", email="bad\r\nheader", role="reader")


async def test_new_write_timeout_is_not_retried() -> None:
    writes = 0

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal writes
        if request.method == "POST":
            writes += 1
            raise httpx.ReadTimeout("provider-private", request=request)
        return httpx.Response(200, json={"id": "file", "version": "1"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        workspace = GoogleWorkspace(token, client)
        args = {"file_id": "file", "name": "Copy"}
        snapshot = await workspace.snapshot("drive", "copy_file", args)
        with pytest.raises(ConnectorError) as error:
            await workspace.call("drive", "copy_file", args | {"_snapshot": snapshot})
        assert error.value.code == "outcome_unknown" and writes == 1


def test_calendar_all_day_and_recurrence_validate_before_a_google_write() -> None:
    from mcp_calendar.schemas.create_event import CreateEvent
    from pydantic import ValidationError

    event = CreateEvent(
        title="Planning day",
        start="2026-11-14",
        end="2026-11-15",
        recurrence=["RRULE:FREQ=WEEKLY;COUNT=2"],
    )
    assert event.start == "2026-11-14"
    for changes in [
        {"end": "2026-11-14"},
        {"timezone": "Unknown/Zone"},
        {"attendees": ["bad\r\nrecipient"]},
        {"recurrence": ["RRULE:FREQ=DAILY\r\nInjected"]},
    ]:
        with pytest.raises(ValidationError):
            CreateEvent.model_validate(event.model_dump() | changes)


async def test_drive_export_returns_real_provider_bytes_and_checks_download_capability() -> None:
    export = b"%PDF-1.7\nverified provider bytes"

    def handle(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/export"):
            assert request.url.params["mimeType"] == "application/pdf"
            return httpx.Response(200, content=export)
        return httpx.Response(
            200,
            json={
                "id": "native-doc",
                "name": "Report",
                "mimeType": "application/vnd.google-apps.document",
                "capabilities": {"canDownload": True},
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        result = await GoogleWorkspace(token, client).call(
            "drive", "export_file", {"file_id": "native-doc", "mime_type": "application/pdf"}
        )
        assert base64.b64decode(result["content_base64"]) == export
        assert result["size"] == len(export)


async def test_drive_permission_write_readback_and_notification_choice() -> None:
    calls: list[httpx.Request] = []
    permission = {
        "id": "permission-1",
        "type": "user",
        "emailAddress": "reader@example.invalid",
        "role": "reader",
    }

    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if request.method == "POST":
            assert request.url.params["sendNotificationEmail"] == "false"
            assert json.loads(request.content) == {
                "type": "user",
                "emailAddress": permission["emailAddress"],
                "role": "reader",
            }
            return httpx.Response(200, json=permission)
        if request.url.path.endswith("/permissions"):
            return httpx.Response(200, json={"permissions": []})
        if request.url.path.endswith("/permission-1"):
            return httpx.Response(200, json=permission)
        return httpx.Response(
            200, json={"id": "file-1", "version": "3", "name": "Approved document"}
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        workspace = GoogleWorkspace(token, client)
        args = {
            "file_id": "file-1",
            "email": permission["emailAddress"],
            "role": "reader",
            "send_notification": False,
        }
        snapshot = await workspace.snapshot("drive", "share_file", args)
        result = await workspace.call("drive", "share_file", args | {"_snapshot": snapshot})
        assert result["permission"] == permission and result["readback_verified"]
        assert sum(call.method == "POST" for call in calls) == 1


async def test_gmail_archive_requires_snapshot_and_verifies_inbox_label_removal() -> None:
    archived = False
    writes = 0

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal archived, writes
        if request.method == "POST":
            writes += 1
            archived = True
            assert json.loads(request.content) == {"removeLabelIds": ["INBOX"]}
            return httpx.Response(200, json={"id": "message-1"})
        return httpx.Response(
            200,
            json={
                "id": "message-1",
                "labelIds": ["STARRED"] if archived else ["STARRED", "INBOX"],
                "historyId": "2" if archived else "1",
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        workspace = GoogleWorkspace(token, client)
        args = {"message_id": "message-1"}
        with pytest.raises(ConnectorError, match="snapshot"):
            await workspace.call("gmail", "archive_message", args)
        assert writes == 0
        snapshot = await workspace.snapshot("gmail", "archive_message", args)
        result = await workspace.call("gmail", "archive_message", args | {"_snapshot": snapshot})
        assert result["label_ids"] == ["STARRED"] and result["readback_verified"]
        with pytest.raises(ConnectorError, match="changed"):
            await workspace.call("gmail", "archive_message", args | {"_snapshot": snapshot})
        assert writes == 1


async def test_drive_find_operation_inspects_prior_effect_without_writing() -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert "workspace_operation" in request.url.params["q"]
        assert "approved-operation-123" in request.url.params["q"]
        return httpx.Response(200, json={"files": [{"id": "already-created", "name": "Report"}]})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        result = await GoogleWorkspace(token, client).call(
            "drive", "find_operation", {"operation_id": "approved-operation-123"}
        )
        assert result["files"][0]["id"] == "already-created"


def test_extra_live_tools_are_absent_from_mock_catalogs() -> None:
    from mcp_drive.server import LIVE_ONLY_TOOLS as drive_live
    from mcp_drive.server import tool_definitions as drive_tools
    from mcp_gmail.server import LIVE_ONLY_TOOLS as gmail_live
    from mcp_gmail.server import tool_definitions as gmail_tools

    assert not drive_live.intersection(drive_tools())
    assert not gmail_live.intersection(gmail_tools())
    assert drive_live <= drive_tools(include_live=True).keys()
    assert gmail_live <= gmail_tools(include_live=True).keys()
