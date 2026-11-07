from __future__ import annotations

from typing import Literal

ArtifactFormat = Literal["docx", "pdf", "xlsx", "pptx", "csv", "markdown", "html"]

Template = Literal["business_report", "meeting_summary", "analysis_sheet", "presentation", "simple"]

MIME_TYPES: dict[str, str] = {
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "pdf": "application/pdf",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "csv": "text/csv",
    "markdown": "text/markdown",
    "html": "text/html",
}

EXTENSIONS = {**{key: key for key in MIME_TYPES}, "markdown": "md"}

MAX_SPEC_BYTES = 500_000

MAX_FILE_BYTES = 10 * 1024 * 1024

MAX_ROWS = 1_000

MAX_SLIDES = 50

MAX_ZIP_MEMBERS = 2_000

MAX_EXPANDED_BYTES = 40 * 1024 * 1024
