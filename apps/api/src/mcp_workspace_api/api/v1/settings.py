from __future__ import annotations

from typing import TYPE_CHECKING, Any
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, HTTPException

from mcp_workspace_api.db import (
    User,
)
from mcp_workspace_api.schemas.requests.settings_update import SettingsUpdate
from mcp_workspace_api.schemas.responses import (
    SettingsView,
)

if TYPE_CHECKING:
    from mcp_workspace_api.core.application_context import ApplicationContext


def register(app: FastAPI, context: ApplicationContext) -> None:
    settings = context.settings
    db = context.db
    app = context.app
    require_user = context.session_service.require_user

    @app.get("/api/settings", response_model=SettingsView)
    async def get_settings(user: User = Depends(require_user)) -> dict[str, Any]:
        return {
            "provider": settings.llm_provider,
            "provider_url": settings.llm_base_url
            if settings.llm_provider != "fake"
            else "local synthetic model",
            "model": settings.llm_model or "FakeLLM",
            "llm_consent": user.llm_consent
            and user.consent_provider == settings.llm_base_url + ":" + settings.llm_model,
            "timezone": user.timezone,
        }

    @app.patch("/api/settings")
    async def patch_settings(
        body: SettingsUpdate, user: User = Depends(require_user)
    ) -> dict[str, Any]:
        if body.timezone:
            try:
                ZoneInfo(body.timezone)
            except (ValueError, KeyError):
                raise HTTPException(400, "Unknown timezone") from None
        with db.session() as session:
            row = session.get(User, user.id)
            if row:
                if body.llm_consent is not None:
                    row.llm_consent, row.consent_provider = (
                        body.llm_consent,
                        settings.llm_base_url + ":" + settings.llm_model,
                    )
                if body.timezone:
                    row.timezone = body.timezone
        return {"status": "saved"}
