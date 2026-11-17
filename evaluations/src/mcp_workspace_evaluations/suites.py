"""Named subsets share the authoritative packaged datasets and runner."""

SUITES: dict[str, set[str] | None] = {
    "all": None,
    "tools": {"gmail", "calendar", "drive"},
    "workflows": {"cross_app"},
    "artifacts": {"artifacts"},
    "security": {"approvals", "impossible"},
}
