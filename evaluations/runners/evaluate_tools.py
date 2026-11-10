"""Evaluate the 26 preserved Gmail, Calendar and Drive routing cases."""

from mcp_workspace_evaluations.cli import main

if __name__ == "__main__":
    main({"gmail", "calendar", "drive"}, "tools")
