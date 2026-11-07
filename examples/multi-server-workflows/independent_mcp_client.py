"""Independent official-SDK discovery and bounded read; token comes from the environment.

Example: uv run python examples/multi-server-workflows/independent_mcp_client.py demo --transport stdio
Obtain a short-lived caller assertion with ``workspace-ai token demo`` and set
WORKSPACE_MCP_TOKEN without printing it in logs. This is never a Google token.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import httpx2
from mcp import Client, StdioServerParameters

ROOT = Path(__file__).resolve().parents[2]

READS: dict[str, tuple[str, dict[str, Any]]] = {
    "demo": ("demo.ping", {}),
    "gmail": ("gmail.list_labels", {}),
    "calendar": ("calendar.list_calendars", {}),
    "drive": ("drive.list_folder", {"max_results": 2}),
    "artifact": ("artifact.list_artifacts", {"max_results": 2}),
}


async def inspect(client: Client, namespace: str) -> dict[str, Any]:
    discovered = await client.list_tools()
    names = sorted(
        tool.name
        for tool in discovered.tools
        if re.fullmatch(r"[a-z]+\.[a-z_]+", tool.name) and tool.name.startswith(namespace + ".")
    )
    name, arguments = READS[namespace]
    result = await client.call_tool(name, {"request": arguments})
    content = result.structured_content or {}
    data = content.get("data", {})
    # Only names, protocol, counts and result state leave this client; no bodies,
    # document text, account identities, credentials, schemas or source snippets.
    counts = (
        {
            key: len(value)
            for key, value in data.items()
            if key in {"labels", "calendars", "files", "artifacts"} and isinstance(value, list)
        }
        if isinstance(data, dict)
        else {}
    )
    return {
        "protocol_version": client.protocol_version,
        "namespace": namespace,
        "tools": names,
        "read": {
            "tool": name,
            "status": "error" if result.is_error else content.get("status", "unknown"),
            "counts": counts,
        },
    }


async def run(namespace: str, transport_name: str, url: str, token: str) -> dict[str, Any]:
    if transport_name == "stdio":
        parameters = StdioServerParameters(
            command=sys.executable,
            args=["-m", "mcp_workspace_api.cli", "mcp", namespace, "--transport", "stdio"],
            env={**os.environ, "WORKSPACE_MCP_TOKEN": token},
            cwd=ROOT,
        )
        async with Client(parameters, read_timeout_seconds=15) as client:
            return await inspect(client, namespace)

    from mcp.client.streamable_http import streamable_http_client

    @asynccontextmanager
    async def transport() -> AsyncIterator[Any]:
        async with httpx2.AsyncClient(
            headers={"Authorization": "Bearer " + token.removeprefix("Bearer ")}, timeout=15
        ) as http:
            async with streamable_http_client(
                url.rstrip("/") + f"/mcp/{namespace}/", http_client=http
            ) as streams:
                yield streams

    async with Client(transport(), read_timeout_seconds=15) as client:
        return await inspect(client, namespace)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("namespace", nargs="?", default="demo", choices=READS)
    parser.add_argument("--transport", choices=["http", "stdio"], default="http")
    parser.add_argument(
        "--url", default="http://127.0.0.1:8000", help="Trusted workspace API base URL"
    )
    args = parser.parse_args()
    token = os.environ.get("WORKSPACE_MCP_TOKEN", "").strip()
    if not token:
        parser.error("Set WORKSPACE_MCP_TOKEN to a short-lived app caller assertion")
    parsed = urlsplit(args.url)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        parser.error("Use an HTTP(S) API base URL without credentials, query or fragment")
    if parsed.scheme == "http" and parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
        parser.error("Remote endpoints require HTTPS")
    try:
        result = asyncio.run(run(args.namespace, args.transport, args.url, token))
        print(json.dumps(result, indent=2))
        return 0 if result["read"]["status"] == "success" else 1
    except Exception as exc:
        # Network/server exception details may contain untrusted or sensitive data.
        print(
            f"MCP request failed ({type(exc).__name__}); check endpoint, token scope, and server mode.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
