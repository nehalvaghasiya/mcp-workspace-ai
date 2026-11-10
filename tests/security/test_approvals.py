from __future__ import annotations

import asyncio
import json
from typing import Any

import pytest
from mcp_workspace_api.connectors import ConnectorError
from mcp_workspace_api.db import (
    Approval,
    Operation,
    now,
)
from sqlalchemy import select

from tests.support import Browser, LiveServer
from tests.support.security_actions import DRAFT, authorized_action, mcp_call


async def test_browser_csrf_tenant_isolation_and_rejection_causes_no_write(
    live_server: LiveServer, browser: Browser
) -> None:
    response = await browser.http.post(
        "/api/conversations", headers={"X-CSRF-Token": "wrong"}, json={"title": "Blocked"}
    )
    assert response.status_code == 403
    response = await browser.http.post(
        "/api/conversations",
        headers={"Origin": "https://attacker.invalid"},
        json={"title": "Blocked"},
    )
    assert response.status_code == 403
    conversation, run_id = await browser.start("Draft a reply to Alex")
    assert (await browser.wait(conversation, run_id))["status"] == "needs_approval"
    approvals = (await browser.http.get("/api/approvals")).json()
    approval = next(x for x in approvals if x["run_id"] == run_id)
    assert not live_server.runtime.adapter(browser.user_id)._load()["drafts"]
    async with live_server.browser() as other:
        assert (await other.http.get(f"/api/conversations/{conversation}")).status_code == 404
        assert (await other.http.get(f"/api/runs/{run_id}/trace")).status_code == 404
        assert (
            await other.http.post(
                f"/api/approvals/{approval['id']}/decide", json={"decision": "approve"}
            )
        ).status_code == 404
    assert (
        await browser.http.post(
            f"/api/approvals/{approval['id']}/decide", json={"decision": "reject"}
        )
    ).status_code == 200
    assert not live_server.runtime.adapter(browser.user_id)._load()["drafts"]


async def test_chunked_browser_request_cannot_bypass_body_size_limit(browser: Browser) -> None:
    async def content() -> Any:
        yield b'{"title":"'
        for _ in range(11):
            yield b"x" * 100000
        yield b'"}'

    response = await browser.http.post(
        "/api/conversations", headers={"Content-Type": "application/json"}, content=content()
    )
    assert response.status_code == 413
    invalid = await browser.http.post(
        "/api/conversations", json={"title": "PRIVATE_REQUEST_CANARY" + "x" * 300}
    )
    assert invalid.status_code == 422
    assert "PRIVATE_REQUEST_CANARY" not in invalid.text


async def test_approval_exact_arguments_cross_user_expiry_and_concurrent_replay(
    live_server: LiveServer, browser: Browser
) -> None:
    run_id, approval = await authorized_action(
        live_server, browser.user_id, "gmail.create_draft", DRAFT
    )
    changed = await mcp_call(
        live_server,
        browser.user_id,
        "gmail.create_draft",
        DRAFT | {"to": ["attacker@example.invalid"]},
        run_id,
        approval,
    )
    assert changed["status"] == "error"
    assert not live_server.runtime.adapter(browser.user_id)._load()["drafts"]
    async with live_server.browser() as other:
        crossed = await mcp_call(
            live_server, other.user_id, "gmail.create_draft", DRAFT, run_id, approval
        )
        assert crossed["status"] == "error"
    first, second = await asyncio.gather(
        *(
            mcp_call(live_server, browser.user_id, "gmail.create_draft", DRAFT, run_id, approval)
            for _ in range(2)
        )
    )
    assert sorted([first["status"], second["status"]]) == ["error", "success"]
    assert len(live_server.runtime.adapter(browser.user_id)._load()["drafts"]) == 1
    expired_run, expired = await authorized_action(
        live_server, browser.user_id, "gmail.create_draft", DRAFT
    )
    with live_server.runtime.db.session() as session:
        row = session.get(Approval, expired["id"])
        assert row is not None
        row.expires_at = now() - 1
    result = await mcp_call(
        live_server, browser.user_id, "gmail.create_draft", DRAFT, expired_run, expired
    )
    assert result["code"] == "APPROVAL_EXPIRED"
    assert len(live_server.runtime.adapter(browser.user_id)._load()["drafts"]) == 1


async def test_mutated_draft_target_snapshot_blocks_send(
    live_server: LiveServer, browser: Browser
) -> None:
    adapter = live_server.runtime.adapter(browser.user_id)
    draft = await adapter.call("gmail", "create_draft", DRAFT)
    args = {"draft_id": draft["id"]}
    run_id, approval = await authorized_action(
        live_server, browser.user_id, "gmail.send_draft", args
    )
    state = adapter._load()
    state["drafts"][0]["message"]["to"] = "attacker@example.invalid"
    adapter._save(state)
    result = await mcp_call(
        live_server, browser.user_id, "gmail.send_draft", args, run_id, approval
    )
    assert result["status"] == "error"
    assert not adapter._load()["sent"]


async def test_unknown_write_outcome_consumed_without_retry(
    live_server: LiveServer, browser: Browser, monkeypatch: pytest.MonkeyPatch
) -> None:
    adapter = live_server.runtime.adapter(browser.user_id)
    calls = 0

    async def uncertain(*args: Any) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        raise ConnectorError("outcome_unknown", "CANARY_PROVIDER_SECRET")

    run_id, approval = await authorized_action(
        live_server, browser.user_id, "gmail.create_draft", DRAFT
    )
    monkeypatch.setattr(adapter, "call", uncertain)
    result = await mcp_call(
        live_server, browser.user_id, "gmail.create_draft", DRAFT, run_id, approval
    )
    assert result["code"] == "OUTCOME_UNKNOWN"
    assert "CANARY" not in json.dumps(result)
    replay = await mcp_call(
        live_server, browser.user_id, "gmail.create_draft", DRAFT, run_id, approval
    )
    assert replay["status"] == "error" and calls == 1
    with live_server.runtime.db.session() as session:
        operation = session.scalar(select(Operation).where(Operation.approval_id == approval["id"]))
        assert operation is not None and operation.status == "outcome_unknown"
