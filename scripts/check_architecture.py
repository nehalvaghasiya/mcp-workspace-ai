"""Check handwritten class ownership, dependency direction and module size."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOTS = [
    "apps/api",
    "mcp-servers",
    "packages/mcp-common",
    "evaluations/src",
    "evaluations/runners",
    "tests",
    "scripts",
    "examples",
]
SERVER_MODULES = {
    "gmail": "mcp_gmail",
    "calendar": "mcp_calendar",
    "drive": "mcp_drive",
    "documents": "mcp_documents",
    "demo": "mcp_demo",
}


def violations(path: Path, source: str) -> list[str]:
    tree = ast.parse(source)
    relative = path.relative_to(ROOT).as_posix()
    errors = []
    classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    if len(classes) > 1:
        errors.append(f"{relative}: {len(classes)} classes; use one class per file")
    if len(source.splitlines()) > 400 and "/migrations/versions/" not in relative:
        errors.append(f"{relative}: exceeds the 400-line review limit")
    own = next(
        (
            module
            for name, module in SERVER_MODULES.items()
            if relative.startswith(f"mcp-servers/{name}/src/")
        ),
        None,
    )
    common = relative.startswith("packages/mcp-common/src/")
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
        elif isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "import_module"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        ):
            imports.append(node.args[0].value)
    for imported in imports:
        module = imported.split(".")[0]
        if module == "workspace_ai":
            errors.append(f"{relative}: obsolete workspace_ai import")
        if (own or common) and module == "mcp_workspace_api":
            errors.append(f"{relative}: lower-level package imports API")
        if module in SERVER_MODULES.values() and (common or own and module != own):
            errors.append(f"{relative}: forbidden cross-package import {module}")
    return errors


def main() -> int:
    errors = []
    files = [
        path
        for root in SOURCE_ROOTS
        for path in (ROOT / root).rglob("*.py")
        if not any(part in {"__pycache__", "dist", ".venv"} for part in path.parts)
    ]
    files.append(ROOT / "conftest.py")
    for path in files:
        errors.extend(violations(path, path.read_text()))
    if errors:
        print("\n".join(errors))
        return 1
    print(f"Architecture checks passed for {len(files)} Python modules")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
