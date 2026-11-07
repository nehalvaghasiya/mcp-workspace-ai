from __future__ import annotations

from mcp_documents.artifacts import (
    ArtifactSpec,
)


def report(format: str) -> ArtifactSpec:
    return ArtifactSpec.model_validate(
        {
            "format": format,
            "title": "Quarterly café report",
            "template": "business_report",
            "metadata": {"author": "Synthetic Team", "language": "en-US"},
            "blocks": [
                {"type": "heading", "level": 1, "text": "Decisions"},
                {"type": "paragraph", "text": "Launch approved. Budget €4200; résumé reviewed."},
                {"type": "bullet_list", "items": ["Confirm owner", "Review deadline"]},
                {
                    "type": "table",
                    "headers": ["Risk", "Owner"],
                    "rows": [["Dependency", "Team A"], ["Schedule", "Team B"]],
                },
            ],
        }
    )


def spreadsheet(format: str = "xlsx") -> ArtifactSpec:
    return ArtifactSpec.model_validate(
        {
            "format": format,
            "title": "Budget tracker",
            "sheets": [
                {
                    "name": "Tracker",
                    "columns": ["Task", "Cost", "Due", "Total"],
                    "rows": [
                        [
                            {"type": "string", "value": '=HYPERLINK("https://evil.invalid")'},
                            {"type": "number", "value": 42.5},
                            {"type": "date", "value": "2026-11-05"},
                            {"type": "formula", "value": "=SUM(B2:B3)"},
                        ],
                        [
                            {"type": "string", "value": "+cmd|' /C calculator'!A0"},
                            {"type": "number", "value": -12},
                            {"type": "date", "value": "2026-11-06"},
                            {"type": "string", "value": "@SUM(B2:B3)"},
                        ],
                    ],
                }
            ],
        }
    )
