from __future__ import annotations

from pathlib import Path

from pydantic import JsonValue

from mcp_documents.constants import ArtifactFormat
from mcp_documents.schemas.strict_model import StrictModel


class RenderedArtifact(StrictModel):
    path: Path
    format: ArtifactFormat
    mime_type: str
    size: int
    sha256: str
    validation: dict[str, JsonValue]
