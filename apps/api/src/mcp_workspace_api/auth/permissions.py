from __future__ import annotations

from mcp_workspace_common.errors import Denied
from mcp_workspace_common.scopes import GOOGLE_SERVICES, scope_options_satisfied
from sqlalchemy import select

from mcp_workspace_api.contracts import Risk, ToolDefinition
from mcp_workspace_api.core.config import Settings
from mcp_workspace_api.db import Database, GoogleAccount, User


class Policy:
    def __init__(self, settings: Settings, db: Database) -> None:
        self.settings, self.db = settings, db

    def authorize(self, user_id: str, tool: ToolDefinition) -> str:
        with self.db.session() as session:
            user = session.get(User, user_id)
            if not user or user.deleted:
                raise Denied("PERMISSION_DENIED", "User is unavailable")
            if tool.server in GOOGLE_SERVICES:
                account = session.scalar(
                    select(GoogleAccount).where(GoogleAccount.user_id == user_id)
                )
                if not account or tool.server not in account.enabled:
                    raise Denied("CONNECTOR_NOT_AUTHORIZED", "Enable this connector first")
                if self.settings.mode == "live":
                    if not scope_options_satisfied(
                        account.scopes, tool.scopes, tool.scope_alternatives
                    ):
                        raise Denied(
                            "SCOPE_MISSING",
                            "Reconnect this connector to grant the required permission",
                        )
                return account.id
            return user_id

    @staticmethod
    def needs_approval(tool: ToolDefinition) -> bool:
        return tool.risk in {Risk.ACCOUNT_WRITE, Risk.EXTERNAL_EFFECT, Risk.DESTRUCTIVE}
