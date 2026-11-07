from __future__ import annotations

import html

from mcp_documents.schemas.artifact_spec import ArtifactSpec
from mcp_documents.schemas.bullet_list import BulletList
from mcp_documents.schemas.heading import Heading
from mcp_documents.schemas.paragraph_block import ParagraphBlock


def _render_html(spec: ArtifactSpec) -> str:
    escape = html.escape
    parts = [
        '<!doctype html><html lang="en"><head><meta charset="utf-8">',
        '<meta http-equiv="Content-Security-Policy" content="default-src &#x27;none&#x27;; base-uri &#x27;none&#x27;; form-action &#x27;none&#x27;">',
        f"<title>{escape(spec.title)}</title></head><body><main><h1>{escape(spec.title)}</h1>",
    ]
    for block in spec.blocks:
        if isinstance(block, Heading):
            parts.append(f"<h{block.level + 1}>{escape(block.text)}</h{block.level + 1}>")
        elif isinstance(block, ParagraphBlock):
            parts.append(f"<p>{escape(block.text)}</p>")
        elif isinstance(block, BulletList):
            parts.append(
                "<ul>" + "".join(f"<li>{escape(item)}</li>" for item in block.items) + "</ul>"
            )
        else:
            parts.append(
                "<table><thead><tr>"
                + "".join(f"<th>{escape(text)}</th>" for text in block.headers)
                + "</tr></thead><tbody>"
            )
            parts.extend(
                "<tr>" + "".join(f"<td>{escape(text)}</td>" for text in row) + "</tr>"
                for row in block.rows
            )
            parts.append("</tbody></table>")
    return "".join(parts) + "</main></body></html>"
