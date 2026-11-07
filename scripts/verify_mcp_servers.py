"""Verify actual authenticated MCP discovery, workflow calls and four downloads."""

import argparse
import asyncio
import json
import os

from mcp_workspace_api.operations.smoke import smoke

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=os.environ.get("API_URL", "http://127.0.0.1:8000"))
    args = parser.parse_args()
    print(json.dumps(asyncio.run(smoke(args.url)), indent=2))
