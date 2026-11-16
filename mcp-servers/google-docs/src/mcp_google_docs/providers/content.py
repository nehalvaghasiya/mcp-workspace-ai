from __future__ import annotations

from typing import Any

from mcp_workspace_common.errors import ConnectorError


def utf16_length(text: str) -> int:
    return len(text.encode("utf-16-le")) // 2


def document_body(
    document: dict[str, Any], tab_id: str | None
) -> tuple[dict[str, Any], str | None]:
    def walk(tabs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [item for tab in tabs for item in [tab, *walk(tab.get("childTabs", []))]]

    tabs = [tab for tab in walk(document.get("tabs", [])) if tab.get("documentTab")]
    for tab in tabs:
        current = tab.get("tabProperties", {}).get("tabId")
        if tab_id is None or current == tab_id:
            return dict(tab["documentTab"].get("body", {})), current
    if tab_id:
        raise ConnectorError("not_found", "The selected document tab is unavailable")
    return dict(document.get("body", {})), None


def document_text(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("textRun", {}).get("content", "")) + "".join(
            document_text(item) for key, item in value.items() if key != "textRun"
        )
    if isinstance(value, list):
        return "".join(document_text(item) for item in value)
    return ""


def text_requests(
    blocks: list[dict[str, Any]], index: int, tab_id: str | None
) -> list[dict[str, Any]]:
    parts: list[str] = []
    formats: list[dict[str, Any]] = []
    cursor = index
    for block in blocks:
        text = "\n".join(block["items"]) if block["type"] == "bullet_list" else block["text"]
        text += "\n"
        end = cursor + utf16_length(text)
        target = {"startIndex": cursor, "endIndex": end} | ({"tabId": tab_id} if tab_id else {})
        style = f"HEADING_{block['level']}" if block["type"] == "heading" else "NORMAL_TEXT"
        formats.append(
            {
                "updateParagraphStyle": {
                    "range": target,
                    "paragraphStyle": {"namedStyleType": style},
                    "fields": "namedStyleType",
                }
            }
        )
        if block["type"] == "bullet_list":
            formats.append(
                {
                    "createParagraphBullets": {
                        "range": target,
                        "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE",
                    }
                }
            )
        parts.append(text)
        cursor = end
    location = {"index": index} | ({"tabId": tab_id} if tab_id else {})
    return (
        [{"insertText": {"location": location, "text": "".join(parts)}}, *formats] if parts else []
    )


def table_values(block: dict[str, Any]) -> list[list[str]]:
    return [block["headers"], *block.get("rows", [])]
