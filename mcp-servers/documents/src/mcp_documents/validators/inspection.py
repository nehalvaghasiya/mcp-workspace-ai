from __future__ import annotations

from dataclasses import dataclass, field

from pydantic import JsonValue


@dataclass
class _Inspection:
    summary: dict[str, JsonValue]
    texts: list[str] = field(default_factory=list)
    tables: list[list[list[str]]] = field(default_factory=list)
    sheets: list[list[list[str]]] = field(default_factory=list)
    formulas: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
