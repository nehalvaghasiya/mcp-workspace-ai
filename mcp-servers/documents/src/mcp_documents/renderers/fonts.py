"""Register licensed Unicode fonts from installed package resources."""

from __future__ import annotations

import threading
from contextlib import ExitStack
from importlib.resources import as_file, files

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from mcp_documents.exceptions.artifact_error import ArtifactError

_FONT_LOCK = threading.Lock()


def _pdf_fonts() -> tuple[str, str]:
    with _FONT_LOCK:
        if "WorkspaceSans" not in pdfmetrics.getRegisteredFontNames():
            bundled = files("mcp_documents").joinpath("assets", "fonts")
            regular = bundled.joinpath("DejaVuSans.ttf")
            bold = bundled.joinpath("DejaVuSans-Bold.ttf")
            if not regular.is_file() or not bold.is_file():
                fallback = files("reportlab").joinpath("fonts")
                regular, bold = fallback.joinpath("Vera.ttf"), fallback.joinpath("VeraBd.ttf")
            if not regular.is_file() or not bold.is_file():
                raise ArtifactError("A licensed Unicode PDF font is required")
            with ExitStack() as resources:
                regular_path = resources.enter_context(as_file(regular))
                bold_path = resources.enter_context(as_file(bold))
                pdfmetrics.registerFont(TTFont("WorkspaceSans", str(regular_path)))
                pdfmetrics.registerFont(TTFont("WorkspaceSansBold", str(bold_path)))
        return "WorkspaceSans", "WorkspaceSansBold"
