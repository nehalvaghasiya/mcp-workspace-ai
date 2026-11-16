from __future__ import annotations

import hashlib
import json

from mcp_workspace_api.core.config import Settings


def runtime_identity(settings: Settings) -> str:
    """Identify this local workspace/configuration without exposing paths or credentials."""
    public_configuration = {
        "storage": str(settings.storage),
        "mode": settings.mode,
        "api_url": settings.api_url,
        "web_origin": settings.web_origin,
        "provider": settings.llm_provider,
        "endpoint": settings.llm_base_url,
        "model": settings.llm_model,
    }
    return hashlib.sha256(json.dumps(public_configuration, sort_keys=True).encode()).hexdigest()
