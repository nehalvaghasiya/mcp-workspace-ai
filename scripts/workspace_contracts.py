"""Capture checkout contracts for independent installed-wheel verification."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from mcp_workspace_api.core.config import Settings
from mcp_workspace_api.db import Database
from mcp_workspace_api.db.migrate import migrate
from mcp_workspace_api.mcp.registry import tool_definitions
from mcp_workspace_evaluations.case_loader import cases
from sqlalchemy import inspect


def current_contracts(root: Path) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="workspace-contracts-") as temporary:
        settings = Settings(
            _env_file=None, mode="mock", llm_provider="fake", data_dir=Path(temporary)
        )  # type: ignore[call-arg]
        settings.prepare()
        database = Database(f"sqlite:///{settings.storage / 'workspace.db'}")
        try:
            migrate(database)
            inspector = inspect(database.engine)
            schema = {
                name: {
                    "columns": [
                        {
                            key: str(value) if key == "type" else value
                            for key, value in column.items()
                        }
                        for column in inspector.get_columns(name)
                    ],
                    "foreign_keys": inspector.get_foreign_keys(name),
                }
                for name in inspector.get_table_names()
            }
        finally:
            database.engine.dispose()
    return {
        "policy_digests": {name: tool.digest for name, tool in tool_definitions("mock").items()},
        "live_policy_digests": {
            name: tool.digest for name, tool in tool_definitions("live").items()
        },
        "openapi": json.loads((root / "packages/shared-types/openapi.json").read_text()),
        "cases": cases(),
        "db_schema": schema,
    }
