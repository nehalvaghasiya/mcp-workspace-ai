from __future__ import annotations

from typing import Any
from uuid import uuid4

from mcp_workspace_api.db import Approval, Operation, Run
from sqlalchemy import select

from tests.support import Browser, LiveServer


async def stage_action(
    live_server: LiveServer, browser: Browser, tool: str, arguments: dict[str, Any]
) -> tuple[str, str, str]:
    """Persist a deterministic one-step plan; actual execution uses API + MCP."""
    conversation = await browser.conversation()
    with live_server.runtime.db.session() as session:
        run = Run(
            user_id=browser.user_id,
            conversation_id=conversation,
            request_id=uuid4().hex,
            prompt="Explicit synthetic action",
            status="needs_approval",
            state={"steps": [{"tool": tool, "arguments": arguments}], "position": 0, "results": []},
        )
        session.add(run)
        session.flush()
        run_id = run.id
    approval = await live_server.runtime.propose(browser.user_id, run_id, tool, arguments)
    return conversation, run_id, approval.id


async def approved_action(
    live_server: LiveServer, browser: Browser, tool: str, arguments: dict[str, Any]
) -> dict[str, Any]:
    before = live_server.runtime.adapter(browser.user_id)._load()
    conversation, run_id, approval_id = await stage_action(live_server, browser, tool, arguments)
    # Proposal and direct invocation without the capability have zero side effects.
    assert live_server.runtime.adapter(browser.user_id)._load() == before
    async with live_server.mcp(browser.user_id, tool.split(".")[0], run_id=run_id) as client:
        denied = await client.call_tool(tool, {"request": arguments})
    assert denied.structured_content["code"] == "APPROVAL_REQUIRED"
    assert live_server.runtime.adapter(browser.user_id)._load() == before
    response = await browser.http.post(
        f"/api/approvals/{approval_id}/decide", json={"decision": "approve"}
    )
    assert response.status_code == 200, response.text
    run = await browser.wait(conversation, run_id, statuses={"completed", "failed", "cancelled"})
    assert run["status"] == "completed", run
    with live_server.runtime.db.session() as session:
        approval = session.get(Approval, approval_id)
        operation = session.scalar(select(Operation).where(Operation.approval_id == approval_id))
        assert approval.status == "consumed"
        assert operation.status == "completed"
        result = dict(operation.result)
    after = live_server.runtime.adapter(browser.user_id)._load()
    assert after != before
    replay = await browser.http.post(
        f"/api/approvals/{approval_id}/decide", json={"decision": "approve"}
    )
    assert replay.status_code == 409
    assert live_server.runtime.adapter(browser.user_id)._load() == after
    return result
