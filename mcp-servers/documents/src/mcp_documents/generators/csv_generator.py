from __future__ import annotations

import csv
from pathlib import Path

from mcp_documents.schemas.artifact_spec import ArtifactSpec
from mcp_documents.utils.conversion import _cell_text, _sheets
from mcp_documents.utils.text import _csv_literal


def _render_csv(spec: ArtifactSpec, path: Path) -> None:
    sheet = _sheets(spec)[0]
    rows = [sheet.columns, *[[_cell_text(cell) for cell in row] for row in sheet.rows]]
    with path.open("w", encoding="utf-8", newline="") as stream:
        csv.writer(stream).writerows([[_csv_literal(cell) for cell in row] for row in rows])
