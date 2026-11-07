"""Run the existing guarded synthetic-fixture CLI command."""

import subprocess
import sys

if __name__ == "__main__":
    raise SystemExit(
        subprocess.call([sys.executable, "-m", "mcp_workspace_api.cli", "seed-demo", *sys.argv[1:]])
    )
