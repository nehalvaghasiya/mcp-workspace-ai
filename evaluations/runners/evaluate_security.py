"""Evaluate ten approval/ambiguity cases; adversarial pytest results stay separate."""

from mcp_workspace_evaluations.cli import main

if __name__ == "__main__":
    main({"approvals", "impossible"}, "security")
