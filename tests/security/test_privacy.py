from __future__ import annotations

import asyncio
import base64
import json
import threading
import time
from typing import Any

import pytest
from mcp_documents.artifacts import ArtifactEngine
from mcp_workspace_api.agents import cloud_step
from mcp_workspace_api.core.security import Denied
from mcp_workspace_api.db import (
    User,
)

from tests.support import Browser, LiveServer
from tests.support.security_actions import DRAFT, mcp_call, seeded_run
from tests.support.stub_model import StubModel


async def test_raw_email_body_never_enters_tool_trace(
    live_server: LiveServer, browser: Browser
) -> None:
    body = "PRIVATE_BODY_CANARY_" + "x" * 2000
    adapter = live_server.runtime.adapter(browser.user_id)
    state = adapter._load()
    state["messages"][0]["payload"]["body"]["data"] = base64.urlsafe_b64encode(
        body.encode()
    ).decode()
    adapter._save(state)
    run_id = seeded_run(live_server, browser.user_id)
    result = await mcp_call(
        live_server, browser.user_id, "gmail.get_message", {"message_id": "msg-001"}, run_id
    )
    assert body in result["data"]["text"]
    trace = await browser.http.get(f"/api/runs/{run_id}/trace")
    assert trace.status_code == 200 and "PRIVATE_BODY_CANARY" not in trace.text


async def test_llm_consent_bound_to_current_provider_before_data_sharing(
    live_server: LiveServer, browser: Browser, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime = live_server.runtime
    monkeypatch.setattr(runtime.settings, "mode", "live")
    monkeypatch.setattr(runtime.settings, "llm_model", "synthetic-model")
    monkeypatch.setattr(runtime.settings, "llm_api_key", "CANARY_LLM_KEY")
    requests: list[dict[str, Any]] = []

    StubModel.requests = requests

    monkeypatch.setattr(
        "mcp_workspace_api.llm.providers.openai_compatible.httpx.AsyncClient", StubModel
    )
    evidence = [{"data": {"text": "PRIVATE_LLM_EVIDENCE"}}]
    with pytest.raises(Denied) as caught:
        await cloud_step(runtime, browser.user_id, "Summarize", evidence, [])
    assert caught.value.code == "LLM_CONSENT_REQUIRED" and not requests
    assert (
        await browser.http.patch("/api/settings", json={"llm_consent": True})
    ).status_code == 200
    assert (await cloud_step(runtime, browser.user_id, "Summarize", evidence, []))["content"]
    assert "PRIVATE_LLM_EVIDENCE" in json.dumps(requests)
    monkeypatch.setattr(runtime.settings, "llm_model", "different-model")
    with pytest.raises(Denied):
        await cloud_step(runtime, browser.user_id, "Summarize", evidence, [])
    assert len(requests) == 1


async def test_account_deletion_removes_hashed_mock_state_and_fences_identity(
    live_server: LiveServer, browser: Browser
) -> None:
    adapter = live_server.runtime.adapter(browser.user_id)
    await adapter.call("gmail", "create_draft", DRAFT)
    state_path = adapter.path
    assert state_path.is_file()
    deleted = await browser.http.delete("/api/account")
    assert deleted.status_code == 200, deleted.text
    assert not state_path.exists(), "Deletion must erase hashed per-user mock state"
    assert (await browser.http.get("/api/conversations")).status_code == 401
    with pytest.raises(Denied):
        live_server.runtime.policy.authorize(
            browser.user_id, live_server.runtime.tools["gmail.search_messages"]
        )


async def test_account_deletion_fences_inflight_renderer(
    live_server: LiveServer, browser: Browser, monkeypatch: pytest.MonkeyPatch
) -> None:
    started, resume, finished = threading.Event(), threading.Event(), threading.Event()
    original = ArtifactEngine.create

    def blocked_create(self: ArtifactEngine, *args: Any, **kwargs: Any) -> Any:
        started.set()
        assert resume.wait(10), "Test must release the renderer"
        try:
            return original(self, *args, **kwargs)
        finally:
            finished.set()

    monkeypatch.setattr(ArtifactEngine, "create", blocked_create)
    await browser.start("Create a PDF report")
    assert await asyncio.to_thread(started.wait, 10)
    deletion = asyncio.create_task(browser.http.delete("/api/account"))
    try:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            with live_server.runtime.db.session() as session:
                user = session.get(User, browser.user_id)
                fenced = bool(user and user.deleted)
            if fenced:
                break
            await asyncio.sleep(0.01)
        assert fenced
        resume.set()
        response = await deletion
        assert response.status_code == 200, response.text
        assert await asyncio.to_thread(finished.wait, 10)
        artifact_dir = live_server.settings.storage / "artifacts" / browser.user_id
        assert not [path for path in artifact_dir.rglob("*") if path.is_file()]
    finally:
        resume.set()
        await asyncio.gather(deletion, return_exceptions=True)
