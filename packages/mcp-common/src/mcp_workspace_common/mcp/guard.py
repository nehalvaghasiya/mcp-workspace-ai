from __future__ import annotations

import os
from typing import Any

from mcp import MCPError

from mcp_workspace_common.errors import Denied
from mcp_workspace_common.execution.context import caller
from mcp_workspace_common.execution.server_context import ServerContext


class Guard:
    def __init__(self, runtime: ServerContext, server: str) -> None:
        self.runtime, self.server = runtime, server

    def authenticate(self, authorization: str) -> dict[str, Any]:
        token = authorization.removeprefix("Bearer ")
        claims = self.runtime.signer.verify(token, self.server)
        # Identity is supplied by the trusted host, never a browser header.
        if not self.runtime.user_available(claims.get("user_id", "")):
            raise Denied("PERMISSION_DENIED", "User is unavailable")
        return claims

    async def __call__(self, ctx: Any, call_next: Any) -> Any:
        try:
            authorization = (
                ctx.request.headers.get("authorization", "")
                if ctx.request
                else os.environ.get("WORKSPACE_MCP_TOKEN", "")
            )
            claims = self.authenticate(authorization)
            if ctx.method == "tools/call":
                name = (ctx.params or {}).get("name", "")
                if name not in claims.get("tools", []):
                    raise Denied("PERMISSION_DENIED", "Caller has no authority for this tool")
            elif ctx.method not in {
                "server/discover",
                "initialize",
                "notifications/initialized",
                "notifications/cancelled",
                "ping",
                "tools/list",
                "resources/list",
                "resources/templates/list",
                "resources/read",
                "prompts/list",
                "prompts/get",
                "completion/complete",
            }:
                raise Denied("PERMISSION_DENIED", "Method is not permitted")
            handle = caller.set(claims)
            try:
                return await call_next(ctx)
            finally:
                caller.reset(handle)
        except Denied as exc:
            raise MCPError(-32001, exc.code) from None
