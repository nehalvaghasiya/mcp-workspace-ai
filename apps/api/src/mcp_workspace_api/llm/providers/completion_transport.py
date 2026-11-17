from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from collections.abc import AsyncIterator, Callable
from typing import Any, NoReturn

import httpx

from mcp_workspace_api.core.security import Denied
from mcp_workspace_api.llm.providers.transient_error import TransientModelError

MAX_RESPONSE_BYTES = 2_000_000
MODEL_REQUEST_TIMEOUT_SECONDS = 90


def raise_provider_error(error: Any) -> NoReturn:
    code = str(error.get("code", "")).lower() if isinstance(error, dict) else ""
    safe_code = code if re.fullmatch(r"[a-z0-9_]{1,64}", code) else "unspecified"
    logging.getLogger("workspace.model").warning("model_provider_error code=%s", safe_code)
    if code in {"bad_gateway", "upstream_timeout", "service_unavailable", "provider_unavailable"}:
        raise TransientModelError()
    message = str(error.get("message", "")).lower() if isinstance(error, dict) else ""
    if code in {"tool_use_failed", "tool_call_validation_error"} or (
        code == "bad_request" and "tool call validation failed" in message
    ):
        raise Denied(
            "MODEL_INVALID_RESPONSE",
            "The provider could not validate the model's tool request. Retrieved information is saved; continue to retry this model step.",
        )
    if code in {"invalid_api_key", "unauthorized", "authentication_error"}:
        raise Denied(
            "MODEL_AUTH_REQUIRED",
            "The model gateway rejected authentication; check its provider connection",
        )
    if code in {"insufficient_quota", "quota_exceeded", "rate_limit_exceeded", "rate_limited"}:
        raise Denied(
            "MODEL_RATE_LIMITED",
            "The model gateway's provider limit was reached; review its quota or retry later",
        )
    raise Denied(
        "PROVIDER_UNAVAILABLE",
        "The model gateway could not complete this request. Check its provider availability, limits, and tool compatibility.",
    )


async def bounded_chunks(response: httpx.Response) -> AsyncIterator[bytes]:
    size = 0
    async for chunk in response.aiter_bytes():
        size += len(chunk)
        if size > MAX_RESPONSE_BYTES:
            raise Denied("PROVIDER_UNAVAILABLE", "The model response exceeded its size limit")
        yield chunk


async def read_payload(response: httpx.Response) -> dict[str, Any]:
    chunks = [chunk async for chunk in bounded_chunks(response)]
    value = json.loads(b"".join(chunks))
    if not isinstance(value, dict):
        raise ValueError
    if value.get("error") is not None:
        raise_provider_error(value["error"])
    return value


async def bounded_lines(response: httpx.Response) -> AsyncIterator[str]:
    pending = b""
    async for chunk in bounded_chunks(response):
        pending += chunk
        while b"\n" in pending:
            line, pending = pending.split(b"\n", 1)
            yield line.rstrip(b"\r").decode("utf-8")
    if pending:
        yield pending.rstrip(b"\r").decode("utf-8")


def check_status(status: int) -> None:
    if status in {401, 403}:
        raise Denied(
            "MODEL_AUTH_REQUIRED",
            "The configured model rejected authentication; check its server credentials",
        )
    if status == 429:
        raise Denied("MODEL_RATE_LIMITED", "The model provider is rate limited; try again shortly")
    if status >= 400:
        raise Denied("PROVIDER_UNAVAILABLE", "The configured model provider returned an error")


async def stream_completion(
    client: httpx.AsyncClient,
    url: str,
    headers: dict[str, str],
    body: dict[str, Any],
    on_delta: Callable[[str], None],
    metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    content = ""
    calls: dict[int, dict[str, Any]] = {}
    usage: dict[str, Any] = {}
    finished = False
    async with client.stream(
        "POST",
        url,
        headers=headers,
        json=body | {"stream": True, "stream_options": {"include_usage": True}},
    ) as response:
        check_status(response.status_code)
        if "text/event-stream" not in response.headers.get("content-type", ""):
            return await read_payload(response)
        async for line in bounded_lines(response):
            if not line.startswith("data:"):
                continue
            raw = line[5:].strip()
            if raw == "[DONE]":
                finished = True
                break
            if not raw:
                continue
            event = json.loads(raw)
            if not isinstance(event, dict):
                raise ValueError
            if metrics is not None:
                metrics["stream_events"] = metrics.get("stream_events", 0) + 1
                model_name = event.get("model")
                if (
                    isinstance(model_name, str)
                    and model_name not in {"keepalive", "auto"}
                    and re.fullmatch(r"[A-Za-z0-9._:/+-]{1,128}", model_name)
                ):
                    metrics["upstream_model"] = model_name
            if event.get("error") is not None:
                raise_provider_error(event["error"])
            usage = event.get("usage") or usage
            for choice in event.get("choices") or []:
                if choice.get("index", 0) != 0:
                    continue
                if choice.get("finish_reason"):
                    if choice["finish_reason"] not in {"stop", "tool_calls", "function_call"}:
                        raise ValueError
                    finished = True
                delta = choice.get("delta") or {}
                if metrics is not None:
                    metrics["reasoning_characters"] = metrics.get("reasoning_characters", 0) + len(
                        delta.get("reasoning_content") or ""
                    )
                text = delta.get("content") or ""
                if text:
                    content += text
                    on_delta(text)
                for call in delta.get("tool_calls") or []:
                    index = call.get("index", 0)
                    item = calls.setdefault(
                        index,
                        {"id": "", "type": "function", "function": {"name": "", "arguments": ""}},
                    )
                    if call.get("id"):
                        item["id"] = call["id"]
                    for field in ("name", "arguments"):
                        item["function"][field] += call.get("function", {}).get(field, "")
    if not finished:
        raise Denied(
            "MODEL_INVALID_RESPONSE",
            "The model stream ended before its response was complete; retry the request",
        )
    message: dict[str, Any] = {"role": "assistant", "content": content or None}
    if calls:
        message["tool_calls"] = [calls[index] for index in sorted(calls)]
    return {"choices": [{"message": message}], "usage": usage, "_streamed": bool(content)}


async def _completion_once(
    url: str,
    key: str,
    body: dict[str, Any],
    on_delta: Callable[[str], None] | None = None,
    *,
    request_timeout: float | None = None,
    connect_timeout: float = 10,
    read_timeout: float = 60,
    on_progress: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    headers = {"Authorization": "Bearer " + key}
    started = time.monotonic()
    budget = MODEL_REQUEST_TIMEOUT_SECONDS if request_timeout is None else request_timeout
    metrics: dict[str, Any] = {
        "request_bytes": len(json.dumps(body).encode()),
        "timeout_seconds": budget,
    }

    async def received(response: httpx.Response) -> None:
        metrics.setdefault("first_response_ms", round((time.monotonic() - started) * 1000, 2))
        metrics["http_status"] = response.status_code

    try:
        async with (
            asyncio.timeout(budget),
            httpx.AsyncClient(
                timeout=httpx.Timeout(read_timeout, connect=connect_timeout),
                follow_redirects=False,
                trust_env=False,
                event_hooks={"response": [received]},
            ) as client,
        ):
            if on_delta:
                return await stream_completion(client, url, headers, body, on_delta, metrics)
            async with client.stream("POST", url, headers=headers, json=body) as response:
                check_status(response.status_code)
                return await read_payload(response)
    except (httpx.TimeoutException, TimeoutError):
        metrics["code"] = "MODEL_TIMED_OUT"
        raise Denied(
            "MODEL_TIMED_OUT",
            "The model took too long to respond. Retrieved information has been saved.",
        ) from None
    except httpx.HTTPError:
        metrics["code"] = "PROVIDER_UNAVAILABLE"
        raise Denied(
            "PROVIDER_UNAVAILABLE",
            "Cannot reach the configured model provider; check that its service is running",
        ) from None
    except (ValueError, TypeError, KeyError, AttributeError, IndexError):
        metrics["code"] = "MODEL_INVALID_RESPONSE"
        raise Denied(
            "MODEL_INVALID_RESPONSE", "The model provider returned an invalid response"
        ) from None
    except TransientModelError as exc:
        metrics["code"] = exc.code
        metrics["transient"] = True
        raise
    except Denied as exc:
        metrics["code"] = exc.code
        raise
    except asyncio.CancelledError:
        metrics["code"] = "CANCELLED"
        raise
    finally:
        metrics["elapsed_ms"] = round((time.monotonic() - started) * 1000, 2)
        logging.getLogger("workspace.model").info("model_request %s", json.dumps(metrics))
        if on_progress:
            on_progress(metrics)


async def completion(
    url: str,
    key: str,
    body: dict[str, Any],
    on_delta: Callable[[str], None] | None = None,
    *,
    request_timeout: float | None = None,
    connect_timeout: float = 10,
    read_timeout: float = 60,
    on_progress: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Retry one explicit gateway failure before output, within the original budget.

    This repeats model generation only. No tool executes until a complete model
    response is returned, and partial published text is never replayed.
    """
    budget = MODEL_REQUEST_TIMEOUT_SECONDS if request_timeout is None else request_timeout
    deadline = time.monotonic() + budget
    emitted = False

    def delta(text: str) -> None:
        nonlocal emitted
        emitted = emitted or bool(text)
        if on_delta:
            on_delta(text)

    for attempt in range(2):

        def progress(metrics: dict[str, Any], attempt_number: int = attempt) -> None:
            if on_progress is not None:
                on_progress({**metrics, "attempt": attempt_number + 1})

        try:
            return await _completion_once(
                url,
                key,
                body,
                delta if on_delta else None,
                request_timeout=max(0.001, deadline - time.monotonic()),
                connect_timeout=connect_timeout,
                read_timeout=read_timeout,
                on_progress=progress if on_progress is not None else None,
            )
        except TransientModelError:
            if attempt or emitted or deadline - time.monotonic() <= 0.25:
                raise
            await asyncio.sleep(0.25)
    raise AssertionError("Model attempt loop must return or raise")
