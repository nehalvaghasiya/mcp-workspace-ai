from __future__ import annotations

import asyncio
from typing import Any

from cryptography.fernet import Fernet

from mcp_workspace_api.auth.token_vault import TokenVault
from mcp_workspace_api.contracts import (
    tool_definitions,
)
from mcp_workspace_api.core.config import Settings
from mcp_workspace_api.core.presenters import approval_json as approval_json
from mcp_workspace_api.core.presenters import artifact_json as artifact_json
from mcp_workspace_api.core.presenters import timestamp as timestamp
from mcp_workspace_api.core.security import Policy, Signer
from mcp_workspace_api.db import (
    Database,
    User,
)
from mcp_workspace_api.mcp.connection_manager import ConnectionManager
from mcp_workspace_api.mcp.discovery import Discovery
from mcp_workspace_api.mcp.gateway import Gateway
from mcp_workspace_api.mcp.tool_adapter import ToolAdapter
from mcp_workspace_api.services.approval_service import ApprovalService
from mcp_workspace_api.services.artifact_service import ArtifactService
from mcp_workspace_api.services.audit_service import AuditService
from mcp_workspace_api.services.source_resolver import resolve_sources
from mcp_workspace_api.services.workspace_file_service import WorkspaceFileService


class Runtime:
    def __init__(self, settings: Settings, db: Database) -> None:
        self.settings, self.db = settings, db
        self.tools = tool_definitions(settings.mode)
        self.signer = Signer(settings.session_secret)
        self.vault = Fernet(settings.token_encryption_key.encode())
        self.policy = Policy(settings, db)
        self.tasks: dict[str, asyncio.Task[None]] = {}
        self.write_locks: dict[str, asyncio.Lock] = {}
        self.adapters: dict[str, Any] = {}
        self.schema_digests: dict[str, str] = {}
        self.render_slots = asyncio.Semaphore(2)
        self.token_vault = TokenVault(self)
        self.account = self.token_vault.account
        self.token = self.token_vault.token
        self._refresh_token = self.token_vault._refresh_token
        self.connection_manager = ConnectionManager(self)
        self.adapter = self.connection_manager.adapter
        self.client = self.connection_manager.client
        self.discovery = Discovery(self)
        self.catalog = self.discovery.catalog
        self.tool_adapter = ToolAdapter(self)
        self.validate_arguments = self.tool_adapter.validate_arguments
        self.invoke = self.tool_adapter.invoke
        self.audit_service = AuditService(self)
        self.emit = self.audit_service.emit
        self.approval_service = ApprovalService(self)
        self.propose = self.approval_service.propose
        self._write = self.approval_service._write
        self.artifact_service = ArtifactService(self)
        self.workspace_file_service = WorkspaceFileService(self)
        self._artifact = self.artifact_service._artifact
        self.gateway = Gateway(self)
        self.execute = self.gateway.execute
        self._sources = resolve_sources

    def user_available(self, user_id: str) -> bool:
        with self.db.session() as session:
            user = session.get(User, user_id)
            return bool(user and not user.deleted)
