from __future__ import annotations

import base64
import io
import zipfile

import pytest
from docx import Document
from mcp_workspace_common.extraction import (
    DOCX,
    PPTX,
    XLSX,
    ExtractionError,
    extract_text,
    html_to_text,
    parse_gmail_message,
)
from openpyxl import Workbook
from pptx import Presentation
from reportlab.pdfgen.canvas import Canvas


@pytest.mark.parametrize("mime", [DOCX, XLSX, PPTX, "application/pdf"])
def test_native_document_extraction(mime: str) -> None:
    buffer = io.BytesIO()
    if mime == DOCX:
        document = Document()
        document.add_heading("Synthetic launch", 0)
        document.add_paragraph("Budget is $24000")
        document.save(buffer)
    elif mime == XLSX:
        workbook = Workbook()
        workbook.active.append(["Synthetic launch", 24000])
        workbook.save(buffer)
    elif mime == PPTX:
        deck = Presentation()
        slide = deck.slides.add_slide(deck.slide_layouts[0])
        slide.shapes.title.text = "Synthetic launch"
        deck.save(buffer)
    else:
        canvas = Canvas(buffer)
        canvas.drawString(50, 750, "Synthetic launch")
        canvas.save()
    result = extract_text(buffer.getvalue(), mime)
    assert "Synthetic launch" in result["text"]
    assert result["untrusted"] and not result["truncated"]


def test_html_active_content_removed_no_url_fetch() -> None:
    assert (
        html_to_text(
            '<p>Safe</p><script>steal()</script><style>hidden</style><img src="http://169.254.169.254/">'
        )
        == "Safe"
    )
    assert extract_text(b"abcdef", "text/plain", 3)["text"] == "abc"
    assert extract_text(b"abcdef", "text/plain", 3)["truncated"]


def test_zip_bomb_and_mime_spoof_rejected() -> None:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("word/document.xml", "A" * 1000000)
    with pytest.raises(ExtractionError, match="Unsafe archive"):
        extract_text(buffer.getvalue(), DOCX)
    with pytest.raises(ExtractionError, match="does not match"):
        extract_text(b"not a pdf", "application/pdf")
    with pytest.raises(ExtractionError, match="Unsupported"):
        extract_text(b"binary", "application/octet-stream")


def test_xml_entity_expansion_rejected() -> None:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(
            "word/document.xml",
            '<!DOCTYPE doc [<!ENTITY ext SYSTEM "file:///etc/passwd">]><doc>&ext;</doc>',
        )
    with pytest.raises(ExtractionError, match="safely extracted"):
        extract_text(buffer.getvalue(), DOCX)


def test_gmail_multipart_html_and_attachment() -> None:
    def encode(value: str) -> str:
        return base64.urlsafe_b64encode(value.encode()).decode()

    message = {
        "id": "message-1",
        "threadId": "thread-1",
        "payload": {
            "mimeType": "multipart/mixed",
            "headers": [{"name": "Subject", "value": "Synthetic"}],
            "parts": [
                {
                    "mimeType": "text/html",
                    "body": {"data": encode("<p>Content</p><script>bad()</script>")},
                },
                {
                    "filename": "memo.pdf",
                    "mimeType": "application/pdf",
                    "body": {"size": 12, "attachmentId": "attachment-1"},
                },
            ],
        },
    }
    result = parse_gmail_message(message)
    assert result["text"] == "Content"
    assert result["attachments"][0]["attachment_id"] == "attachment-1"
    assert "bad()" not in str(result)
