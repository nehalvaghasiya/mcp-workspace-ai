from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import select

from mcp_workspace_api.db import (
    Run,
    RunEvent,
    User,
)

if TYPE_CHECKING:
    from mcp_workspace_api.core.execution_context import Runtime


class AuditService:
    def __init__(self, context: Runtime) -> None:
        self.context = context

    def emit(self, run_id: str, event_type: str, data: dict[str, Any]) -> None:
        context = self.context
        with context.db.session() as session:
            run = session.get(Run, run_id)
            if not run:
                return
            user = session.get(User, run.user_id)
            if not user or user.deleted:
                return
            last = (
                session.scalar(
                    select(RunEvent.sequence)
                    .where(RunEvent.run_id == run_id)
                    .order_by(RunEvent.sequence.desc())
                    .limit(1)
                )
                or 0
            )
            session.add(
                RunEvent(
                    user_id=run.user_id,
                    run_id=run_id,
                    sequence=last + 1,
                    type=event_type,
                    data=data,
                )
            )
