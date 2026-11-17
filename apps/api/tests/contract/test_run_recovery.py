from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock

import httpx
import pytest
import respx
from mcp_workspace_api.contracts import ToolResult
from mcp_workspace_api.db import GoogleAccount, Message, Run, User
from sqlalchemy import select

from tests.support import Browser, LiveServer

ENDPOINT = "https://model.example.invalid/v1/chat/completions"


def configure(server: LiveServer, browser: Browser, monkeypatch: pytest.MonkeyPatch) -> Any:
    runtime = server.runtime
    runtime.settings.mode = "live"
    runtime.settings.llm_provider = "openai_compatible"
    runtime.settings.llm_base_url = ENDPOINT.removesuffix("/chat/completions")
    runtime.settings.llm_model = "test-model"
    runtime.settings.llm_api_key = "SYNTHETIC_KEY"
    with runtime.db.session() as session:
        user = session.get(User, browser.user_id)
        assert user
        user.llm_consent = True
        user.consent_provider = runtime.settings.llm_base_url + ":test-model"
        account = session.scalar(select(GoogleAccount).where(GoogleAccount.user_id == user.id))
        assert account
        account.scopes = ["https://www.googleapis.com/auth/gmail.readonly"]
    monkeypatch.setattr(runtime, "catalog", AsyncMock(return_value=[]))
    return runtime


def call(name: str, arguments: dict[str, Any], index: int) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "choices": [
                {
                    "message": {
                        "content": None,
                        "tool_calls": [
                            {
                                "id": f"call-{index}",
                                "type": "function",
                                "function": {
                                    "name": name.replace(".", "__"),
                                    "arguments": json.dumps(arguments),
                                },
                            }
                        ],
                    }
                }
            ]
        },
    )


async def test_five_full_emails_continue_after_timeout_without_repeating_reads(
    live_server: LiveServer, browser: Browser, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime = configure(live_server, browser, monkeypatch)
    reads: list[str] = []
    requests: list[dict[str, Any]] = []

    async def invoke(user_id: str, name: str, args: dict[str, Any], *rest: Any) -> ToolResult:
        if name == "gmail.search_messages":
            return ToolResult(data={"messages": [{"id": str(i)} for i in range(5)]})
        reads.append(args["message_id"])
        return ToolResult(
            data={"id": args["message_id"], "body_text": "Complete body " + args["message_id"]}
        )

    monkeypatch.setattr(runtime, "invoke", invoke)

    def provider(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        requests.append(body)
        index = len(requests)
        if index == 1:
            return call("gmail.search_messages", {"query": "in:inbox", "max_results": 5}, index)
        if index == 3:
            raise httpx.ReadTimeout("PRIVATE_UPSTREAM_DETAILS")
        if len(reads) < 5:
            return call("gmail.get_message", {"message_id": str(len(reads))}, index)
        return httpx.Response(
            200, json={"choices": [{"message": {"content": "Read all five complete messages."}}]}
        )

    with respx.mock() as router:
        router.route(host="127.0.0.1").pass_through()
        router.post(ENDPOINT).mock(side_effect=provider)
        conversation, failed = await browser.start("Summarize my latest five emails")
        result = await browser.wait(conversation, failed)
        assert result["status"] == "failed" and result["retryable"]
        assert result["error_code"] == "MODEL_TIMED_OUT"
        assert result["read_count"] == 1 and result["selected_count"] == 5
        assert "PRIVATE" not in result["error"]
        response = await browser.http.post(
            f"/api/runs/{failed}/retry", json={"request_id": "continue-once"}
        )
        assert response.status_code == 200, response.text
        child = response.json()["id"]
        duplicate = await browser.http.post(
            f"/api/runs/{failed}/retry", json={"request_id": "continue-once"}
        )
        assert duplicate.json()["id"] == child
        assert (await browser.wait(conversation, child))["status"] == "completed"
    assert reads == [str(i) for i in range(5)]
    final_context = json.dumps(requests[-1]["messages"])
    assert all("Complete body " + str(i) in final_context for i in range(5))
    with runtime.db.session() as session:
        messages = list(
            session.scalars(select(Message).where(Message.conversation_id == conversation))
        )
        assert [row.role for row in messages].count("user") == 1
        assert [row.role for row in messages].count("assistant") == 1
        assert session.get(Run, failed).status == "failed"


@pytest.mark.parametrize("blocked", ["write", "tool", "permission", "consent", "newer"])
async def test_continuation_refuses_unsafe_or_stale_checkpoints(
    live_server: LiveServer, browser: Browser, monkeypatch: pytest.MonkeyPatch, blocked: str
) -> None:
    async with live_server.browser() as other:
        other_cookies = other.http.cookies
        other_headers = dict(other.http.headers)
    runtime = configure(live_server, browser, monkeypatch)
    conversation = await browser.conversation()
    with runtime.db.session() as session:
        run = Run(
            user_id=browser.user_id,
            conversation_id=conversation,
            request_id="failed-" + blocked,
            prompt="Read email",
            status="failed",
            state={
                "phase": "model",
                "error_code": "MODEL_TIMED_OUT",
                "results": [{"tool": "gmail.get_message", "data": {"id": "one"}}],
            },
        )
        session.add(run)
        session.flush()
        run_id = run.id
        if blocked == "write":
            run.state = {**run.state, "results": [{"tool": "gmail.create_draft", "data": {}}]}
        if blocked == "tool":
            run.state = {**run.state, "phase": "tool"}
        if blocked == "permission":
            account = session.scalar(
                select(GoogleAccount).where(GoogleAccount.user_id == browser.user_id)
            )
            account.enabled = []
        if blocked == "consent":
            session.get(User, browser.user_id).llm_consent = False
        if blocked == "newer":
            session.add(
                Run(
                    user_id=browser.user_id,
                    conversation_id=conversation,
                    prompt="Later request",
                    request_id="later",
                    status="completed",
                )
            )
    response = await browser.http.post(f"/api/runs/{run_id}/retry", json={"request_id": "attempt"})
    assert response.status_code in {403, 409}, response.text
    async with httpx.AsyncClient(
        base_url=live_server.url, cookies=other_cookies, headers=other_headers
    ) as other_http:
        response = await other_http.post(
            f"/api/runs/{run_id}/retry", json={"request_id": "foreign"}
        )
        assert response.status_code in {401, 403, 404}
