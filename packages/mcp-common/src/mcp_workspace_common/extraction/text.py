from __future__ import annotations

import io
from typing import Any

from defusedxml import ElementTree

from mcp_workspace_common.errors import ExtractionError
from mcp_workspace_common.extraction.constants import (
    DOCX,
    MAX_EXPANDED_BYTES,
    MAX_FILE_BYTES,
    PPTX,
    SUPPORTED_MIMES,
    XLSX,
)

from .archive import _safe_zip
from .html_text import html_to_text


def extract_text(data: bytes, mime_type: str, max_chars: int = 20000) -> dict[str, Any]:
    """Extract plain text only; bounded input, archive expansion, pages and output."""
    if len(data) > MAX_FILE_BYTES:
        raise ExtractionError("File exceeds 10 MiB extraction limit")
    if mime_type not in SUPPORTED_MIMES:
        raise ExtractionError("Unsupported file MIME type")
    if not 1 <= max_chars <= 100000:
        raise ExtractionError("max_chars must be between 1 and 100000")
    parts: list[str] = []
    partial = False
    try:
        if mime_type in {DOCX, XLSX, PPTX}:
            with _safe_zip(data, mime_type) as archive:
                # Defused XML rejects entity expansion. Extract text nodes, never formulas,
                # macros, links, embedded objects or externally referenced resources.
                if mime_type == DOCX:
                    names = ["word/document.xml"]
                elif mime_type == PPTX:
                    names = sorted(
                        n
                        for n in archive.namelist()
                        if n.startswith("ppt/slides/slide") and n.endswith(".xml")
                    )
                else:
                    names = [n for n in archive.namelist() if n == "xl/sharedStrings.xml"]
                    names += sorted(
                        n
                        for n in archive.namelist()
                        if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")
                    )
                for name in names:
                    root = ElementTree.fromstring(archive.read(name))
                    parts.append(
                        " ".join(
                            node.text or ""
                            for node in root.iter()
                            if node.tag.rsplit("}", 1)[-1] in {"t", "v"}
                        )
                    )
                    if sum(map(len, parts)) > max_chars:
                        partial = True
                        break
        elif mime_type == "application/pdf":
            from pypdf import PdfReader, apply_configuration

            if not data.startswith(b"%PDF-"):
                raise ExtractionError("File content does not match MIME type")
            with apply_configuration(
                maximum_declared_stream_length=5 * 1024 * 1024,
                zlib_maximum_output_length=5 * 1024 * 1024,
                lzw_maximum_output_length=5 * 1024 * 1024,
                run_length_maximum_output_length=5 * 1024 * 1024,
                stream_decoding_work_maximum_length=MAX_EXPANDED_BYTES,
                page_tree_maximum_entries=1000,
                xform_maximum_invocations_per_extraction=100,
            ):
                reader = PdfReader(
                    io.BytesIO(data), strict=True, xref_stream_maximum_entries=100000
                )
                if reader.is_encrypted:
                    raise ExtractionError("Encrypted PDF is unsupported")
                partial = len(reader.pages) > 100
                for page in reader.pages[:100]:
                    contents = page.get_contents()
                    if contents is not None and len(contents.get_data()) > 5 * 1024 * 1024:
                        raise ExtractionError("PDF page exceeds extraction limit")
                    parts.append(page.extract_text() or "")
                    if sum(map(len, parts)) > max_chars:
                        partial = True
                        break
        else:
            value = data.decode("utf-8", errors="replace")
            if "\x00" in value:
                raise ExtractionError("Binary content does not match text MIME type")
            parts = [html_to_text(value) if mime_type == "text/html" else value]
    except ExtractionError:
        raise
    except Exception:
        # Third party parsers have many exception types; do not expose their input.
        raise ExtractionError("File could not be safely extracted") from None
    text = "\n".join(parts)
    return {
        "text": text[:max_chars],
        "truncated": partial or len(text) > max_chars,
        "mime_type": mime_type,
        "start_offset": 0,
        "end_offset": min(len(text), max_chars),
        "untrusted": True,
    }
