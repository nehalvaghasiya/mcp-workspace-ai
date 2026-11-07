"""Recovery and transport faults must preserve evidence without replaying effects."""

from __future__ import annotations

import asyncio
import json
import socket
import time
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from mcp_workspace_api.core.config import Settings
from mcp_workspace_api.core.security import Denied
from mcp_workspace_api.db import Approval, GoogleAccount, Operation, Run, now, uid
from mcp_workspace_api.main import create_app
from sqlalchemy import select


def test_restart_preserves_session_events_and_pending_work_without_write_replay(
    tmp_path: Path,
) -> None:
    settings = Settings(_env_file=None, mode="mock", data_dir=tmp_path, llm_provider="fake")
    first = create_app(settings)
    with TestClient(first) as client:
        identity = client.post("/api/auth/demo").json()
        user = identity["user"]["id"]
        client.headers["X-CSRF-Token"] = identity["csrf_token"]
        conversation = client.post("/api/conversations", json={}).json()["id"]
        cookies = dict(client.cookies)
        runs: dict[str, str] = {}
        with first.state.db.session() as session:
            account = session.scalar(select(GoogleAccount).where(GoogleAccount.user_id == user))
            assert account is not None
            for status in ("running", "queued", "needs_approval", "completed"):
                run = Run(
                    user_id=user,
                    conversation_id=conversation,
                    request_id=uid(),
                    prompt="Controlled recovery fixture",
                    status=status,
                    state={"position": 1, "results": []},
                )
                session.add(run)
                session.flush()
                runs[status] = run.id
            approval = Approval(
                user_id=user,
                run_id=runs["running"],
                tool="gmail.send_draft",
                arguments={"draft_id": "controlled-draft"},
                action_digest="controlled-digest",
                account_id=account.id,
                expires_at=now() + 300,
                status="consumed",
            )
            pending = Approval(
                user_id=user,
                run_id=runs["needs_approval"],
                tool="gmail.create_draft",
                arguments={"to": ["alex@example.invalid"], "subject": "Controlled draft"},
                action_digest="pending-digest",
                account_id=account.id,
                expires_at=now() + 300,
            )
            session.add_all([approval, pending])
            session.flush()
            session.add(Operation(user_id=user, approval_id=approval.id, status="dispatched"))
            consumed_id, pending_id = approval.id, pending.id
        first.state.runtime.emit(runs["running"], "tool.started", {"tool": "gmail.send_draft"})

    restarted = create_app(settings)
    with TestClient(restarted) as client:
        client.cookies.update(cookies)
        client.headers["X-CSRF-Token"] = identity["csrf_token"]
        assert client.get("/api/session").json()["user"]["id"] == user
        response = client.get(f"/api/conversations/{conversation}")
        assert response.status_code == 200
        statuses = {run["id"]: run["status"] for run in response.json()["runs"]}
        assert statuses == {
            runs["running"]: "interrupted",
            runs["queued"]: "interrupted",
            runs["needs_approval"]: "needs_approval",
            runs["completed"]: "completed",
        }
        approvals = {row["id"]: row["status"] for row in client.get("/api/approvals").json()}
        assert approvals[pending_id] == "pending"
        assert approvals[consumed_id] == "consumed"
        assert (
            client.post(
                f"/api/approvals/{consumed_id}/decide", json={"decision": "approve"}
            ).status_code
            == 409
        )
        stream = client.get(f"/api/runs/{runs['running']}/events").text
        events = [
            json.loads(line.removeprefix("data: "))
            for line in stream.splitlines()
            if line.startswith("data: ")
        ]
        assert len(events) == 1 and events[0]["type"] == "tool.started"
        replay = client.get(
            f"/api/runs/{runs['running']}/events",
            headers={"Last-Event-ID": str(events[0]["id"])},
        )
        assert "data: " not in replay.text
        with restarted.state.db.session() as session:
            operations = list(session.scalars(select(Operation)))
            assert len(operations) == 1 and operations[0].status == "outcome_unknown"
        assert not restarted.state.runtime.tasks
        assert not restarted.state.runtime.adapters


async def test_changed_discovery_digest_blocks_run_before_any_tool(
    live_server: Any, browser: Any
) -> None:
    await live_server.runtime.catalog(browser.user_id)
    live_server.runtime.schema_digests["gmail.search_messages"] = "different-trusted-schema"
    with pytest.raises(Denied) as rejected:
        await live_server.runtime.catalog(browser.user_id)
    assert rejected.value.code == "TOOL_SCHEMA_CHANGED"
    conversation, run_id = await browser.start("Create a PDF from launch emails")
    run = await browser.wait(conversation, run_id)
    assert run["status"] == "failed"
    assert "schema" in run["error"].lower()
    assert (await browser.http.get(f"/api/runs/{run_id}/trace")).json() == []
    assert (await browser.http.get("/api/artifacts")).json() == []


@pytest.mark.parametrize("fault", ["unavailable", "timeout"])
async def test_transport_fault_stops_future_steps_without_effects(
    live_server: Any, browser: Any, monkeypatch: pytest.MonkeyPatch, fault: str
) -> None:
    monkeypatch.setattr(live_server.settings, "tool_timeout", 1)
    if fault == "unavailable":
        with socket.socket() as reserved:
            reserved.bind(("127.0.0.1", 0))
            port = reserved.getsockname()[1]
        monkeypatch.setattr(live_server.settings, "api_url", f"http://127.0.0.1:{port}")
    else:

        async def delayed_read(*args: Any) -> dict[str, Any]:
            await asyncio.sleep(10)
            pytest.fail("Read continued after its deadline")

        monkeypatch.setattr(live_server.runtime.adapter(browser.user_id), "call", delayed_read)
    started = time.monotonic()
    conversation, run_id = await browser.start("Create a PDF from launch emails")
    run = await browser.wait(conversation, run_id, deadline_seconds=6)
    assert run["status"] == "failed"
    assert time.monotonic() - started < 6
    assert (await browser.http.get("/api/artifacts")).json() == []
    assert (await browser.http.get("/api/approvals")).json() == []
    with live_server.runtime.db.session() as session:
        assert list(session.scalars(select(Operation))) == []
