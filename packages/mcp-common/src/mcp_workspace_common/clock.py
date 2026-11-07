from datetime import UTC, datetime


def now() -> float:
    return datetime.now(UTC).timestamp()
