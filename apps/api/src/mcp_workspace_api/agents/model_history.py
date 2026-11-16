from __future__ import annotations

from typing import Any

from sqlalchemy import select

from mcp_workspace_api.core.execution_context import Runtime
from mcp_workspace_api.db import Message


def conversation_history(
    runtime: Runtime, user_id: str, conversation_id: str, prompt: str
) -> list[dict[str, Any]]:
    with runtime.db.session() as session:
        rows = list(
            session.scalars(
                select(Message)
                .where(
                    Message.user_id == user_id,
                    Message.conversation_id == conversation_id,
                    Message.role.in_(["user", "assistant"]),
                )
                .order_by(Message.created_at.desc())
                .limit(21)
            )
        )
        if rows and rows[0].role == "user" and rows[0].content == prompt:
            rows.pop(0)
        budget, history = 40000, []
        for row in rows:
            if budget <= 0:
                break
            text = row.content[: min(12000, budget)]
            budget -= len(text)
            history.append({"role": row.role, "content": text})
    return list(reversed(history))
