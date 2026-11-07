from __future__ import annotations

import base64
import io
import re
import zipfile
from functools import lru_cache

from mcp_workspace_common.constants import DEMO_NOW
from mcp_workspace_common.extraction import PPTX, XLSX


@lru_cache(maxsize=3)
def _synthetic_binary(mime: str) -> str:
    """Real, deterministic native files; only synthetic content, no filesystem IO."""
    buffer = io.BytesIO()
    if mime == XLSX:
        from openpyxl import Workbook

        workbook = Workbook()
        workbook.properties.created = workbook.properties.modified = DEMO_NOW.replace(tzinfo=None)
        workbook.active.append(["Synthetic launch budget", 24000])
        workbook.save(buffer)
    elif mime == PPTX:
        from pptx import Presentation

        deck = Presentation()
        deck.core_properties.created = deck.core_properties.modified = DEMO_NOW.replace(tzinfo=None)
        slide = deck.slides.add_slide(deck.slide_layouts[0])
        slide.shapes.title.text = "Synthetic launch risk review"
        deck.save(buffer)
    else:
        from reportlab.pdfgen.canvas import Canvas

        canvas = Canvas(buffer, invariant=1)
        canvas.drawString(50, 750, "Synthetic launch: vendor delay, budget $24000")
        canvas.save()
    data = buffer.getvalue()
    if mime in {XLSX, PPTX}:
        # Office libraries include ZIP creation times; freeze them for manifest hashes.
        canonical = io.BytesIO()
        with zipfile.ZipFile(io.BytesIO(data)) as source, zipfile.ZipFile(canonical, "w") as target:
            for name in sorted(source.namelist()):
                body = source.read(name)
                if name == "docProps/core.xml":
                    body = re.sub(
                        rb"(<dcterms:modified[^>]*>)[^<]+", rb"\g<1>2026-11-05T18:00:00Z", body
                    )
                target.writestr(zipfile.ZipInfo(name, (2026, 11, 5, 18, 0, 0)), body)
        data = canonical.getvalue()
    return base64.urlsafe_b64encode(data).decode()
