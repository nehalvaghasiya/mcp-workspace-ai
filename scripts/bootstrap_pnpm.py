"""Resolve the pinned pnpm executable, bootstrapping into ignored project tools."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def pnpm_executable(*, install: bool = False) -> Path:
    """Return an exact-version executable without changing global installations."""
    version = json.loads((ROOT / "package.json").read_text())["packageManager"].removeprefix(
        "pnpm@"
    )
    local = ROOT / ".local" / "tools" / "pnpm"
    candidates = [local / "node_modules" / ".bin" / "pnpm"]
    available = shutil.which("pnpm")
    if available:
        candidates.append(Path(available))
    for candidate in candidates:
        if candidate.is_file():
            # An outside-project cwd makes --version independent of workspace resolution.
            result = subprocess.run(
                [str(candidate), "--version"],
                cwd=ROOT.parent,
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            if result.returncode == 0 and result.stdout.strip() == version:
                return candidate.resolve()
    if not install:
        raise RuntimeError("Pinned pnpm is missing; run make setup first")
    npm = shutil.which("npm")
    if npm is None:
        raise RuntimeError("Install Node 24/npm to bootstrap the pinned pnpm")
    subprocess.run(
        [npm, "install", "--prefix", str(local), "--no-audit", "--no-fund", f"pnpm@{version}"],
        cwd=ROOT,
        check=True,
    )
    return pnpm_executable()


def main() -> None:
    print(pnpm_executable(install=True))


if __name__ == "__main__":
    main()
