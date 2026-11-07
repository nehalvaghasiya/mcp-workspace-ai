from __future__ import annotations

from html.parser import HTMLParser

from mcp_workspace_common.extraction.constants import (
    MAX_FILE_BYTES,
)


class _HTMLText(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.hidden = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "iframe", "object", "svg"}:
            self.hidden += 1
        if tag in {"p", "br", "div", "li", "tr"} and not self.hidden:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "iframe", "object", "svg"}:
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, data: str) -> None:
        if not self.hidden:
            self.parts.append(data)


def html_to_text(value: str) -> str:
    parser = _HTMLText()
    parser.feed(value[:MAX_FILE_BYTES])
    return "".join(parser.parts).strip()
