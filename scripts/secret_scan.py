"""Small tracked-source canary scan; dependency/AST scans run separately."""

import re
import sys
from pathlib import Path

PATTERNS = [
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"GOCSPX-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AIza[A-Za-z0-9_-]{30,}"),
    re.compile(r"sk-(?:proj-)?[A-Za-z0-9_-]{40,}"),
]
hits = []
for root in (
    Path("apps/api/src"),
    Path("apps/web/src"),
    Path("mcp-servers"),
    Path("packages"),
    Path("evaluations/src"),
    Path("docs"),
    Path("examples"),
):
    for path in root.rglob("*"):
        if "node_modules" in path.parts or "__pycache__" in path.parts:
            continue
        if path.is_file() and path.suffix in {".py", ".ts", ".tsx", ".md", ".json"}:
            content = path.read_text()
            if any(pattern.search(content) for pattern in PATTERNS):
                hits.append(str(path))
if hits:
    print("Potential secrets detected in:", ", ".join(hits))
    sys.exit(1)
print("Source secret-pattern scan passed (heuristic; not a credential audit).")
