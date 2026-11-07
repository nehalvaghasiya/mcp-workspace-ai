from __future__ import annotations

from typing import Any

import httpx
import pytest
from mcp_workspace_api.connectors import (
    ConnectorError,
    GoogleWorkspace,
    MockWorkspace,
)

from tests.support.connector_fixtures import token


async def test_calendar_all_day_recurrence_freebusy(workspace: MockWorkspace) -> None:
    args = {
        "calendar_id": "primary",
        "time_min": "2026-11-01T00:00:00-05:00",
        "time_max": "2026-12-05T00:00:00-06:00",
        "max_results": 100,
    }
    result = await workspace.call("calendar", "list_events", args)
    assert any("date" in x["start"] for x in result["events"])
    instances = [x for x in result["events"] if x.get("recurringEventId")]
    assert len(instances) == 4
    fetched = await workspace.call(
        "calendar", "get_event", {"calendar_id": "primary", "event_id": instances[0]["id"]}
    )
    assert fetched["recurringEventId"] == "event-004"
    assert all(x["status"] != "cancelled" for x in result["events"])
    busy = await workspace.call(
        "calendar", "query_freebusy", args | {"calendar_ids": ["primary", "restricted"]}
    )
    assert busy["calendars"]["primary"]["busy"]
    assert busy["calendars"]["restricted"]["errors"]


@pytest.mark.parametrize(
    "start,timezone",
    [
        ("2026-11-05T15:00:00", "America/Chicago"),
        ("2026-03-08T02:30:00-06:00", "America/Chicago"),
        ("2026-11-05T15:00:00-06:00", "Missing/Zone"),
    ],
)
async def test_calendar_rejects_ambiguous_or_nonexistent_time(
    workspace: MockWorkspace, start: str, timezone: str
) -> None:
    with pytest.raises(ConnectorError):
        await workspace.call(
            "calendar",
            "create_event",
            {
                "title": "Meeting",
                "start": start,
                "end": "2026-11-05T16:00:00-06:00",
                "timezone": timezone,
            },
        )


async def test_calendar_write_snapshot_and_permission(workspace: MockWorkspace) -> None:
    args = {
        "calendar_id": "primary",
        "event_id": "event-001",
        "changes": {"title": "Changed title"},
    }
    snapshot = await workspace.snapshot("calendar", "update_event", args)
    changed = await workspace.call("calendar", "update_event", args | {"_snapshot": snapshot})
    assert changed["summary"] == "Changed title"
    with pytest.raises(ConnectorError, match="changed"):
        await workspace.call("calendar", "cancel_event", args | {"_snapshot": snapshot})
    with pytest.raises(ConnectorError, match="read only"):
        await workspace.call(
            "calendar",
            "create_event",
            {"calendar_id": "team", "title": "No", "start": "2026-11-05", "end": "2026-11-06"},
        )


async def test_calendar_utc_input_converted_to_explicit_zone(workspace: MockWorkspace) -> None:
    event = await workspace.call(
        "calendar",
        "create_event",
        {
            "title": "UTC event",
            "start": "2026-11-05T20:00:00Z",
            "end": "2026-11-05T21:00:00Z",
            "timezone": "America/Chicago",
            "idempotency_key": "stable-event-1",
        },
    )
    assert event["start"]["dateTime"] == "2026-11-05T14:00:00-06:00"
    repeated = await workspace.call(
        "calendar",
        "create_event",
        {
            "title": "UTC event",
            "start": "2026-11-05T20:00:00Z",
            "end": "2026-11-05T21:00:00Z",
            "timezone": "America/Chicago",
            "idempotency_key": "stable-event-1",
        },
    )
    assert repeated["id"] == event["id"]


async def test_live_calendar_etag_and_drive_stream_limits() -> None:
    event = {
        "id": "event-1",
        "summary": "Planning",
        "etag": '"v1"',
        "start": {"dateTime": "2026-11-05T14:00:00-06:00", "timeZone": "America/Chicago"},
        "end": {"dateTime": "2026-11-05T15:00:00-06:00", "timeZone": "America/Chicago"},
        "attendees": [{"email": "test-recipient@example.invalid"}],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        if "calendar" in request.url.path:
            if request.method == "PATCH":
                assert request.headers["if-match"] == '"v1"'
                assert request.url.params["sendUpdates"] == "all"
                return httpx.Response(200, json=event | {"summary": "Approved title"})
            return httpx.Response(200, json=event)
        return httpx.Response(
            200,
            json={
                "id": "large",
                "mimeType": "text/plain",
                "size": "20000000",
                "capabilities": {"canDownload": True},
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        workspace = GoogleWorkspace(token, client)
        args: dict[str, Any] = {
            "calendar_id": "primary",
            "event_id": "event-1",
            "changes": {"title": "Approved title"},
        }
        args["_snapshot"] = await workspace.snapshot("calendar", "update_event", args)
        assert (await workspace.call("calendar", "update_event", args))[
            "summary"
        ] == "Approved title"
        with pytest.raises(ConnectorError, match="10 MiB"):
            await workspace.call("drive", "read_file", {"file_id": "large"})
