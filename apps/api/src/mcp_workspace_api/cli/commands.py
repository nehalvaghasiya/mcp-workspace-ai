from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
from pathlib import Path
from typing import Any
from uuid import uuid4

from sqlalchemy import select

from mcp_workspace_api.core.runtime_settings import load_settings
from mcp_workspace_api.core.security import RotationError, rotate_credentials
from mcp_workspace_api.db import Database, GoogleAccount, User
from mcp_workspace_api.db.migrate import migrate
from mcp_workspace_api.operations.backup import backup_workspace, restore_workspace
from mcp_workspace_api.operations.backup_error import WorkspaceBackupError
from mcp_workspace_api.operations.smoke import smoke


def local_runtime() -> Any:
    from mcp_workspace_api.core.execution_context import Runtime

    settings = load_settings()
    settings.prepare()
    db = Database(f"sqlite:///{settings.storage / 'workspace.db'}")
    migrate(db)
    return Runtime(settings, db)


def seed(runtime: Any) -> User:
    if runtime.settings.mode != "mock":
        raise SystemExit("Fixture commands are only available in MODE=mock")
    with runtime.db.session() as session:
        user = session.scalar(select(User).where(User.subject == "demo:cli"))
        if not user:
            user = User(subject="demo:cli", display_name="Synthetic protocol explorer")
            session.add(user)
            session.flush()
            session.add(
                GoogleAccount(
                    user_id=user.id,
                    subject=user.subject,
                    credentials="mock",
                    scopes=[],
                    enabled=["gmail", "calendar", "drive"],
                )
            )
        return user


def main() -> None:
    parser = argparse.ArgumentParser(prog="workspace-ai")
    commands = parser.add_subparsers(dest="command", required=True)
    api = commands.add_parser("api")
    api.add_argument("--port", type=int, default=8000)
    commands.add_parser("dev")
    commands.add_parser(
        "doctor", help="Show redacted configuration and model connection diagnostics"
    )
    live_check = commands.add_parser(
        "verify-live", help="Test real model chat/tool calling and read-only Google access"
    )
    live_check.add_argument("--user-id", default="")
    mcp = commands.add_parser("mcp")
    mcp.add_argument(
        "server",
        choices=["gmail", "calendar", "drive", "docs", "sheets", "slides", "artifact", "demo"],
    )
    mcp.add_argument("--transport", choices=["stdio", "streamable-http"], default="stdio")
    token = commands.add_parser("token")
    token.add_argument(
        "server",
        choices=["gmail", "calendar", "drive", "docs", "sheets", "slides", "artifact", "demo"],
    )
    commands.add_parser("seed-demo")
    commands.add_parser("reset-demo")
    check = commands.add_parser("smoke")
    check.add_argument("--url", default="http://127.0.0.1:8000")
    eval_parser = commands.add_parser("eval")
    eval_parser.add_argument("--url", default="http://127.0.0.1:8000")
    eval_parser.add_argument("--output", default=".local/verification/evaluations/latest.json")
    eval_parser.add_argument(
        "--suite", choices=["all", "tools", "workflows", "artifacts", "security"], default="all"
    )
    export = commands.add_parser("export-schema")
    export.add_argument("--output", default="packages/shared-types/openapi.json")
    backup = commands.add_parser("backup")
    backup.add_argument("destination", type=Path)
    restore = commands.add_parser(
        "restore",
        help="Restore DB/artifacts to fresh DATA_DIR only; preserve the original encryption key",
    )
    restore.add_argument("source", type=Path)
    rotate = commands.add_parser(
        "rotate-key",
        help="Offline only: stop the app, back up data, and set NEW_TOKEN_ENCRYPTION_KEY in the environment",
    )
    rotate.add_argument(
        "--key-version",
        default=uuid4().hex,
        help="Nonsecret replacement key version identifier (default: random opaque ID)",
    )
    args = parser.parse_args()
    if args.command == "api":
        import uvicorn

        uvicorn.run(
            "mcp_workspace_api.main:create_app",
            factory=True,
            host="127.0.0.1",
            port=args.port,
            access_log=False,
        )
    elif args.command == "dev":
        from mcp_workspace_api.operations.dev_server import run_dev

        raise SystemExit(run_dev())
    elif args.command == "doctor":
        from mcp_workspace_api.operations.diagnostics import diagnose

        print(json.dumps(asyncio.run(diagnose()), indent=2))
    elif args.command == "verify-live":
        from mcp_workspace_api.operations.live_verification import verify_live

        report = asyncio.run(verify_live(local_runtime(), args.user_id))
        print(json.dumps(report, indent=2))
        if report["status"] != "PASS":
            raise SystemExit(1)
    elif args.command in {"mcp", "token", "seed-demo", "reset-demo"}:
        from mcp_workspace_api.mcp.servers import build_servers

        runtime = local_runtime()
        if args.command == "mcp":
            # Refuse anonymous stdio before the protocol starts; no diagnostics on stdout.
            runtime.signer.verify(
                os.environ.get("WORKSPACE_MCP_TOKEN", "").removeprefix("Bearer "), args.server
            )
            servers = build_servers(runtime)
            if args.server not in servers:
                raise SystemExit("This MCP service is not available in the selected runtime mode")
            servers[args.server].run(args.transport)
        else:
            user = seed(runtime)
            if args.command == "token":
                names = [
                    name
                    for name, definition in runtime.tools.items()
                    if definition.server == args.server
                    and not runtime.policy.needs_approval(definition)
                ]
                print(
                    runtime.signer.issue(
                        {"user_id": user.id, "server": args.server, "tools": names}, ttl=300
                    )
                )
            elif args.command == "reset-demo":
                path = runtime.adapter(user.id).directory
                if path.exists():
                    shutil.rmtree(path)
                print("Reset the synthetic CLI fixture workspace; live data was not accessed.")
            else:
                print(
                    json.dumps(
                        {
                            "user_id": user.id,
                            "mode": "mock",
                            "fixture_clock": "2026-11-05T12:00:00-06:00",
                        }
                    )
                )
    elif args.command == "smoke":
        print(json.dumps(asyncio.run(smoke(args.url)), indent=2))
    elif args.command == "eval":
        from mcp_workspace_evaluations.runner import evaluate
        from mcp_workspace_evaluations.suites import SUITES

        report = asyncio.run(evaluate(args.url, Path(args.output), SUITES[args.suite]))
        print(json.dumps(report, indent=2))
        if report["passed"] != report["cases"]:
            raise SystemExit(1)
    elif args.command == "export-schema":
        from mcp_workspace_api.main import create_app

        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(create_app().openapi(), indent=2))
    elif args.command == "backup":
        settings = load_settings()
        settings.prepare()
        try:
            backup_workspace(settings, args.destination)
        except WorkspaceBackupError as exc:
            raise SystemExit(str(exc)) from None
        print("Database and artifacts backed up. Keep the encryption key separately.")
    elif args.command == "restore":
        settings = load_settings()
        settings.prepare()
        try:
            restore_workspace(settings, args.source)
        except WorkspaceBackupError as exc:
            raise SystemExit(str(exc)) from None
        print(
            "Database and artifacts restored to fresh storage. Keep the original TOKEN_ENCRYPTION_KEY and TOKEN_KEY_VERSION before starting the app."
        )
    elif args.command == "rotate-key":
        new_key = os.environ.get("NEW_TOKEN_ENCRYPTION_KEY", "")
        if not new_key:
            raise SystemExit(
                "Set NEW_TOKEN_ENCRYPTION_KEY in the operator environment; keep the app stopped during rotation"
            )
        settings = load_settings()
        settings.prepare()
        if not (settings.storage / "workspace.db").is_file():
            raise SystemExit("An existing workspace database is required for offline rotation")
        database = Database(f"sqlite:///{settings.storage / 'workspace.db'}")
        try:
            migrate(database)
            count = rotate_credentials(
                database, settings.token_encryption_key, new_key, args.key_version
            )
        except RotationError as exc:
            raise SystemExit(str(exc)) from None
        finally:
            database.engine.dispose()
        print(
            f"Rotated {count} credential records. Keep the app stopped until TOKEN_ENCRYPTION_KEY is replaced and TOKEN_KEY_VERSION is set to {args.key_version}."
        )
