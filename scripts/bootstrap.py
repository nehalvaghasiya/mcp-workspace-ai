"""Report the installed local workspace tools after make setup."""

import json
import platform
from importlib.metadata import version

from bootstrap_pnpm import pnpm_executable
from mcp_workspace_api.mcp.registry import tool_definitions

if __name__ == "__main__":
    print(
        json.dumps(
            {
                "python": platform.python_version(),
                "mcp": version("mcp"),
                "pnpm": str(pnpm_executable()),
                "registered_tools": len(tool_definitions()),
            }
        )
    )
