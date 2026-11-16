from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit

import httpx
from cryptography.fernet import Fernet

from mcp_workspace_api.core.runtime_settings import load_settings


async def diagnose() -> dict[str, Any]:
    settings = load_settings()
    try:
        Fernet(settings.token_encryption_key.encode())
        valid_key = True
    except ValueError:
        valid_key = False
    endpoint = urlsplit(settings.llm_base_url)
    report: dict[str, Any] = {
        "mode": settings.mode,
        "provider": settings.llm_provider,
        "model": settings.llm_model or None,
        "timeouts_seconds": {
            "model_connect": settings.model_connect_timeout,
            "model_read": settings.model_read_timeout,
            "model_request": settings.model_request_timeout,
            "workflow": settings.run_timeout,
        },
        "model_endpoint": f"{endpoint.scheme}://{endpoint.netloc}{endpoint.path}",
        "model_key_present": bool(settings.llm_api_key),
        "google_oauth_configured": bool(
            settings.google_client_id and settings.google_client_secret
        ),
        "encryption_key_valid": valid_key,
        "session_secret_configured": bool(settings.session_secret),
        "storage": str(settings.storage),
        "web_origin": settings.web_origin,
        "oauth_redirect_uri": settings.google_redirect_uri,
    }
    try:
        async with httpx.AsyncClient(timeout=5, trust_env=False, follow_redirects=False) as client:
            response = await client.get(
                settings.llm_base_url + "/models",
                headers={"Authorization": "Bearer " + settings.llm_api_key},
            )
            report["model_endpoint_status"] = response.status_code
            if response.status_code == 200 and len(response.content) < 2_000_000:
                report["selected_model_listed"] = any(
                    row.get("id") == settings.llm_model for row in response.json().get("data", [])
                )
    except (httpx.HTTPError, ValueError, TypeError, AttributeError):
        report["model_endpoint_status"] = "unavailable"
    return report
