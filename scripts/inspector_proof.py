"""Verify the synthetic Demo server with a separately installed MCP Inspector CLI."""

from __future__ import annotations

import argparse
import json
import os
import subprocess  # nosec B404
import sys
import tempfile
from pathlib import Path
from typing import Any

from mcp_workspace_api.cli import local_runtime, seed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--inspector", type=Path, required=True, help="Trusted installed mcp-inspector executable"
    )
    parser.add_argument(
        "--output", type=Path, default=Path("demo/evidence/reorganization/inspector-proof.json")
    )
    args = parser.parse_args()
    runtime = local_runtime()
    user = seed(runtime)
    token = runtime.signer.issue(
        {"user_id": user.id, "server": "demo", "tools": ["demo.ping"]}, ttl=300
    )
    package = args.inspector.parent.parent / "@modelcontextprotocol/inspector/package.json"
    inspector_version = (
        json.loads(package.read_text())["version"] if package.is_file() else "unknown"
    )
    proof: dict[str, Any] = {
        "inspector_version": inspector_version,
        "mode": "mock",
        "observations": [],
    }
    with tempfile.TemporaryDirectory(prefix="workspace-inspector-proof-") as temporary:
        directory = Path(temporary)
        config = directory / "session.json"
        config.write_text(
            json.dumps(
                {
                    "mcpServers": {
                        "http": {
                            "type": "streamable-http",
                            "url": runtime.settings.api_url + "/mcp/demo/",
                            "headers": {"Authorization": "Bearer " + token},
                            "protocolEra": "modern",
                        },
                        "stdio": {
                            "type": "stdio",
                            "command": sys.executable,
                            "args": [
                                "-m",
                                "mcp_workspace_api.cli",
                                "mcp",
                                "demo",
                                "--transport",
                                "stdio",
                            ],
                            "cwd": str(Path.cwd()),
                            "protocolEra": "modern",
                            "env": {
                                "MODE": "mock",
                                "LLM_PROVIDER": "fake",
                                "DATA_DIR": str(runtime.settings.data_dir.resolve()),
                                "SESSION_SECRET": runtime.settings.session_secret,
                                "TOKEN_ENCRYPTION_KEY": runtime.settings.token_encryption_key,
                                "WORKSPACE_MCP_TOKEN": token,
                            },
                        },
                    }
                }
            )
        )
        config.chmod(0o600)
        env = {
            **os.environ,
            "MCP_INSPECTOR_SECRET_STORE": "memory",
            "MCP_INSPECTOR_PERSIST_TOKENS": "none",
            "MCP_STORAGE_DIR": str(directory / "storage"),
        }
        for transport in ("http", "stdio"):
            for method in (
                "initialize",
                "tools/list",
                "tools/call",
                "resources/list",
                "prompts/list",
            ):
                command = [
                    str(args.inspector.resolve()),
                    "--cli",
                    "--config",
                    str(config),
                    "--server",
                    transport,
                    "--method",
                    method,
                    "--format",
                    "json",
                    "--connect-timeout",
                    "15000",
                ]
                if method == "tools/call":
                    command.extend(
                        ["--tool-name", "demo.ping", "--tool-args-json", '{"request":{}}']
                    )
                result = subprocess.run(
                    command, env=env, capture_output=True, text=True, timeout=30
                )  # nosec B603
                if result.returncode:
                    print(
                        f"Inspector {transport} {method} failed (exit {result.returncode}).",
                        file=sys.stderr,
                    )
                    # The config contains secrets; never dump command, environment or raw diagnostics.
                    return 1
                payload = json.loads(result.stdout)["result"]
                if method == "initialize" and payload.get("protocolVersion") != "2026-07-28":
                    raise RuntimeError("Inspector negotiated an unexpected protocol")
                if (
                    method == "tools/call"
                    and payload.get("structuredContent", {}).get("status") != "success"
                ):
                    raise RuntimeError("Inspector tool invocation did not succeed")
                proof["observations"].append(
                    {
                        "transport": transport,
                        "method": method,
                        "exit_code": result.returncode,
                        "status": "PASS",
                    }
                )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(proof, indent=2) + "\n")
    print(json.dumps(proof, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
