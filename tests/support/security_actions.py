from __future__ import annotations

from typing import Any

from mcp_workspace_api.core.security import secret_hash
from mcp_workspace_api.db import (
    Approval,
    Conversation,
    Run,
    uid,
)

from tests.support import LiveServer


def seeded_run(server: LiveServer, user_id: str) -> str:
    with server.runtime.db.session() as session:
        conversation = Conversation(user_id=user_id, title="Security boundary")
        session.add(conversation)
        session.flush()
        run = Run(
            user_id=user_id,
            conversation_id=conversation.id,
            request_id=uid(),
            prompt="Explicit controlled test action",
            status="needs_approval",
        )
        session.add(run)
        session.flush()
        return str(run.id)


async def authorized_action(
    server: LiveServer, user_id: str, name: str, args: dict[str, Any]
) -> tuple[str, dict[str, str]]:
    run_id = seeded_run(server, user_id)
    approval = await server.runtime.propose(user_id, run_id, name, args)
    secret = "synthetic-one-use-capability"
    with server.runtime.db.session() as session:
        row = session.get(Approval, approval.id)
        assert row is not None
        row.status, row.capability_hash = "approved", secret_hash(secret)
    return run_id, {"id": approval.id, "secret": secret}


async def mcp_call(
    server: LiveServer,
    user_id: str,
    name: str,
    args: dict[str, Any],
    run_id: str = "",
    approval: dict[str, str] | None = None,
) -> dict[str, Any]:
    async with server.mcp(
        user_id, name.split(".")[0], tools=[name], run_id=run_id, approval=approval
    ) as client:
        result = await client.call_tool(name, {"request": args})
        assert not result.is_error, result
        return dict(result.structured_content or {})


DRAFT = {
    "to": ["test-recipient@example.invalid"],
    "subject": "Controlled synthetic action",
    "body_text": "Approved exact body",
}
