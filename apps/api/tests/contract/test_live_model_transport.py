from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator

import httpx
import pytest
import respx
from mcp_workspace_api.core.security import Denied
from mcp_workspace_api.llm.providers import completion_transport
from mcp_workspace_api.llm.providers.completion_transport import completion

ENDPOINT = "https://model.example.invalid/v1/chat/completions"


class UnfinishedGatewayStream(httpx.AsyncByteStream):
    def __init__(self, chunks: list[bytes], delay: float = 0) -> None:
        self.chunks = chunks
        self.delay = delay

    async def __aiter__(self) -> AsyncIterator[bytes]:
        for chunk in self.chunks:
            yield chunk
            await asyncio.sleep(self.delay)
        raise AssertionError("The response must complete or time out before consuming more data")


def event(delta: dict[str, object], *, finish: str | None = None) -> str:
    return (
        "data: "
        + json.dumps({"choices": [{"index": 0, "delta": delta, "finish_reason": finish}]})
        + "\n\n"
    )


@pytest.mark.parametrize(
    "status, code",
    [
        (401, "MODEL_AUTH_REQUIRED"),
        (403, "MODEL_AUTH_REQUIRED"),
        (429, "MODEL_RATE_LIMITED"),
        (503, "PROVIDER_UNAVAILABLE"),
    ],
)
@pytest.mark.parametrize("stream", [False, True])
async def test_provider_failures_are_typed_and_never_reflect_response_secrets(
    status: int, code: str, stream: bool
) -> None:
    with respx.mock() as router:
        route = router.post(ENDPOINT).mock(
            return_value=httpx.Response(status, text="PRIVATE_PROVIDER_BODY_AND_KEY")
        )
        with pytest.raises(Denied) as caught:
            await completion(
                ENDPOINT,
                "SYNTHETIC_AUTH_KEY",
                {"model": "configured-model", "messages": []},
                (lambda text: None) if stream else None,
            )
        assert caught.value.code == code
        assert "PRIVATE" not in str(caught.value) and "SYNTHETIC_AUTH_KEY" not in str(caught.value)
        assert route.call_count == 1


@pytest.mark.parametrize(
    "content, content_type",
    [
        (b"{PRIVATE_INVALID_JSON", "application/json"),
        (b"data: {PRIVATE_INVALID_JSON\n\n", "text/event-stream"),
        (b'data: ["PRIVATE_INVALID_EVENT"]\n\ndata: [DONE]\n\n', "text/event-stream"),
    ],
)
async def test_invalid_json_is_sanitized_for_streaming_and_json(
    content: bytes, content_type: str
) -> None:
    with respx.mock() as router:
        router.post(ENDPOINT).mock(
            return_value=httpx.Response(
                200, content=content, headers={"content-type": content_type}
            )
        )
        with pytest.raises(Denied) as caught:
            await completion(ENDPOINT, "SYNTHETIC_AUTH_KEY", {}, lambda text: None)
        assert caught.value.code == "MODEL_INVALID_RESPONSE"
        assert "PRIVATE" not in str(caught.value)


async def test_truncated_stream_must_not_turn_partial_content_into_a_completed_answer() -> None:
    deltas: list[str] = []
    with respx.mock() as router:
        router.post(ENDPOINT).mock(
            return_value=httpx.Response(
                200,
                text=event({"content": "Partial answer"}),
                headers={"content-type": "text/event-stream"},
            )
        )
        with pytest.raises(Denied) as caught:
            await completion(ENDPOINT, "SYNTHETIC_AUTH_KEY", {}, deltas.append)
        assert caught.value.code == "MODEL_INVALID_RESPONSE"


async def test_stream_assembles_split_tool_arguments_and_usage_without_emitting_an_answer() -> None:
    deltas: list[str] = []
    stream = event(
        {
            "tool_calls": [
                {
                    "index": 0,
                    "id": "call-real",
                    "type": "function",
                    "function": {"name": "gmail__get_message", "arguments": '{"request":'},
                }
            ]
        }
    )
    stream += event(
        {
            "tool_calls": [
                {"index": 0, "function": {"arguments": '{"message_id":"selected-message"}}'}}
            ]
        },
        finish="tool_calls",
    )
    stream += (
        "data: "
        + json.dumps({"choices": [], "usage": {"prompt_tokens": 12, "completion_tokens": 4}})
        + "\n\ndata: [DONE]\n\n"
    )
    with respx.mock() as router:
        router.post(ENDPOINT).mock(
            return_value=httpx.Response(
                200, text=stream, headers={"content-type": "text/event-stream"}
            )
        )
        response = await completion(ENDPOINT, "SYNTHETIC_AUTH_KEY", {}, deltas.append)
    call = response["choices"][0]["message"]["tool_calls"][0]
    assert call["id"] == "call-real" and call["function"]["name"] == "gmail__get_message"
    assert json.loads(call["function"]["arguments"]) == {
        "request": {"message_id": "selected-message"}
    }
    assert response["usage"]["prompt_tokens"] == 12
    assert deltas == []


async def test_stream_byte_limit_applies_before_accepting_an_oversized_response() -> None:
    with respx.mock() as router:
        router.post(ENDPOINT).mock(
            return_value=httpx.Response(
                200,
                text=event({"content": "x" * 2_000_001}),
                headers={"content-type": "text/event-stream"},
            )
        )
        with pytest.raises(Denied) as caught:
            await completion(ENDPOINT, "SYNTHETIC_AUTH_KEY", {}, lambda text: None)
        assert caught.value.code == "PROVIDER_UNAVAILABLE"


async def test_provider_timeout_is_sanitized() -> None:
    with respx.mock() as router:
        router.post(ENDPOINT).mock(
            side_effect=httpx.ReadTimeout("PRIVATE_TIMEOUT_WITH_CREDENTIALS")
        )
        with pytest.raises(Denied) as caught:
            await completion(ENDPOINT, "SYNTHETIC_AUTH_KEY", {})
        assert caught.value.code == "MODEL_TIMED_OUT" and "PRIVATE" not in str(caught.value)


@pytest.mark.parametrize("stream", [True, False])
@pytest.mark.parametrize(
    "provider_code, expected_code",
    [
        ("bad_gateway", "PROVIDER_UNAVAILABLE"),
        ("tool_use_failed", "MODEL_INVALID_RESPONSE"),
        ("bad_request", "MODEL_INVALID_RESPONSE"),
        ("invalid_api_key", "MODEL_AUTH_REQUIRED"),
        ("insufficient_quota", "MODEL_RATE_LIMITED"),
    ],
)
async def test_gateway_error_inside_http_200_is_a_provider_failure(
    stream: bool, provider_code: str, expected_code: str
) -> None:
    payload = {
        "error": {
            "type": "server_error",
            "code": provider_code,
            "message": ("Tool call validation failed: " if provider_code == "bad_request" else "")
            + "PRIVATE_UPSTREAM_KEY_AND_DIAGNOSTICS",
        },
        "diagnostics": {"private": "PRIVATE_DIAGNOSTIC"},
    }
    body = (
        ("data: " + json.dumps(payload) + "\n\n").encode()
        if stream
        else json.dumps(payload).encode()
    )
    with respx.mock() as router:
        router.post(ENDPOINT).mock(
            return_value=httpx.Response(
                200,
                content=body,
                headers={"content-type": "text/event-stream" if stream else "application/json"},
            )
        )
        with pytest.raises(Denied) as caught:
            await completion(
                ENDPOINT, "SYNTHETIC_AUTH_KEY", {}, (lambda text: None) if stream else None
            )
    assert caught.value.code == expected_code
    assert "PRIVATE" not in str(caught.value)


async def test_stream_accepts_nullable_gateway_keepalive_and_terminal_fields() -> None:
    chunks = [
        {"choices": None},
        {"choices": [{"index": 0, "delta": {"content": "Hello!", "tool_calls": None}}]},
        {"choices": [{"index": 0, "delta": None, "finish_reason": "stop"}]},
        {"choices": None, "usage": {"completion_tokens": 2}},
    ]
    stream = "".join("data: " + json.dumps(chunk) + "\n\n" for chunk in chunks)
    stream += "data: [DONE]\n\n"
    deltas: list[str] = []
    with respx.mock() as router:
        router.post(ENDPOINT).mock(
            return_value=httpx.Response(
                200, text=stream, headers={"content-type": "text/event-stream"}
            )
        )
        response = await completion(ENDPOINT, "SYNTHETIC_AUTH_KEY", {}, deltas.append)
    assert response["choices"][0]["message"]["content"] == "Hello!"
    assert response["usage"] == {"completion_tokens": 2}
    assert deltas == ["Hello!"]


async def test_done_marker_completes_without_waiting_for_gateway_to_close_connection() -> None:
    with respx.mock() as router:
        router.post(ENDPOINT).mock(
            return_value=httpx.Response(
                200,
                stream=UnfinishedGatewayStream(
                    [(event({"content": "Hello!"}, finish="stop") + "data: [DONE]\n\n").encode()]
                ),
                headers={"content-type": "text/event-stream"},
            )
        )
        response = await completion(ENDPOINT, "SYNTHETIC_AUTH_KEY", {}, lambda text: None)
    assert response["choices"][0]["message"]["content"] == "Hello!"


async def test_gateway_keepalives_cannot_extend_request_deadline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(completion_transport, "MODEL_REQUEST_TIMEOUT_SECONDS", 0.02)

    with respx.mock() as router:
        router.post(ENDPOINT).mock(
            return_value=httpx.Response(
                200,
                stream=UnfinishedGatewayStream([b'data: {"choices": []}\n\n'] * 100, delay=0.005),
                headers={"content-type": "text/event-stream"},
            )
        )
        with pytest.raises(Denied) as caught:
            await completion(ENDPOINT, "SYNTHETIC_AUTH_KEY", {}, lambda text: None)
    assert caught.value.code == "MODEL_TIMED_OUT"


async def test_transient_gateway_failure_retries_generation_once_before_any_output() -> None:
    deltas: list[str] = []
    with respx.mock() as router:
        route = router.post(ENDPOINT).mock(
            side_effect=[
                httpx.Response(
                    200, json={"error": {"code": "bad_gateway", "message": "PRIVATE_UPSTREAM"}}
                ),
                httpx.Response(200, json={"choices": [{"message": {"content": "Recovered"}}]}),
            ]
        )
        result = await completion(ENDPOINT, "SYNTHETIC_KEY", {}, deltas.append)
    assert result["choices"][0]["message"]["content"] == "Recovered"
    assert route.call_count == 2


async def test_transient_failure_after_published_text_is_not_retried() -> None:
    deltas: list[str] = []
    stream = event({"content": "Partial"}) + 'data: {"error":{"code":"bad_gateway"}}\n\n'
    with respx.mock() as router:
        route = router.post(ENDPOINT).mock(
            return_value=httpx.Response(
                200, text=stream, headers={"content-type": "text/event-stream"}
            )
        )
        with pytest.raises(Denied) as caught:
            await completion(ENDPOINT, "SYNTHETIC_KEY", {}, deltas.append)
    assert caught.value.code == "PROVIDER_UNAVAILABLE" and route.call_count == 1
    assert deltas == ["Partial"]
