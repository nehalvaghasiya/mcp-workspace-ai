from __future__ import annotations

import io
import zipfile

from mcp_workspace_common.errors import ExtractionError
from mcp_workspace_common.extraction.constants import (
    DOCX,
    MAX_EXPANDED_BYTES,
    PPTX,
    XLSX,
)


def _safe_zip(data: bytes, mime_type: str) -> zipfile.ZipFile:
    archive = zipfile.ZipFile(io.BytesIO(data))
    infos = archive.infolist()
    if len(infos) > 2000 or sum(i.file_size for i in infos) > MAX_EXPANDED_BYTES:
        archive.close()
        raise ExtractionError("Archive exceeds extraction limits")
    for item in infos:
        if (
            item.flag_bits & 1
            or item.file_size > 5 * 1024 * 1024
            or item.file_size > max(1, item.compress_size) * 200
            or item.filename.startswith("/")
            or ".." in item.filename.split("/")
            or "vbaproject" in item.filename.lower()
        ):
            archive.close()
            raise ExtractionError("Unsafe archive content")
    expected = {DOCX: "word/document.xml", XLSX: "xl/workbook.xml", PPTX: "ppt/presentation.xml"}[
        mime_type
    ]
    if expected not in archive.namelist():
        archive.close()
        raise ExtractionError("File content does not match MIME type")
    return archive
