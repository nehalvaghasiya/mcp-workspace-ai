from __future__ import annotations

from typing import Any

from mcp_workspace_common.errors import ConnectorError


def _page(items: list[dict[str, Any]], args: dict[str, Any], key: str = "items") -> dict[str, Any]:
    limit = int(args.get("max_results", 20))
    if not 1 <= limit <= 100:
        raise ConnectorError("invalid_input", "max_results must be between 1 and 100")
    token = str(args.get("page_token") or "0")
    if not token.isdigit() or len(token) > 6:
        raise ConnectorError("invalid_input", "Invalid page token")
    offset = int(token)
    return {
        key: items[offset : offset + limit],
        "next_page_token": str(offset + limit) if offset + limit < len(items) else None,
        "result_count": len(items[offset : offset + limit]),
    }


def _source(provider: str, item: dict[str, Any], synthetic: bool = False) -> dict[str, Any]:
    rid = item.get("id", "")
    title = item.get("subject") or item.get("summary") or item.get("name") or rid
    urls = {
        "gmail": f"https://mail.google.com/mail/u/0/#all/{rid}",
        "calendar": item.get("htmlLink"),
        "drive": item.get("webViewLink"),
    }
    return {
        "provider": provider,
        "resource_id": rid,
        "title": title,
        "url": f"/api/sources/{provider}/{rid}" if synthetic else urls.get(provider),
        "snippet": str(item.get("snippet") or item.get("description") or "")[:500],
        "synthetic": synthetic,
        "untrusted": True,
    }
