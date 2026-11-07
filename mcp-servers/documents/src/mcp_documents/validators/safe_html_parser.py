from __future__ import annotations

from html.parser import HTMLParser

from mcp_documents.exceptions.artifact_error import ArtifactError


class _SafeHTMLParser(HTMLParser):
    allowed = {
        "html",
        "head",
        "meta",
        "title",
        "body",
        "main",
        "h1",
        "h2",
        "h3",
        "h4",
        "p",
        "ul",
        "li",
        "table",
        "thead",
        "tbody",
        "tr",
        "th",
        "td",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.texts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag not in self.allowed:
            raise ArtifactError("HTML contains an unsupported element")
        permitted = (
            {"lang"}
            if tag == "html"
            else {"charset", "http-equiv", "content"}
            if tag == "meta"
            else set()
        )
        if any(key not in permitted for key, _ in attrs):
            raise ArtifactError("HTML contains an unsupported attribute")

    def handle_data(self, data: str) -> None:
        self.texts.append(data)
