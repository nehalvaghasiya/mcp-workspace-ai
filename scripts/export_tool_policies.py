"""Generate or check the policy projection without introducing another authority."""

import argparse
import json
from pathlib import Path

from mcp_workspace_api.mcp.registry import tool_definitions


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    path = Path(__file__).resolve().parents[1] / "config/tool-policies.yaml"
    projection = {
        "generated_from": "mcp_workspace_api.mcp.registry.tool_definitions",
        "tools": {
            name: {"risk": str(tool.risk), "scopes": list(tool.scopes), "digest": tool.digest}
            for name, tool in tool_definitions().items()
        },
    }
    if args.check:
        if json.loads(path.read_text()) != projection:
            print("Policy projection is stale; regenerate it with scripts/export_tool_policies.py")
            return 1
        print("Policy projection matches the typed registry")
    else:
        path.write_text(json.dumps(projection, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
