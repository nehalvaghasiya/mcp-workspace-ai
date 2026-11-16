"""Recognize explicit local conversion of content already in the conversation."""

import re
from typing import Any


def artifact_followup_format(prompt: str, history: list[dict[str, Any]]) -> str | None:
    text = prompt.lower()
    if not any(row.get("role") == "assistant" and row.get("content") for row in history):
        return None
    if not re.search(r"\b(create|generate|make|export|convert|turn)\b", text):
        return None
    if not re.search(
        r"\b(from (this|these|the above)|turn (this|these)|same (report|brief)|these findings)\b",
        text,
    ):
        return None
    if re.search(
        r"\b(read|search|check|find|review|google docs?|google sheets?|google slides?)\b", text
    ):
        return None
    formats = {
        "pdf": r"\bpdf\b",
        "docx": r"\b(word|docx)\b",
        "xlsx": r"\b(excel|xlsx)\b",
        "pptx": r"\b(powerpoint|pptx)\b",
        "csv": r"\bcsv\b",
        "markdown": r"\bmarkdown\b",
        "html": r"\bhtml\b",
    }
    selected = [name for name, pattern in formats.items() if re.search(pattern, text)]
    return selected[0] if len(selected) == 1 else None
