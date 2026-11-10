"""HTTP contract tests for the optional model adapter, without a real provider."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest
import respx
from mcp_workspace_api.agents import cloud_step
from mcp_workspace_api.core.security import Denied
from mcp_workspace_api.db import GoogleAccount, User
from sqlalchemy import select


def configured_runtime(server: Any, user_id: str) -> Any:
    runtime = server.runtime
    runtime.settings.mode = "live"
    runtime.settings.llm_provider = "openai_compatible"
    runtime.settings.llm_base_url = "https://model.example.invalid/v1"
    runtime.settings.llm_model = "contract-model"
    runtime.settings.llm_api_key = "synthetic-provider-key"
    with runtime.db.session() as session:
        user = session.get(User, user_id)
        user.llm_consent = True
        user.consent_provider = runtime.settings.llm_base_url + ":contract-model"
        user.timezone = "America/New_York"
        account = session.scalar(select(GoogleAccount).where(GoogleAccount.user_id == user_id))
        account.credentials = "vault-canary-not-for-model"
    return runtime


async def test_model_receives_authorized_context_and_usage_but_no_vault(
    live_server: Any, browser: Any
) -> None:
    runtime = configured_runtime(live_server, browser.user_id)
    with respx.mock() as router:
        call = router.post("https://model.example.invalid/v1/chat/completions").mock(
            return_value=httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": "A grounded answer"}}],
                    "usage": {"prompt_tokens": 11, "completion_tokens": 4},
                },
            )
        )
        result = await cloud_step(
            runtime,
            browser.user_id,
            "Summarize this record",
            [{"data": {"text": "Authorized evidence"}}],
            [],
            [{"data": {"text": "Prior-turn evidence"}}],
        )
        assert result["content"] == "A grounded answer" and result["usage"]["prompt_tokens"] == 11
        body = call.calls[0].request.content.decode()
        assert "Authorized evidence" in body and "Prior-turn evidence" in body
        assert "America/New_York" in body and "UNTRUSTED" in body
        assert "vault-canary" not in body and "synthetic-provider-key" not in body


async def test_model_tool_call_preserves_typed_request_and_namespace(
    live_server: Any, browser: Any
) -> None:
    runtime = configured_runtime(live_server, browser.user_id)
    with respx.mock() as router:
        router.post("https://model.example.invalid/v1/chat/completions").mock(
            return_value=httpx.Response(
                200,
                json={
                    "choices": [
                        {
                            "message": {
                                "tool_calls": [
                                    {
                                        "function": {
                                            "name": "gmail__get_message",
                                            "arguments": json.dumps(
                                                {"request": {"message_id": "msg-001"}}
                                            ),
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                },
            )
        )
        result = await cloud_step(
            runtime,
            browser.user_id,
            "Read the selected message",
            [],
            [
                {
                    "name": "gmail.get_message",
                    "description": "Read one owned message",
                    "input_schema": {"type": "object"},
                    "enabled": True,
                }
            ],
        )
        assert result["tool"] == "gmail.get_message" and result["arguments"] == {
            "message_id": "msg-001"
        }


@pytest.mark.parametrize("status,size", [(500, 100), (200, 2_000_001)])
async def test_model_error_bodies_are_bounded_and_not_reflected(
    live_server: Any, browser: Any, status: int, size: int
) -> None:
    runtime = configured_runtime(live_server, browser.user_id)
    with respx.mock() as router:
        router.post("https://model.example.invalid/v1/chat/completions").mock(
            return_value=httpx.Response(status, content=("canary" * (size // 6 + 1))[:size])
        )
        with pytest.raises(Denied) as error:
            await cloud_step(runtime, browser.user_id, "Read", [], [])
        assert "canary" not in str(error.value)


async def test_calendar_arguments_use_user_profile_timezone(live_server: Any, browser: Any) -> None:
    runtime = live_server.runtime
    with runtime.db.session() as session:
        user = session.get(User, browser.user_id)
        user.timezone = "America/New_York"
    parsed = runtime.validate_arguments(
        browser.user_id,
        runtime.tools["calendar.list_events"],
        {"time_min": "2026-11-06T00:00:00-05:00", "time_max": "2026-11-07T00:00:00-05:00"},
    )
    assert parsed.timezone == "America/New_York"
