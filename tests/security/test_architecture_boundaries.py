"""Architecture checks reject ownership violations, including lazy imports."""

from pathlib import Path

import pytest

from scripts.check_architecture import ROOT, documentation_errors, violations


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


def test_documentation_check_catches_missing_files_and_allows_urls_and_anchors(
    tmp_path: Path,
) -> None:
    (tmp_path / "README.md").write_text(
        "[Missing](docs/missing.md) [Web](https://example.com) [Here](#here) "
        "[Raw file](README.md?raw=true#here)"
    )
    issues = documentation_errors(tmp_path)
    assert len(issues) == 1 and "docs/missing.md" in issues[0]
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/missing.md").write_text("# Present")
    assert documentation_errors(tmp_path) == []
