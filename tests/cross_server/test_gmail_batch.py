import asyncio
import base64

import httpx
import pytest
from mcp_gmail.schemas.message_batch import MessageBatch
from mcp_workspace_api.connectors import GoogleWorkspace
from pydantic import ValidationError

from tests.support.connector_fixtures import token


async def test_batch_reads_are_bounded_ordered_deduplicated_and_sourced() -> None:
    active = peak = 0
    calls = []

    async def handle(request: httpx.Request) -> httpx.Response:
        nonlocal active, peak
        assert request.method == "GET" and request.url.params["format"] == "full"
        active += 1
        peak = max(active, peak)
        await asyncio.sleep(0.01)
        active -= 1
        identifier = request.url.path.rsplit("/", 1)[-1]
        calls.append(identifier)
        if identifier == "missing":
            return httpx.Response(404, json={"error": {"message": "private"}})
        return httpx.Response(
            200,
            json={
                "id": identifier,
                "threadId": "thread-" + identifier,
                "payload": {
                    "mimeType": "text/plain",
                    "headers": [{"name": "Subject", "value": "Selected"}],
                    "body": {
                        "data": base64.urlsafe_b64encode(
                            ("Full body " + identifier).encode()
                        ).decode()
                    },
                },
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        result = await GoogleWorkspace(token, client).call(
            "gmail",
            "get_messages",
            {
                "message_ids": ["one", "two", "three", "four", "five", "one", "missing"],
                "format": "full",
            },
        )
    assert peak <= 4 and peak > 1
    assert calls.count("one") == 1
    assert [row["id"] for row in result["messages"]] == ["one", "two", "three", "four", "five"]
    assert all(row["body_text"].startswith("Full body") for row in result["messages"])
    assert len(result["sources"]) == 5
    assert result["partial"] and len(result["unavailable"]) == 1
    assert "private" not in str(result["unavailable"])


@pytest.mark.parametrize("identifiers", [[], [str(i) for i in range(21)]])
def test_batch_selection_is_limited_before_any_google_request(identifiers: list[str]) -> None:
    with pytest.raises(ValidationError):
        MessageBatch(message_ids=identifiers)
