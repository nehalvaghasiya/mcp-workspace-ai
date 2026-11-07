from __future__ import annotations

from enum import StrEnum


class Risk(StrEnum):
    READ = "READ"
    LOCAL_WRITE = "LOCAL_WRITE"
    ACCOUNT_WRITE = "ACCOUNT_WRITE"
    EXTERNAL_EFFECT = "EXTERNAL_EFFECT"
    DESTRUCTIVE = "DESTRUCTIVE"
