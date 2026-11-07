"""Run the authoritative locked dependency audits through their Make target."""

from __future__ import annotations

import subprocess
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    return subprocess.run(["make", "dependency-audit"], cwd=root, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
