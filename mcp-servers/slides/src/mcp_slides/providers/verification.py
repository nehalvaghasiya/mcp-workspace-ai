from __future__ import annotations

import re
from typing import Any

from mcp_workspace_common.errors import ConnectorError

from mcp_slides.providers.content import presentation_text


def matches_presentation(presentation: dict[str, Any], slides: list[dict[str, Any]]) -> bool:
    pages = presentation.get("slides", [])
    remaining = list(pages)
    for expected in slides:
        values = [expected["title"], expected.get("body", ""), *expected.get("bullets", [])]
        for table in expected.get("tables", []):
            values.extend([*table["headers"], *(cell for row in table["rows"] for cell in row)])
        if expected.get("notes"):
            values.append(expected["notes"])
        match = next(
            (
                page
                for page in remaining
                if all(not value or value in presentation_text(page) for value in values)
            ),
            None,
        )
        if match is None:
            return False
        remaining.remove(match)
    return True


def text_targets(presentation: dict[str, Any]) -> dict[str, tuple[str, str]]:
    targets: dict[str, tuple[str, str]] = {}
    for slide in presentation.get("slides", []):
        page = slide["objectId"]
        for element in slide.get("pageElements", []):
            if "shape" in element:
                targets[element["objectId"]] = (
                    page,
                    presentation_text(element["shape"]).rstrip("\n"),
                )
            if "table" in element:
                for row_index, row in enumerate(element["table"].get("tableRows", [])):
                    for column, cell in enumerate(row.get("tableCells", [])):
                        key = f"{element['objectId']}:{row_index}:{column}"
                        targets[key] = (page, presentation_text(cell).rstrip("\n"))
    return targets


def expected_edits(presentation: dict[str, Any], args: dict[str, Any]) -> dict[str, str]:
    targets = text_targets(presentation)
    changed: dict[str, str] = {}
    deleted = set(args["delete_slide_ids"])
    for replacement in args["replace_text"]:
        pages = set(replacement["slide_ids"])
        pattern = re.compile(
            re.escape(replacement["find"]), 0 if replacement["match_case"] else re.IGNORECASE
        )
        matched = False
        for key, (page, text) in list(targets.items()):
            if pages and page not in pages:
                continue
            replacement_text: str = replacement["replacement"]
            updated, count = pattern.subn(replacement_text.replace("\\", "\\\\"), text)
            if count:
                matched = True
                targets[key] = (page, updated)
                if page not in deleted:
                    changed[key] = updated.rstrip("\n")
        if not matched:
            raise ConnectorError(
                "not_found", "The requested text was not found on the selected slides"
            )
    for update in args["shape_text"]:
        page, _ = targets[update["object_id"]]
        if page in deleted:
            raise ConnectorError(
                "invalid_input", "A slide cannot be edited and removed in the same action"
            )
        changed[update["object_id"]] = update["text"].rstrip("\n")
    return changed


def verify_edits(
    presentation: dict[str, Any], expected: dict[str, str], deleted: list[str]
) -> bool:
    current = text_targets(presentation)
    if any(key not in current or current[key][1] != value for key, value in expected.items()):
        return False
    return not set(deleted) & {slide["objectId"] for slide in presentation.get("slides", [])}
