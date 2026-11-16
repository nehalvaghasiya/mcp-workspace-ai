from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from mcp_workspace_api.api.middleware import boundary, errors
from mcp_workspace_api.api.v1 import (
    account,
    approvals,
    artifacts,
    auth,
    chat,
    connections,
    conversations,
    health,
    tools,
    workspace_files,
)
from mcp_workspace_api.api.v1 import settings as settings_routes
from mcp_workspace_api.core.application_context import ApplicationContext
from mcp_workspace_api.core.config import Settings
from mcp_workspace_api.core.execution_context import Runtime
from mcp_workspace_api.core.lifecycle import application_lifespan
from mcp_workspace_api.core.runtime_settings import load_settings, validate_live_configuration
from mcp_workspace_api.db import Database
from mcp_workspace_api.mcp.servers import Guard, ProtectedHTTP, build_servers


def create_app(settings: Settings | None = None) -> FastAPI:
    for name in ("httpx", "httpx2"):
        logging.getLogger(name).setLevel(logging.WARNING)
    if settings is None:
        settings = load_settings()
        validate_live_configuration(settings)
    settings.prepare()
    db = Database(f"sqlite:///{settings.storage / 'workspace.db'}")
    runtime = Runtime(settings, db)
    servers = build_servers(runtime)
    app = FastAPI(title="MCP Workspace AI", version="0.1.0")
    context = ApplicationContext(app, settings, db, runtime, servers)
    app.router.lifespan_context = application_lifespan(context, servers)
    app.state.runtime, app.state.db, app.state.settings = runtime, db, settings
    app.state.context = context
    app.state.prune_expired = context.retention_service.prune_expired
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.web_origin],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Content-Type", "X-CSRF-Token", "Last-Event-ID"],
    )
    errors.install(app)
    boundary.install(app, context)
    health.register(app, context)
    auth.register(app, context)
    connections.register(app, context)
    conversations.register(app, context)
    chat.register(app, context)
    approvals.register(app, context)
    artifacts.register(app, context)
    tools.register(app, context)
    settings_routes.register(app, context)
    workspace_files.register(app, context)
    account.register(app, context)
    for name, server in servers.items():
        app.mount(
            f"/mcp/{name}",
            ProtectedHTTP(
                server.streamable_http_app(
                    streamable_http_path="/", json_response=True, stateless_http=True
                ),
                Guard(runtime, name),
            ),
        )
    frontend = settings.web_dist_dir
    if frontend.is_dir():
        app.mount("/", StaticFiles(directory=frontend, html=True), name="web")
    return app
