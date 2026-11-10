from __future__ import annotations


class WorkspaceBackupError(ValueError):
    """Safe offline backup/restore failure without credential or key details."""
