from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi import Depends, FastAPI
from sqlalchemy import delete, select

from mcp_workspace_api.core.security import secret_hash
from mcp_workspace_api.db import (
    Artifact,
    Conversation,
    OAuthState,
    User,
    UserSession,
)

if TYPE_CHECKING:
    from mcp_workspace_api.core.application_context import ApplicationContext


def register(app: FastAPI, context: ApplicationContext) -> None:
    settings = context.settings
    db = context.db
    app = context.app
    require_user = context.session_service.require_user
    remove_conversation = context.deletion_service.remove_conversation
    google_disconnect = context.connection_service.google_disconnect

    @app.delete("/api/conversations/{conversation_id}")
    async def delete_conversation(
        conversation_id: str, user: User = Depends(require_user)
    ) -> dict[str, str]:
        await remove_conversation(conversation_id, user)
        return {"status": "deleted"}

    @app.delete("/api/account")
    async def delete_account(user: User = Depends(require_user)) -> dict[str, Any]:
        import shutil

        with db.session() as session:
            row = session.get(User, user.id)
            if row:
                row.deleted = True
                row.subject = "deleted:" + row.id
                row.display_name, row.email, row.timezone = "Deleted user", "", "UTC"
                row.llm_consent, row.consent_provider = False, ""
            conversations_ids = list(
                session.scalars(select(Conversation.id).where(Conversation.user_id == user.id))
            )
        for conversation_id in conversations_ids:
            await remove_conversation(conversation_id, user)
        await google_disconnect(user)
        with db.session() as session:
            for model in (UserSession, OAuthState):
                session.execute(delete(model).where(model.user_id == user.id))
            for artifact in session.scalars(select(Artifact).where(Artifact.user_id == user.id)):
                session.delete(artifact)
        for directory in (
            settings.storage / "artifacts" / user.id,
            settings.storage / "fixtures" / "mock_workspace" / secret_hash(user.id),
        ):
            if directory.is_dir():
                shutil.rmtree(directory)
        return {"status": "deleted", "remote_resources_deleted": False}
