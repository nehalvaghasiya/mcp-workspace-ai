from __future__ import annotations

import re
import unicodedata


def _plain_text(value: str) -> str:
    if any(
        (ord(char) < 32 and char not in "\n\r\t")
        or 0xD800 <= ord(char) <= 0xDFFF
        or ord(char) in (0xFFFE, 0xFFFF)
        for char in value
    ):
        raise ValueError("Unsupported control character in text")
    return value


def _csv_literal(value: str) -> str:
    # Leading whitespace/control characters do not bypass spreadsheet import rules.
    return "'" + value if value.lstrip().startswith(("=", "+", "-", "@")) else value


def _normalize(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).split())


def _markdown_text(value: str) -> str:
    return (
        re.sub(r"([\\`*_{}\[\]()#+.!|<>-])", r"\\\1", value).replace("\n", " ").replace("\r", " ")
    )
