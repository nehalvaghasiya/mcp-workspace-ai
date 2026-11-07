from __future__ import annotations

import zipfile
from pathlib import Path

import pytest
from docx import Document
from mcp_documents.artifacts import (
    MAX_ROWS,
    MAX_SLIDES,
    MAX_SPEC_BYTES,
    ArtifactEngine,
    ArtifactError,
    ArtifactSpec,
)
from pydantic import ValidationError

from tests.support.artifact_specs import report, spreadsheet


def test_symlink_directories_and_files_are_rejected(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real, target_is_directory=True)
    engine = ArtifactEngine()
    with pytest.raises(ArtifactError, match="symlink"):
        engine.create(report("docx"), link / "nested")
    rendered = engine.create(report("docx"), real)
    file_link = tmp_path / "linked.docx"
    file_link.symlink_to(rendered.path)
    with pytest.raises(ArtifactError, match="symlink"):
        engine.validate(file_link, "docx")


def test_limits_on_rows_slides_text_and_total_input() -> None:
    with pytest.raises(ValidationError):
        ArtifactSpec.model_validate(
            {
                "format": "csv",
                "title": "Huge",
                "sheets": [
                    {
                        "name": "Huge",
                        "columns": ["Value"],
                        "rows": [[{"type": "string", "value": "x"}]] * (MAX_ROWS + 1),
                    }
                ],
            }
        )
    with pytest.raises(ValidationError):
        ArtifactSpec.model_validate(
            {"format": "pptx", "title": "Huge", "slides": [{"title": "Slide"}] * (MAX_SLIDES + 1)}
        )
    with pytest.raises(ValidationError):
        ArtifactSpec.model_validate(
            {
                "format": "docx",
                "title": "Huge",
                "blocks": [{"type": "paragraph", "text": "x" * 10_001}],
            }
        )
    with pytest.raises(ValidationError, match="500000"):
        ArtifactSpec.model_validate(
            {
                "format": "docx",
                "title": "Huge",
                "blocks": [{"type": "paragraph", "text": "x" * 10_000}]
                * (MAX_SPEC_BYTES // 10_000),
            }
        )


def test_failure_and_size_limit_leave_no_published_or_temporary_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    engine = ArtifactEngine(max_bytes=20)
    with pytest.raises(ArtifactError, match="file limit"):
        engine.create(report("docx"), tmp_path)
    assert list(tmp_path.iterdir()) == []

    def incomplete_render(spec: ArtifactSpec, path: Path) -> None:
        Document().save(str(path))

    engine = ArtifactEngine()
    monkeypatch.setattr(engine, "_render", incomplete_render)
    with pytest.raises(ArtifactError):
        engine.create(report("docx"), tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_semantic_mismatch_is_never_published(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    engine = ArtifactEngine()

    def incorrect_render(spec: ArtifactSpec, path: Path) -> None:
        document = Document()
        document.add_paragraph("Wrong content")
        document.save(str(path))

    monkeypatch.setattr(engine, "_render", incorrect_render)
    with pytest.raises(ArtifactError, match="readback"):
        engine.create(report("docx"), tmp_path)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    "member,content",
    [
        ("../escape.xml", b"bad"),
        ("word/vbaProject.bin", b"macro"),
        ("word/embeddings/object.bin", b"embedded"),
        ("word/huge.bin", b"0" * 100_000),
        (
            "word/_rels/document.xml.rels",
            b'<Relationships><Relationship TargetMode="External" Target="https://evil.invalid"/></Relationships>',
        ),
    ],
)
def test_unsafe_zip_packages_rejected(tmp_path: Path, member: str, content: bytes) -> None:
    path = tmp_path / "unsafe.docx"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as package:
        package.writestr("[Content_Types].xml", b"<Types/>")
        package.writestr("word/document.xml", b"<document/>")
        package.writestr(member, content)
    with pytest.raises(ArtifactError):
        ArtifactEngine().validate(path, "docx")


def test_content_type_spoofing_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "spoof.pdf"
    path.write_text("not a PDF")
    with pytest.raises(ArtifactError, match="signature"):
        ArtifactEngine().validate(path, "pdf")
    rendered = ArtifactEngine().create(report("docx"), tmp_path)
    with pytest.raises(ArtifactError, match="extension"):
        ArtifactEngine().validate(rendered.path, "xlsx")


def test_pdf_multiple_pages_and_explicit_unsupported_unicode(tmp_path: Path) -> None:
    spec = ArtifactSpec.model_validate(
        {
            "format": "pdf",
            "title": "Multipage",
            "blocks": [{"type": "paragraph", "text": "Synthetic launch status. " * 100}] * 10,
        }
    )
    rendered = ArtifactEngine().create(spec, tmp_path)
    assert rendered.validation["pages"] > 1
    with pytest.raises(ArtifactError, match="Unicode"):
        ArtifactEngine().create(
            ArtifactSpec(format="pdf", title="Unsupported \U0010ffff"), tmp_path
        )
    assert len(list(tmp_path.iterdir())) == 1


def test_nested_mutation_is_revalidated_before_render(tmp_path: Path) -> None:
    spec = spreadsheet()
    spec.sheets[0].rows.extend(spec.sheets[0].rows * MAX_ROWS)
    with pytest.raises(ValidationError):
        ArtifactEngine().create(spec, tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_slide_layout_limits_reject_obvious_overflow() -> None:
    with pytest.raises(ValidationError, match="lines"):
        ArtifactSpec.model_validate(
            {
                "format": "pptx",
                "title": "Overflow",
                "slides": [{"title": "Many lines", "body": "line\n" * 25}],
            }
        )
    with pytest.raises(ValidationError, match="layout capacity"):
        ArtifactSpec.model_validate(
            {
                "format": "pptx",
                "title": "Overflow",
                "slides": [
                    {
                        "title": "Large table",
                        "tables": [
                            {
                                "type": "table",
                                "headers": ["A", "B", "C", "D", "E", "F"],
                                "rows": [["long text " * 8] * 6] * 8,
                            }
                        ],
                    }
                ],
            }
        )


def test_xlsx_multiple_sheets_and_duplicate_names(tmp_path: Path) -> None:
    spec = spreadsheet()
    another = spec.sheets[0].model_copy(deep=True)
    another.name = "Archive"
    spec.sheets.append(another)
    rendered = ArtifactEngine().create(spec, tmp_path)
    assert rendered.validation["sheets"] == ["Tracker", "Archive"]
    data = spec.model_dump(mode="json")
    data["sheets"][1]["name"] = "TRACKER"
    with pytest.raises(ValidationError, match="unique"):
        ArtifactSpec.model_validate(data)


def test_pdf_paragraph_spanning_pages_preserves_semantic_readback(tmp_path: Path) -> None:
    text = " ".join(f"Decision {number}: verify the source and owner." for number in range(150))
    spec = ArtifactSpec(
        format="pdf", title="Multipage brief", blocks=[{"type": "paragraph", "text": text}]
    )
    rendered = ArtifactEngine().create(spec, tmp_path)
    assert rendered.validation["pages"] > 1
    assert rendered.validation["semantic_readback"] is True
