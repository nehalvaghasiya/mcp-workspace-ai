from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from sqlalchemy import delete, select

from mcp_workspace_api.db import (
    Approval,
    Artifact,
    Conversation,
    Message,
    Operation,
    Run,
    RunEvent,
    User,
)
from mcp_workspace_api.db.repositories.ownership import owned

if TYPE_CHECKING:
    from mcp_workspace_api.core.application_context import ApplicationContext


class DeletionService:
    def __init__(self, context: ApplicationContext) -> None:
        self.context = context

    async def remove_conversation(self, conversation_id: str, user: User) -> None:
        context = self.context
        settings = context.settings
        db = context.db
        runtime = context.runtime
        with db.session() as session:
            conv = owned(session, Conversation, conversation_id, user)
            runs = list(session.scalars(select(Run).where(Run.conversation_id == conv.id)))
            for run in runs:
                run.status = "cancelled"
        for run in runs:
            task = runtime.tasks.get(run.id)
            if task and not task.done():
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)
        run_ids = [run.id for run in runs]
        with db.session() as session:
            approval_ids = list(
                session.scalars(select(Approval.id).where(Approval.run_id.in_(run_ids)))
            )
            session.execute(delete(Operation).where(Operation.approval_id.in_(approval_ids)))
            session.execute(delete(Approval).where(Approval.run_id.in_(run_ids)))
            session.execute(delete(RunEvent).where(RunEvent.run_id.in_(run_ids)))
            for artifact in session.scalars(select(Artifact).where(Artifact.run_id.in_(run_ids))):
                (settings.storage / artifact.storage_key).unlink(missing_ok=True)
                session.delete(artifact)
            session.flush()
            session.execute(delete(Message).where(Message.conversation_id == conversation_id))
            session.execute(delete(Run).where(Run.id.in_(run_ids)))
            session.execute(
                delete(Conversation).where(
                    Conversation.id == conversation_id, Conversation.user_id == user.id
                )
            )
