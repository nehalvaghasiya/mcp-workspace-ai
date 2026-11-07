from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4


def uid() -> str:
    return uuid4().hex


def now() -> float:
    return datetime.now(UTC).timestamp()
