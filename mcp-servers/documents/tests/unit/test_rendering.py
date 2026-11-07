from __future__ import annotations

import csv
import hashlib
from datetime import date
from pathlib import Path

import pytest
from docx import Document
from mcp_documents.artifacts import (
    ArtifactEngine,
    ArtifactSpec,
    FormulaCell,
)
from openpyxl import load_workbook
from pptx import Presentation
from pydantic import ValidationError
from pypdf import PdfReader

from tests.support.artifact_specs import report, spreadsheet


@pytest.mark.parametrize("format", ["docx", "pdf", "xlsx", "pptx", "csv", "markdown", "html"])
def test_every_format_is_real_and_semantically_valid(tmp_path: Path, format: str) -> None:
    engine = ArtifactEngine()
    rendered = engine.create(report(format), tmp_path / "user-a")
    assert rendered.path.parent == tmp_path / "user-a"
    assert rendered.path.name.split(".")[0].isalnum()
    assert rendered.size == rendered.path.stat().st_size
    assert rendered.sha256 == hashlib.sha256(rendered.path.read_bytes()).hexdigest()
    assert rendered.validation["semantic_readback"] is True
    assert engine.validate(rendered.path, format)["valid"] is True
    assert rendered.path.stat().st_mode & 0o777 == 0o600
    assert list(rendered.path.parent.glob(".render-*")) == []
    if format == "docx":
        document = Document(str(rendered.path))
        assert document.paragraphs[1].style.name == "Heading 1"
        assert document.tables[0].cell(1, 0).text == "Dependency"
        assert document.sections[0].footer.paragraphs[0].text
    elif format == "pdf":
        reader = PdfReader(rendered.path)
        assert "café" in reader.pages[0].extract_text()
        assert "€4200" in reader.pages[0].extract_text()
        assert reader.metadata.title == report(format).title
    elif format == "pptx":
        presentation = Presentation(str(rendered.path))
        assert len(presentation.slides) == 5
        assert any(shape.has_table for slide in presentation.slides for shape in slide.shapes)


def test_spreadsheet_types_formulas_and_literal_injection(tmp_path: Path) -> None:
    rendered = ArtifactEngine().create(spreadsheet(), tmp_path)
    workbook = load_workbook(rendered.path, data_only=False)
    try:
        sheet = workbook["Tracker"]
        assert sheet["A2"].value.startswith("=HYPERLINK")
        assert sheet["A2"].data_type == "s"
        assert sheet["A3"].data_type == "s"
        assert sheet["D3"].data_type == "s"
        assert sheet["B2"].value == 42.5
        assert sheet["C2"].value.date() == date(2026, 11, 5)
        assert sheet["D2"].value == "=SUM(B2:B3)"
        assert sheet["D2"].data_type == "f"
        assert sheet["A1"].font.bold
        assert sheet.freeze_panes == "A2"
        assert rendered.validation["formula_results"] == "not_calculated"
    finally:
        workbook.close()


@pytest.mark.parametrize(
    "value",
    [
        "=1+1",
        "+cmd|' /C calc'!A0",
        "-1+2",
        "@SUM(A1:A2)",
        "\t =1+1",
        "\n@BAD",
        'hello,"quoted"\nnext line',
    ],
)
def test_csv_quotes_and_formula_injection(tmp_path: Path, value: str) -> None:
    spec = ArtifactSpec.model_validate(
        {
            "format": "csv",
            "title": "Safe export",
            "sheets": [
                {
                    "name": "Export",
                    "columns": ["Value"],
                    "rows": [[{"type": "string", "value": value}]],
                }
            ],
        }
    )
    rendered = ArtifactEngine().create(spec, tmp_path)
    with rendered.path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.reader(stream))
    expected = "'" + value if value.lstrip().startswith(("=", "+", "-", "@")) else value
    assert rows == [["Value"], [expected]]


@pytest.mark.parametrize(
    "formula",
    [
        '=HYPERLINK("https://evil.invalid")',
        '=WEBSERVICE("https://evil.invalid")',
        "=cmd|' /C calc'!A0",
        "='[external.xlsx]Sheet'!A1",
        "=INDIRECT(A1)",
        "=NOW()",
        "=SUM(A1:A9999)",
        "=SUM(ZZ1:ZZ2)",
        "=SUM(A1",
        "=A1& B1",
        "=SUM(A1:A2);OTHER()",
        "=SUM()",
        "=1 2",
        "=SUM(A1::A2)",
        "=ROUND(A1)",
        "=ABS(A1,A2)",
        "=A1+",
        "=1**2",
    ],
)
def test_unsafe_formulas_are_rejected(formula: str) -> None:
    with pytest.raises(ValidationError):
        FormulaCell(type="formula", value=formula)


@pytest.mark.parametrize(
    "formula", ["=SUM(A2:A4)", "=ROUND(AVERAGE(B2:B4),2)", "=$A$1*2+MAX(B1:B9)", "=-ABS(A1)"]
)
def test_safe_local_formulas_are_accepted(formula: str) -> None:
    assert FormulaCell(type="formula", value=formula).value == formula


def test_explicit_slide_content_tables_and_notes(tmp_path: Path) -> None:
    spec = ArtifactSpec.model_validate(
        {
            "format": "pptx",
            "title": "Launch",
            "template": "presentation",
            "slides": [
                {
                    "title": "Decisions",
                    "body": "Launch approved",
                    "bullets": ["Review dependency"],
                    "tables": [
                        {
                            "type": "table",
                            "headers": ["Owner", "Task"],
                            "rows": [["Team A", "Release"]],
                        }
                    ],
                    "notes": "Synthetic speaker notes",
                },
                {"title": "Next steps", "body": "Confirm date"},
            ],
        }
    )
    rendered = ArtifactEngine().create(spec, tmp_path)
    presentation = Presentation(str(rendered.path))
    assert len(presentation.slides) == 2
    assert presentation.slides[0].notes_slide.notes_text_frame.text == "Synthetic speaker notes"


def test_html_is_escaped_by_construction_and_markdown_is_inert(tmp_path: Path) -> None:
    payload = '<script>alert("oops")</script><img src="http://169.254.169.254/" onerror="run()"> [link](javascript:run())'
    data = {
        "format": "html",
        "title": "Escaping",
        "blocks": [{"type": "paragraph", "text": payload}],
    }
    rendered = ArtifactEngine().create(ArtifactSpec.model_validate(data), tmp_path)
    content = rendered.path.read_text()
    assert "<script>" not in content and "<img " not in content
    assert "&lt;script&gt;" in content
    assert "Content-Security-Policy" in content
    data["format"] = "markdown"
    rendered = ArtifactEngine().create(ArtifactSpec.model_validate(data), tmp_path)
    assert "<script>" not in rendered.path.read_text()
    assert "[link](javascript:run())" not in rendered.path.read_text()


@pytest.mark.parametrize(
    "key,value",
    [
        ("path", "../../etc/passwd"),
        ("filename", "%2e%2e%2fpasswd"),
        ("image_url", "http://169.254.169.254/latest/meta-data"),
        ("template", "{{ unsafe() }}"),
    ],
)
def test_spec_cannot_select_paths_remote_resources_or_templates(key: str, value: str) -> None:
    data = {"format": "docx", "title": "Report", key: value}
    with pytest.raises(ValidationError):
        ArtifactSpec.model_validate(data)


def test_title_is_content_and_never_a_filename(tmp_path: Path) -> None:
    spec = ArtifactSpec(format="docx", title="../../etc/passwd")
    rendered = ArtifactEngine().create(spec, tmp_path)
    assert rendered.path.parent == tmp_path
    assert rendered.path.suffix == ".docx"
    assert Document(str(rendered.path)).paragraphs[0].text == "../../etc/passwd"
