from __future__ import annotations

from typing import Any

from starlette.responses import JSONResponse

from mcp_workspace_common.errors import Denied
from mcp_workspace_common.mcp.guard import Guard


class ProtectedHTTP:
    def __init__(self, app: Any, guard: Guard) -> None:
        self.app, self.guard = app, guard

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] == "http":
            headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
            origin = headers.get("origin")
            permitted = {
                self.guard.runtime.settings.web_origin,
                self.guard.runtime.settings.api_url,
            }
            if origin and origin not in permitted:
                await JSONResponse({"code": "PERMISSION_DENIED"}, status_code=403)(
                    scope, receive, send
                )
                return
            try:
                self.guard.authenticate(headers.get("authorization", ""))
            except Denied:
                await JSONResponse({"code": "PERMISSION_DENIED"}, status_code=401)(
                    scope, receive, send
                )
                return
        await self.app(scope, receive, send)
