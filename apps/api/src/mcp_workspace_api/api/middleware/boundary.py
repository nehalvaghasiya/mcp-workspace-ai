from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

if TYPE_CHECKING:
    from mcp_workspace_api.core.application_context import ApplicationContext


def install(app: FastAPI, context: ApplicationContext) -> None:
    settings = context.settings
    app = context.app

    @app.middleware("http")
    async def boundary(request: Request, call_next: Any) -> Any:
        if int(request.headers.get("content-length", "0") or 0) > 1_000_000:
            return JSONResponse({"detail": "Request is too large"}, status_code=413)
        if request.method in {"POST", "PATCH", "PUT", "DELETE"}:
            chunks, length = [], 0
            async for chunk in request.stream():
                length += len(chunk)
                if length > 1_000_000:
                    return JSONResponse({"detail": "Request is too large"}, status_code=413)
                chunks.append(chunk)
            request._body = b"".join(chunks)
        if request.url.path.startswith("/api/") and request.method in {"POST", "PATCH", "DELETE"}:
            origin = request.headers.get("origin")
            if origin and origin not in {
                settings.web_origin,
                settings.api_url,
                "http://localhost:8000",
            }:
                return JSONResponse({"detail": "Origin is not permitted"}, status_code=403)
            if request.headers.get("sec-fetch-site") == "cross-site":
                return JSONResponse(
                    {"detail": "Cross-site mutation is not permitted"}, status_code=403
                )
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Frame-Options"] = "DENY"
        return response
