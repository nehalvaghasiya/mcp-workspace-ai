from __future__ import annotations

from mcp_workspace_api.db import GoogleAccount

ERROR_MESSAGES = {
    "auth_required": "Google authorization expired or was revoked. Reconnect this account.",
    "permission_denied": "Google denied access. Review the granted permissions and the selected resource.",
    "provider_unavailable": "Google is temporarily unavailable. Retry a read to check the connection.",
    "rate_limited": "Google temporarily limited requests. Retry shortly.",
}


def connection_status(
    account: GoogleAccount | None, name: str, *, mock: bool, missing: set[str]
) -> tuple[str, str | None]:
    if not account:
        return "disconnected", None
    if name not in account.enabled:
        return "disabled", None
    if mock:
        return "mock", None
    code = account.connection_error or (account.connector_errors or {}).get(name)
    if code == "auth_required":
        return "expired", ERROR_MESSAGES[code]
    if missing:
        return (
            "needs_permission",
            "Grant the required Google permissions to enable these capabilities.",
        )
    if code:
        return "needs_permission" if code == "permission_denied" else "error", ERROR_MESSAGES.get(
            code, "Google connection needs attention. Reconnect or retry."
        )
    return "connected" if account.connection_checked_at else "authorized", None
