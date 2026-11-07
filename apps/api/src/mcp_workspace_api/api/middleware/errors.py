from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from mcp_workspace_api.core.security import Denied

if TYPE_CHECKING:
    pass


def install(app: FastAPI) -> None:
    @app.exception_handler(Denied)
    async def denied(_: Request, exc: Denied) -> JSONResponse:
        return JSONResponse({"detail": str(exc), "code": exc.code}, status_code=403)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(_: Request, exc: RequestValidationError) -> JSONResponse:
        # Do not reflect long or sensitive submitted values in validation errors.
        return JSONResponse(
            {
                "detail": [
                    {"loc": error["loc"], "msg": error["msg"], "type": error["type"]}
                    for error in exc.errors()
                ]
            },
            status_code=422,
        )
