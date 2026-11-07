"""Owner-scoped record lookup shared by application routes and deletion."""

from typing import Any

from fastapi import HTTPException

from mcp_workspace_api.db.models.user import User


def owned(session: Any, model: Any, item_id: str, user: User) -> Any:
    row = session.get(model, item_id)
    if not row or row.user_id != user.id:
        raise HTTPException(404, "Record not found")
    return row
