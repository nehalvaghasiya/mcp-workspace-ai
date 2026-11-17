from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi import Depends, FastAPI
from sqlalchemy import select

from mcp_workspace_api.core.execution_context import (
    timestamp,
)
from mcp_workspace_api.db import (
    Conversation,
    Message,
    Run,
    User,
)
from mcp_workspace_api.db.repositories.ownership import owned
from mcp_workspace_api.schemas.presenters import run_json
from mcp_workspace_api.schemas.requests.new_conversation import NewConversation
from mcp_workspace_api.schemas.responses import (
    ConversationSummary,
    ConversationView,
)

if TYPE_CHECKING:
    from mcp_workspace_api.core.application_context import ApplicationContext


def register(app: FastAPI, context: ApplicationContext) -> None:
    db = context.db
    app = context.app
    require_user = context.session_service.require_user

    @app.get("/api/conversations", response_model=list[ConversationSummary])
    async def conversations(user: User = Depends(require_user)) -> list[dict[str, Any]]:
        with db.session() as session:
            return [
                {"id": row.id, "title": row.title, "updated_at": timestamp(row.updated_at)}
                for row in session.scalars(
                    select(Conversation)
                    .where(Conversation.user_id == user.id)
                    .order_by(Conversation.updated_at.desc())
                    .limit(100)
                )
            ]

    @app.post("/api/conversations", response_model=ConversationSummary)
    async def new_conversation(
        body: NewConversation, user: User = Depends(require_user)
    ) -> dict[str, Any]:
        with db.session() as session:
            row = Conversation(user_id=user.id, title=body.title)
            session.add(row)
            session.flush()
            return {"id": row.id, "title": row.title, "updated_at": timestamp(row.updated_at)}

    @app.get("/api/conversations/{conversation_id}", response_model=ConversationView)
    async def conversation(
        conversation_id: str, user: User = Depends(require_user)
    ) -> dict[str, Any]:
        with db.session() as session:
            row = owned(session, Conversation, conversation_id, user)
            messages = session.scalars(
                select(Message)
                .where(Message.conversation_id == row.id, Message.user_id == user.id)
                .order_by(Message.created_at)
                .limit(200)
            )
            runs = session.scalars(
                select(Run)
                .where(Run.conversation_id == row.id, Run.user_id == user.id)
                .order_by(Run.created_at)
                .limit(200)
            )
            return {
                "id": row.id,
                "title": row.title,
                "messages": [
                    {
                        "id": msg.id,
                        "role": msg.role,
                        "content": msg.content,
                        "sources": msg.sources,
                        "artifacts": msg.artifacts,
                        "workspace_files": msg.workspace_files,
                    }
                    for msg in messages
                ],
                "runs": [run_json(run, context.runtime) for run in runs],
            }
