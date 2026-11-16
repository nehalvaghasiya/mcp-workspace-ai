from __future__ import annotations

from typing import Any

from mcp_google_docs.providers.content import document_text


def matches_document(document: dict[str, Any], blocks: list[dict[str, Any]]) -> bool:
    text = document_text(document)
    for block in blocks:
        if block["type"] == "table":
            expected = [*block["headers"], *(cell for row in block["rows"] for cell in row)]
        elif block["type"] == "bullet_list":
            expected = block["items"]
        else:
            expected = [block["text"]]
        if any(value and value not in text for value in expected):
            return False
    return True
