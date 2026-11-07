from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from sqlalchemy import delete, select

from mcp_workspace_api.db import (
    Artifact,
    Conversation,
    OAuthState,
    Run,
    User,
    UserSession,
    now,
)

if TYPE_CHECKING:
    from mcp_workspace_api.core.application_context import ApplicationContext


class RetentionService:
    def __init__(self, context: ApplicationContext) -> None:
        self.context = context

    async def prune_expired(
        self,
    ) -> dict[str, int]:
        context = self.context
        settings = context.settings
        db = context.db
        remove_conversation = context.deletion_service.remove_conversation
        cutoff = now() - settings.retention_days * 86400
        removed_conversations = 0
        with db.session() as session:
            active_ids = set(
                session.scalars(
                    select(Run.conversation_id).where(
                        Run.status.in_(["running", "queued", "needs_approval"])
                    )
                )
            )
            expired = [
                (row.id, session.get(User, row.user_id))
                for row in session.scalars(
                    select(Conversation).where(Conversation.updated_at < cutoff)
                )
                if row.id not in active_ids
            ]
        for conversation_id, user in expired:
            if user:
                await remove_conversation(conversation_id, user)
                removed_conversations += 1
        with db.session() as session:
            rows = list(session.scalars(select(Artifact).where(Artifact.created_at < cutoff)))
            for artifact in rows:
                run = session.get(Run, artifact.run_id) if artifact.run_id else None
                if not run or run.status not in {"running", "queued", "needs_approval"}:
                    (settings.storage / artifact.storage_key).unlink(missing_ok=True)
                    session.delete(artifact)
            session.execute(delete(UserSession).where(UserSession.expires_at < now()))
            session.execute(delete(OAuthState).where(OAuthState.expires_at < now()))
        return {"conversations_removed": removed_conversations}

    async def retention_loop(
        self,
    ) -> None:
        context = self.context
        prune_expired = context.retention_service.prune_expired
        import logging

        while True:
            try:
                await prune_expired()
            except Exception:
                # This records failure, never user data or provider exception bodies.
                logging.getLogger("workspace.retention").error(
                    "Retention cleanup failed; retrying at next interval"
                )
            await asyncio.sleep(3600)
