from __future__ import annotations

from typing import Any

from fastapi import FastAPI

from mcp_workspace_api.auth.session_service import SessionService
from mcp_workspace_api.core.config import Settings
from mcp_workspace_api.core.execution_context import Runtime
from mcp_workspace_api.db import Database
from mcp_workspace_api.services.connection_service import ConnectionService
from mcp_workspace_api.services.deletion_service import DeletionService
from mcp_workspace_api.services.retention_service import RetentionService
from mcp_workspace_api.services.run_service import RunService


class ApplicationContext:
    def __init__(
        self,
        app: FastAPI,
        settings: Settings,
        db: Database,
        runtime: Runtime,
        servers: dict[str, Any],
    ) -> None:
        self.servers = servers
        self.app, self.settings, self.db, self.runtime = app, settings, db, runtime
        self.session_service = SessionService(self)
        self.run_service = RunService(self)
        self.deletion_service = DeletionService(self)
        self.retention_service = RetentionService(self)
        self.connection_service = ConnectionService(self)
