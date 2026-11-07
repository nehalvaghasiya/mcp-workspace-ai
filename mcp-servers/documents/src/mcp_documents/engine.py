from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path
from uuid import uuid4

from pydantic import JsonValue

from mcp_documents.constants import EXTENSIONS, MAX_FILE_BYTES, MIME_TYPES
from mcp_documents.exceptions.artifact_error import ArtifactError
from mcp_documents.renderers.dispatch import render_artifact
from mcp_documents.schemas.artifact_spec import ArtifactSpec
from mcp_documents.schemas.rendered_artifact import RenderedArtifact
from mcp_documents.validators.inspection import _Inspection
from mcp_documents.validators.inspector import inspect_artifact
from mcp_documents.validators.office_package import check_package
from mcp_documents.validators.semantics import verify_semantics


class ArtifactEngine:
    def __init__(self, *, max_bytes: int = MAX_FILE_BYTES) -> None:
        if not 1 <= max_bytes <= 100 * 1024 * 1024:
            raise ValueError("Invalid artifact file limit")
        self.max_bytes = max_bytes

    def create(self, spec: ArtifactSpec, directory: Path) -> RenderedArtifact:
        # Revalidate even models mutated through nested mutable lists/dictionaries.
        spec = ArtifactSpec.model_validate(spec.model_dump(mode="json"))
        directory = Path(directory).absolute()
        if any(part.is_symlink() for part in (directory, *directory.parents)):
            raise ArtifactError("Artifact directory must not contain symlinks")
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        artifact_id = uuid4().hex
        destination = directory / f"{artifact_id}.{EXTENSIONS[spec.format]}"
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=".render-", suffix=f".{EXTENSIONS[spec.format]}", dir=directory
        )
        os.close(descriptor)
        temporary = Path(temporary_name)
        try:
            self._render(spec, temporary)
            inspection = self._inspect(temporary, spec.format)
            self._verify_semantics(spec, inspection)
            inspection.summary["semantic_readback"] = True
            size = temporary.stat().st_size
            checksum = hashlib.sha256(temporary.read_bytes()).hexdigest()
            os.chmod(temporary, 0o600)
            with temporary.open("rb") as stream:
                os.fsync(stream.fileno())
            temporary.replace(destination)
            return RenderedArtifact(
                path=destination,
                format=spec.format,
                mime_type=MIME_TYPES[spec.format],
                size=size,
                sha256=checksum,
                validation=inspection.summary,
            )
        finally:
            temporary.unlink(missing_ok=True)

    def validate(self, path: Path, format: str) -> dict[str, JsonValue]:
        return self._inspect(path, format).summary

    def _inspect(self, path: Path, format: str) -> _Inspection:
        return inspect_artifact(path, format, self.max_bytes)

    _check_package = staticmethod(check_package)
    _verify_semantics = staticmethod(verify_semantics)

    def _render(self, spec: ArtifactSpec, path: Path) -> None:
        render_artifact(spec, path)
