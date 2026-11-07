from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from docx import Document
from openpyxl import load_workbook
from pptx import Presentation
from pydantic import JsonValue
from pypdf import PdfReader
from pypdf.generic import DictionaryObject

from mcp_documents.constants import EXTENSIONS, MAX_ROWS, MAX_SLIDES, MIME_TYPES
from mcp_documents.exceptions.artifact_error import ArtifactError
from mcp_documents.utils.text import _normalize
from mcp_documents.validators.formulas import _safe_formula
from mcp_documents.validators.inspection import _Inspection
from mcp_documents.validators.office_package import check_package
from mcp_documents.validators.safe_html_parser import _SafeHTMLParser


def inspect_artifact(path: Path, format: str, max_bytes: int) -> _Inspection:
    if format not in MIME_TYPES:
        raise ArtifactError("Unsupported artifact format")
    if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
        raise ArtifactError("Artifact file must not be a symlink")
    if path.suffix != f".{EXTENSIONS[format]}":
        raise ArtifactError("Artifact extension does not match format")
    if not path.is_file() or not 0 < path.stat().st_size <= max_bytes:
        raise ArtifactError("Artifact is empty or exceeds the configured file limit")
    summary: dict[str, JsonValue] = {
        "valid": True,
        "format": format,
        "size": path.stat().st_size,
    }
    result = _Inspection(summary)
    if format in {"docx", "xlsx", "pptx"}:
        check_package(path, format)
        summary["zip_checked"] = True
    if format == "docx":
        document = Document(str(path))
        result.texts = [paragraph.text for paragraph in document.paragraphs]
        result.tables = [
            [[cell.text for cell in row.cells] for row in table.rows] for table in document.tables
        ]
        summary.update(
            paragraphs=len(document.paragraphs),
            tables=len(document.tables),
            title=document.core_properties.title,
        )
    elif format == "pdf":
        if not path.read_bytes().startswith(b"%PDF-"):
            raise ArtifactError("Invalid PDF signature")
        reader = PdfReader(str(path), strict=True)
        if reader.is_encrypted or not 0 < len(reader.pages) <= 200:
            raise ArtifactError("Encrypted or oversized PDF is unsupported")
        root = reader.trailer["/Root"]
        if not isinstance(root, DictionaryObject):
            raise ArtifactError("Invalid PDF document catalog")
        if any(key in root for key in ("/OpenAction", "/AA", "/AcroForm")):
            raise ArtifactError("Active PDF content is unsupported")
        # Our footer is drawn before each page's content. Exclude that known
        # prefix so a paragraph spanning pages remains contiguous in readback.
        result.texts = [
            (page.extract_text() or "").removeprefix(f"Page {index}\n")
            for index, page in enumerate(reader.pages, 1)
        ]
        summary.update(
            pages=len(reader.pages), title=reader.metadata.title if reader.metadata else ""
        )
    elif format == "xlsx":
        workbook = load_workbook(path, read_only=True, data_only=False, keep_links=False)
        try:
            if len(workbook.worksheets) > 10:
                raise ArtifactError("Too many worksheets")
            for sheet in workbook.worksheets:
                if sheet.max_row > MAX_ROWS + 1 or sheet.max_column > 50:
                    raise ArtifactError("Worksheet dimensions exceed limits")
                rows: list[list[str]] = []
                for row in sheet.iter_rows():
                    cells: list[str] = []
                    for cell in row:
                        value = cell.value
                        if cell.data_type == "f":
                            result.formulas.append(_safe_formula(str(value)))
                        if isinstance(value, datetime):
                            cells.append(value.date().isoformat())
                        elif isinstance(value, (int, float)):
                            cells.append(f"{value:.15g}")
                        else:
                            cells.append(str(value) if value is not None else "")
                    rows.append(cells)
                result.sheets.append(rows)
            summary.update(
                sheets=list(workbook.sheetnames),
                rows=[sheet.max_row for sheet in workbook.worksheets],
                formulas=len(result.formulas),
                formula_results="not_calculated",
            )
        finally:
            workbook.close()
    elif format == "pptx":
        presentation = Presentation(str(path))
        if not 0 < len(presentation.slides) <= MAX_SLIDES:
            raise ArtifactError("Presentation slide count exceeds limits")
        for slide in presentation.slides:
            for shape in slide.shapes:
                if shape.has_text_frame:
                    result.texts.extend(paragraph.text for paragraph in shape.text_frame.paragraphs)
                if shape.has_table:
                    result.tables.append(
                        [[cell.text for cell in row.cells] for row in shape.table.rows]
                    )
            if slide.has_notes_slide and slide.notes_slide.notes_text_frame is not None:
                result.notes.append(slide.notes_slide.notes_text_frame.text)
        summary.update(
            slides=len(presentation.slides),
            tables=len(result.tables),
            title=presentation.core_properties.title,
        )
    elif format == "csv":
        with path.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.reader(stream, strict=True))
        if not rows or len(rows) > MAX_ROWS + 1 or len(rows[0]) > 50:
            raise ArtifactError("CSV dimensions exceed limits")
        if any(len(row) != len(rows[0]) for row in rows):
            raise ArtifactError("CSV rows are not rectangular")
        if any(cell.lstrip().startswith(("=", "+", "-", "@")) for row in rows for cell in row):
            raise ArtifactError("CSV contains an unescaped formula prefix")
        result.sheets = [rows]
        summary.update(rows=len(rows), columns=len(rows[0]))
    elif format == "html":
        parser = _SafeHTMLParser()
        parser.feed(path.read_text(encoding="utf-8"))
        parser.close()
        result.texts = parser.texts
        summary["sanitized"] = True
    else:
        result.texts = [path.read_text(encoding="utf-8")]
        summary["encoding"] = "utf-8"
    if not any(_normalize(text) for text in result.texts) and not result.sheets:
        raise ArtifactError("Artifact contains no readable content")
    return result
