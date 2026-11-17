from __future__ import annotations

from typing import Any


def presentation_text(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("textRun", {}).get("content", "")) + "".join(
            presentation_text(item) for key, item in value.items() if key != "textRun"
        )
    if isinstance(value, list):
        return "".join(presentation_text(item) for item in value)
    return ""


def shape_requests(
    page: str, identifier: str, text: str, x: int, y: int, width: int, height: int, font_size: int
) -> list[dict[str, Any]]:
    return [
        {
            "createShape": {
                "objectId": identifier,
                "shapeType": "TEXT_BOX",
                "elementProperties": {
                    "pageObjectId": page,
                    "size": {
                        "width": {"magnitude": width, "unit": "PT"},
                        "height": {"magnitude": height, "unit": "PT"},
                    },
                    "transform": {
                        "scaleX": 1,
                        "scaleY": 1,
                        "translateX": x,
                        "translateY": y,
                        "unit": "PT",
                    },
                },
            }
        },
        {"insertText": {"objectId": identifier, "text": text, "insertionIndex": 0}},
        {
            "updateTextStyle": {
                "objectId": identifier,
                "textRange": {"type": "ALL"},
                "style": {"fontSize": {"magnitude": font_size, "unit": "PT"}},
                "fields": "fontSize",
            }
        },
    ]


def slide_requests(
    slides: list[dict[str, Any]], prefix: str
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    requests: list[dict[str, Any]] = []
    notes: dict[str, str] = {}
    for offset, slide in enumerate(slides):
        page = f"{prefix}_{offset}"
        requests.append(
            {
                "createSlide": {
                    "objectId": page,
                    "slideLayoutReference": {"predefinedLayout": "BLANK"},
                }
            }
        )
        requests.extend(shape_requests(page, page + "_title", slide["title"], 30, 18, 660, 65, 24))
        content = "\n".join(
            part for part in [slide.get("body", ""), *slide.get("bullets", [])] if part
        )
        if content:
            requests.extend(
                shape_requests(
                    page,
                    page + "_body",
                    content,
                    35,
                    90,
                    650,
                    110 if slide.get("tables") else 270,
                    14,
                )
            )
            if slide.get("bullets"):
                start = len(slide.get("body", "").encode("utf-16-le")) // 2 + (
                    1 if slide.get("body") else 0
                )
                requests.append(
                    {
                        "createParagraphBullets": {
                            "objectId": page + "_body",
                            "textRange": {"type": "FROM_START_INDEX", "startIndex": start},
                            "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE",
                        }
                    }
                )
        for table_offset, table in enumerate(slide.get("tables", [])):
            object_id = page + f"_table_{table_offset}"
            values = [table["headers"], *table.get("rows", [])]
            requests.append(
                {
                    "createTable": {
                        "objectId": object_id,
                        "rows": len(values),
                        "columns": len(table["headers"]),
                        "elementProperties": {
                            "pageObjectId": page,
                            "size": {
                                "width": {"magnitude": 650, "unit": "PT"},
                                "height": {"magnitude": 160, "unit": "PT"},
                            },
                            "transform": {
                                "scaleX": 1,
                                "scaleY": 1,
                                "translateX": 35,
                                "translateY": 210,
                                "unit": "PT",
                            },
                        },
                    }
                }
            )
            for row_number, row in enumerate(values):
                for column, text in enumerate(row):
                    if text:
                        requests.append(
                            {
                                "insertText": {
                                    "objectId": object_id,
                                    "cellLocation": {"rowIndex": row_number, "columnIndex": column},
                                    "text": text,
                                    "insertionIndex": 0,
                                }
                            }
                        )
        if slide.get("notes"):
            notes[page] = slide["notes"]
    return requests, notes
