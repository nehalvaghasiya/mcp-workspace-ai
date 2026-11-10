from __future__ import annotations

import json
from typing import Any

import httpx
import pytest
from mcp_workspace_api.connectors import (
    ConnectorError,
    GoogleWorkspace,
)

from tests.support.connector_fixtures import token


async def test_live_read_retry_sanitization_and_allowlist() -> None:
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        assert request.headers["authorization"] == "Bearer CANARY_FAKE_ACCESS_TOKEN"
        return (
            httpx.Response(429, json={"token": "CANARY_PROVIDER_SECRET"})
            if len(calls) < 3
            else httpx.Response(200, json={"labels": []})
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        workspace = GoogleWorkspace(token, client)
        assert await workspace.call("gmail", "list_labels", {}) == {"labels": []}
        assert len(calls) == 3
        with pytest.raises(ConnectorError, match="not allowed"):
            await workspace._request("GET", "http://169.254.169.254/metadata", read=True)


@pytest.mark.parametrize(
    "status,code",
    [
        (401, "auth_required"),
        (403, "permission_denied"),
        (404, "not_found"),
        (429, "rate_limited"),
        (500, "provider_error"),
    ],
)
async def test_live_provider_errors_do_not_leak_tokens(status: int, code: str) -> None:
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(status, text="CANARY_PROVIDER_SECRET")
        )
    ) as client:
        with pytest.raises(ConnectorError) as caught:
            await GoogleWorkspace(token, client).call("gmail", "list_labels", {})
        assert "CANARY" not in str(caught.value)
        assert caught.value.code == code


async def test_live_write_timeout_not_retried() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.ReadTimeout("CANARY_FAKE_ACCESS_TOKEN", request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ConnectorError) as caught:
            await GoogleWorkspace(token, client).call(
                "drive", "create_folder", {"name": "Synthetic"}
            )
        assert caught.value.code == "outcome_unknown"
        assert "CANARY" not in str(caught.value)
        assert calls == 1


@pytest.mark.parametrize(
    "server,tool,args,expected_method,expected_suffix,response",
    [
        (
            "gmail",
            "create_draft",
            {
                "to": ["test-recipient@example.invalid"],
                "subject": "Synthetic",
                "body_text": "Approved draft",
            },
            "POST",
            "/drafts",
            {"id": "draft-1"},
        ),
        (
            "gmail",
            "apply_labels",
            {"message_ids": ["m1"], "add": ["STARRED"], "remove": ["UNREAD"]},
            "POST",
            "/messages/batchModify",
            {},
        ),
        ("calendar", "list_calendars", {}, "GET", "/calendarList", {"items": []}),
        (
            "calendar",
            "list_events",
            {
                "calendar_id": "primary",
                "time_min": "2026-11-05T00:00:00-06:00",
                "time_max": "2026-11-06T00:00:00-06:00",
            },
            "GET",
            "/events",
            {"items": []},
        ),
        (
            "calendar",
            "query_freebusy",
            {
                "calendar_ids": ["primary"],
                "time_min": "2026-11-05T00:00:00-06:00",
                "time_max": "2026-11-06T00:00:00-06:00",
            },
            "POST",
            "/freeBusy",
            {"calendars": {"primary": {"busy": []}}},
        ),
        (
            "calendar",
            "create_event",
            {
                "calendar_id": "primary",
                "title": "Approved invitation",
                "start": "2026-11-05T14:00:00-06:00",
                "end": "2026-11-05T15:00:00-06:00",
                "timezone": "America/Chicago",
                "attendees": ["test-recipient@example.invalid"],
            },
            "POST",
            "/events",
            {"id": "e1"},
        ),
        (
            "drive",
            "search_files",
            {"query": "launch", "mime_types": ["text/plain"], "parent_id": "folder-1"},
            "GET",
            "/files",
            {"files": []},
        ),
        (
            "drive",
            "create_folder",
            {"name": "Approved folder", "parent_id": "folder-1"},
            "POST",
            "/files",
            {"id": "folder-2"},
        ),
    ],
)
async def test_live_method_contracts(
    server: str,
    tool: str,
    args: dict[str, Any],
    expected_method: str,
    expected_suffix: str,
    response: dict[str, Any],
) -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        assert request.method == expected_method
        assert request.url.path.endswith(expected_suffix)
        if tool == "list_events":
            assert request.url.params["singleEvents"] == "true"
            assert request.url.params["orderBy"] == "startTime"
        if tool == "create_event":
            assert request.url.params["sendUpdates"] == "all"
            assert json.loads(request.content)["attendees"] == [
                {"email": "test-recipient@example.invalid"}
            ]
        if tool == "create_draft":
            assert json.loads(request.content)["message"]["raw"]
        if tool == "search_files":
            assert "trashed = false" in request.url.params["q"]
            assert "'folder-1' in parents" in request.url.params["q"]
        return httpx.Response(200, json=response)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await GoogleWorkspace(token, client).call(server, tool, args)
        assert isinstance(result, dict)
        assert len(calls) == 1
