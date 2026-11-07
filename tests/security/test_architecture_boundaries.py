"""Architecture checks reject ownership violations, including lazy imports."""

import pytest

from scripts.check_architecture import ROOT, violations


def test_nested_classes_do_not_bypass_one_class_per_file() -> None:
    issues = violations(
        ROOT / "tests/example.py", "class First:\n    class Nested:\n        pass\n"
    )
    assert any("one class per file" in issue for issue in issues)


@pytest.mark.parametrize(
    "owner, target",
    [("gmail", "mcp_workspace_api"), ("calendar", "mcp_drive"), ("drive", "mcp_documents")],
)
def test_server_packages_cannot_import_upstream_or_siblings(owner: str, target: str) -> None:
    path = ROOT / f"mcp-servers/{owner}/src/example.py"
    assert violations(path, f"def delayed():\n    import {target}\n")


def test_common_package_cannot_import_servers() -> None:
    assert violations(ROOT / "packages/mcp-common/src/example.py", "from mcp_demo import server\n")
