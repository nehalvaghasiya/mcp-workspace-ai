from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock

import httpx
import pytest
import respx
from mcp_workspace_api.agents.model_history import conversation_history
from mcp_workspace_api.contracts import SourceRef, ToolResult
from mcp_workspace_api.db import GoogleAccount, Message, User
from sqlalchemy import select

from tests.support import Browser, LiveServer

ENDPOINT = "https://model.example.invalid/v1/chat/completions"


def configure(live_server: LiveServer, browser: Browser, monkeypatch: pytest.MonkeyPatch) -> Any:
    runtime = live_server.runtime
    runtime.settings.mode = "live"
    runtime.settings.llm_provider = "openai_compatible"
    runtime.settings.llm_base_url = "https://model.example.invalid/v1"
    runtime.settings.llm_model = "configured-live-model"
    runtime.settings.llm_api_key = "SYNTHETIC_MODEL_KEY"
    with runtime.db.session() as session:
        user = session.get(User, browser.user_id)
        assert user is not None
        user.llm_consent = True
        user.consent_provider = runtime.settings.llm_base_url + ":" + runtime.settings.llm_model
        account = session.scalar(select(GoogleAccount).where(GoogleAccount.user_id == user.id))
        assert account is not None
        account.scopes = ["https://www.googleapis.com/auth/gmail.readonly"]
        account.credentials = "PRIVATE_VAULT_CREDENTIAL_CANARY"
    monkeypatch.setattr(runtime, "catalog", AsyncMock(return_value=[]))
    return runtime


def streaming_answer(*pieces: str) -> httpx.Response:
    data = "".join(
        "data: " + json.dumps({"choices": [{"index": 0, "delta": {"content": piece}}]}) + "\n\n"
        for piece in pieces
    )
    data += (
        "data: "
        + json.dumps({"choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]})
        + "\n\ndata: [DONE]\n\n"
    )
    return httpx.Response(200, text=data, headers={"content-type": "text/event-stream"})


async def test_live_greeting_uses_configured_model_and_streams_without_duplicate_deltas(
    live_server: LiveServer, browser: Browser, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime = configure(live_server, browser, monkeypatch)
    invoked = AsyncMock(side_effect=AssertionError("A greeting must not invoke workspace tools"))
    monkeypatch.setattr(runtime, "invoke", invoked)
    with respx.mock() as router:
        router.route(host="127.0.0.1").pass_through()
        route = router.post(ENDPOINT).mock(
            return_value=streaming_answer("Hello", "! How can I help?")
        )
        conversation, run_id = await browser.start("Hi")
        run = await browser.wait(conversation, run_id)
        assert run["status"] == "completed", run
        detail = (await browser.http.get(f"/api/conversations/{conversation}")).json()
        assistant = [row for row in detail["messages"] if row["role"] == "assistant"][-1]
        assert assistant["content"] == "Hello! How can I help?"
        assert "Synthetic demo" not in assistant["content"]
        stream = await browser.http.get(f"/api/runs/{run_id}/events")
    body = json.loads(route.calls[0].request.content)
    assert body["model"] == "configured-live-model" and body["stream"] is True
    assert body["messages"][-1] == {"role": "user", "content": "Hi"}
    assert "PRIVATE_VAULT_CREDENTIAL_CANARY" not in json.dumps(body)
    assert "SYNTHETIC_MODEL_KEY" not in json.dumps(body)
    deltas = [
        json.loads(line[6:])["data"]["text"]
        for line in stream.text.splitlines()
        if line.startswith("data: ") and json.loads(line[6:])["type"] == "message.delta"
    ]
    assert deltas == ["Hello", "! How can I help?"]
    invoked.assert_not_called()


async def test_live_tool_result_is_paired_with_original_assistant_call(
    live_server: LiveServer, browser: Browser, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime = configure(live_server, browser, monkeypatch)
    definition = runtime.tools["gmail.get_message"]
    monkeypatch.setattr(
        runtime,
        "catalog",
        AsyncMock(
            return_value=[
                {
                    "name": definition.name,
                    "description": definition.description,
                    "input_schema": definition.input_model.model_json_schema(),
                    "enabled": True,
                }
            ]
        ),
    )
    invoked = AsyncMock(
        return_value=ToolResult(
            data={"id": "selected-message", "text": "Retrieved authorized email"}
        )
    )
    monkeypatch.setattr(runtime, "invoke", invoked)
    requests: list[dict[str, Any]] = []

    def provider(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        requests.append(body)
        if len(requests) == 1:
            return httpx.Response(
                200,
                json={
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": None,
                                "tool_calls": [
                                    {
                                        "id": "call-selected",
                                        "type": "function",
                                        "function": {
                                            "name": "gmail__get_message",
                                            "arguments": json.dumps(
                                                {"request": {"message_id": "selected-message"}}
                                            ),
                                        },
                                    }
                                ],
                            }
                        }
                    ]
                },
            )
        assert body["messages"][-2]["role"] == "assistant"
        assert body["messages"][-2]["tool_calls"][0]["id"] == "call-selected"
        assert body["messages"][-1]["role"] == "tool"
        assert body["messages"][-1]["tool_call_id"] == "call-selected"
        assert (
            json.loads(body["messages"][-1]["content"])["data"]["text"]
            == "Retrieved authorized email"
        )
        return streaming_answer("The selected email says: ", "Retrieved authorized email.")

    with respx.mock() as router:
        router.route(host="127.0.0.1").pass_through()
        router.post(ENDPOINT).mock(side_effect=provider)
        conversation, run_id = await browser.start("Read the selected message")
        run = await browser.wait(conversation, run_id)
    assert run["status"] == "completed", run
    assert len(requests) == 2
    invoked.assert_awaited_once_with(
        browser.user_id, "gmail.get_message", {"message_id": "selected-message"}, run_id, None
    )


async def test_prior_history_is_bounded_owned_and_does_not_duplicate_current_prompt(
    live_server: LiveServer, browser: Browser, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime = configure(live_server, browser, monkeypatch)
    conversation = await browser.conversation()
    with runtime.db.session() as session:
        for index in range(35):
            session.add(
                Message(
                    user_id=browser.user_id,
                    conversation_id=conversation,
                    role="assistant" if index % 2 else "user",
                    content=f"prior-turn-{index:02d}:" + "x" * 2000,
                    created_at=index + 1,
                )
            )
    with respx.mock() as router:
        router.route(host="127.0.0.1").pass_through()
        route = router.post(ENDPOINT).mock(
            return_value=streaming_answer("I remember the relevant context.")
        )
        _, run_id = await browser.start("Newest question", conversation)
        run = await browser.wait(conversation, run_id)
    assert run["status"] == "completed", run
    body = json.loads(route.calls[0].request.content)
    history = body["messages"][1:-1]
    assert len(history) <= 20 and sum(len(row["content"]) for row in history) <= 40000
    assert all(len(row["content"]) <= 12000 for row in history)
    assert "prior-turn-34" in json.dumps(history) and "prior-turn-00" not in json.dumps(history)
    assert sum(row.get("content") == "Newest question" for row in body["messages"]) == 1
    assert conversation_history(runtime, "another-owner", conversation, "Newest question") == []
    with runtime.db.session() as session:
        session.add(
            Message(
                user_id=browser.user_id,
                conversation_id=conversation,
                role="system",
                content="PRIVATE_SYSTEM_ROW_MUST_NOT_BE_FORWARDED",
            )
        )
    assert "PRIVATE_SYSTEM_ROW" not in json.dumps(
        conversation_history(runtime, browser.user_id, conversation, "Newest question")
    )


async def test_live_consent_denial_prevents_provider_requests(
    live_server: LiveServer, browser: Browser, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime = configure(live_server, browser, monkeypatch)
    with runtime.db.session() as session:
        user = session.get(User, browser.user_id)
        assert user is not None
        user.consent_provider = "https://other-provider.example.invalid/v1:different-model"
    with respx.mock(assert_all_called=False) as router:
        router.route(host="127.0.0.1").pass_through()
        route = router.post(ENDPOINT).mock(return_value=streaming_answer("Must never be used"))
        conversation, run_id = await browser.start("Private message stays here")
        run = await browser.wait(conversation, run_id)
        stream = await browser.http.get(f"/api/runs/{run_id}/events")
    assert run["status"] == "failed"
    assert "LLM_CONSENT_REQUIRED" in stream.text and route.call_count == 0


async def test_five_message_summary_batches_reads_then_synthesizes_without_tool_history(
    live_server: LiveServer, browser: Browser, monkeypatch: pytest.MonkeyPatch
) -> None:
    from mcp_gmail.tools.read_messages import definition

    runtime = configure(live_server, browser, monkeypatch)
    runtime.tools["gmail.get_messages"] = definition()
    names = ["gmail.search_messages", "gmail.get_messages", "artifact.create_pdf"]
    monkeypatch.setattr(
        runtime,
        "catalog",
        AsyncMock(
            return_value=[
                {
                    "name": name,
                    "description": runtime.tools[name].description,
                    "input_schema": runtime.tools[name].input_model.model_json_schema(),
                    "enabled": True,
                }
                for name in names
            ]
        ),
    )
    selected = [str(index) for index in range(5)]
    sources = [
        SourceRef(
            provider="gmail",
            resource_id=identifier,
            title="Selected email",
            url="https://mail.google.com/mail/u/0/#inbox/" + identifier,
            retrieved_at="2026-11-16T00:00:00Z",
        )
        for identifier in selected
    ]

    async def invoke(
        user_id: str, name: str, args: dict[str, Any], run_id: str, approval: Any
    ) -> ToolResult:
        if name == "gmail.search_messages":
            return ToolResult(
                data={"messages": [{"id": identifier} for identifier in selected]}, sources=sources
            )
        if name == "gmail.get_messages":
            return ToolResult(
                data={
                    "messages": [
                        {"id": identifier, "body_text": "Complete selected body " + identifier}
                        for identifier in selected
                    ]
                },
                sources=sources,
            )
        return ToolResult(data=await runtime._artifact(user_id, run_id, "create_pdf", args))

    invoked = AsyncMock(side_effect=invoke)
    monkeypatch.setattr(runtime, "invoke", invoked)
    requests = []

    def provider(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        requests.append(body)
        if len(requests) < 3 or len(requests) == 5:
            name = names[len(requests) - 1] if len(requests) < 3 else "artifact.create_pdf"
            arguments = (
                {"query": "in:inbox", "max_results": 5}
                if len(requests) == 1
                else {"message_ids": selected}
            )
            if len(requests) == 5:
                assert len(body["tools"]) == 1
                assert body["tool_choice"]["function"]["name"] == "artifact__create_pdf"
                assert "Complete selected body" not in json.dumps(body["messages"])
                arguments = {
                    "format": "pdf",
                    "title": "Decision brief",
                    "blocks": [{"type": "paragraph", "text": "Existing findings"}],
                }
            return httpx.Response(
                200,
                json={
                    "choices": [
                        {
                            "message": {
                                "content": None,
                                "tool_calls": [
                                    {
                                        "id": "call-" + str(len(requests)),
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
        assert "tools" not in body
        assert all(row["role"] in {"system", "user", "assistant"} for row in body["messages"])
        assert not any(row.get("tool_calls") for row in body["messages"])
        evidence = json.dumps(body["messages"])
        assert "UNTRUSTED RETRIEVED EVIDENCE" in evidence
        if len(requests) in {3, 4}:
            assert all(
                "Complete selected body " + identifier in evidence for identifier in selected
            )
        return streaming_answer("Summary of all five retrieved messages.")

    with respx.mock() as router:
        router.route(host="127.0.0.1").pass_through()
        router.post(ENDPOINT).mock(side_effect=provider)
        conversation, run_id = await browser.start("Summarize my five most recent inbox emails")
        result = await browser.wait(conversation, run_id)
        assert result["status"] == "completed" and result["read_count"] == 5
        _, followup = await browser.start("Prioritize these findings", conversation)
        followed = await browser.wait(conversation, followup)
        assert followed["status"] == "completed"
        detail = (await browser.http.get(f"/api/conversations/{conversation}")).json()
        assert len(detail["messages"][-1]["sources"]) == 5
        _, document = await browser.start(
            "Create a downloadable local PDF from this action list with sources", conversation
        )
        assert (await browser.wait(conversation, document))["status"] == "completed"
        detail = (await browser.http.get(f"/api/conversations/{conversation}")).json()
        artifact = detail["messages"][-1]["artifacts"][0]
        assert len(artifact["sources"]) == 5
        download = await browser.http.get(artifact["download_url"])
        assert download.status_code == 200 and download.content.startswith(b"%PDF-")
    assert result["status"] == "completed" and result["read_count"] == 5
    assert invoked.await_count == 3 and len(requests) == 6
