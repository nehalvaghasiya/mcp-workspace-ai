from __future__ import annotations

from mcp_documents.schemas.artifact_spec import ArtifactSpec
from mcp_documents.schemas.bullet_list import BulletList
from mcp_documents.schemas.heading import Heading
from mcp_documents.schemas.paragraph_block import ParagraphBlock
from mcp_documents.utils.text import _markdown_text


def _render_markdown(spec: ArtifactSpec) -> str:
    lines = ["# " + _markdown_text(spec.title), ""]
    for block in spec.blocks:
        if isinstance(block, Heading):
            lines.append("#" * (block.level + 1) + " " + _markdown_text(block.text))
        elif isinstance(block, ParagraphBlock):
            lines.append(_markdown_text(block.text))
        elif isinstance(block, BulletList):
            lines.extend("- " + _markdown_text(item) for item in block.items)
        else:
            lines.append("| " + " | ".join(map(_markdown_text, block.headers)) + " |")
            lines.append("| " + " | ".join("---" for _ in block.headers) + " |")
            lines.extend("| " + " | ".join(map(_markdown_text, row)) + " |" for row in block.rows)
        lines.append("")
    return "\n".join(lines)
