"""Verify all workspace wheels in a fresh, noneditable environment outside the checkout."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from datetime import UTC, datetime
from email.parser import Parser
from pathlib import Path
from typing import Any

from workspace_contracts import current_contracts

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = {
    "mcp-workspace-api": "mcp_workspace_api",
    "mcp-workspace-calendar": "mcp_calendar",
    "mcp-workspace-common": "mcp_workspace_common",
    "mcp-workspace-demo": "mcp_demo",
    "mcp-workspace-documents": "mcp_documents",
    "mcp-workspace-drive": "mcp_drive",
    "mcp-workspace-evaluations": "mcp_workspace_evaluations",
    "mcp-workspace-gmail": "mcp_gmail",
    "mcp-workspace-google-docs": "mcp_google_docs",
    "mcp-workspace-sheets": "mcp_sheets",
    "mcp-workspace-slides": "mcp_slides",
}

# The probe is copied into its foreign working directory, rather than importing
# verification helpers from the checkout or putting repository paths on sys.path.
PROBE = r"""
from __future__ import annotations
import asyncio
import hashlib
import importlib
import json
import os
import sys
from importlib.metadata import version
from importlib.resources import files
from pathlib import Path


def require(condition, message):
    if not condition:
        raise AssertionError(message)


async def stdio_probe(runtime, user_id):
    from mcp import Client, StdioServerParameters
    token = runtime.signer.issue(
        {"user_id": user_id, "server": "demo", "tools": ["demo.ping"]}, ttl=120
    )
    parameters = StdioServerParameters(
        command=sys.executable,
        args=["-m", "mcp_workspace_api.cli", "mcp", "demo", "--transport", "stdio"],
        env={**os.environ, "WORKSPACE_MCP_TOKEN": token},
        cwd=Path.cwd(),
    )
    async with Client(parameters, read_timeout_seconds=15) as client:
        require(client.protocol_version == "2026-07-28", "Unexpected stdio protocol")
        names = [tool.name for tool in (await client.list_tools()).tools]
        require(names == ["demo.ping"], "Unexpected stdio tool catalog")
        result = await client.call_tool("demo.ping", {"request": {}})
        require(not result.is_error, "Installed stdio server rejected Demo call")
        require((result.structured_content or {}).get("status") == "success", "Demo failed")
    return {"status": "PASS", "protocol": "2026-07-28", "tools": names}


def probe(expected):
    prefix = Path(sys.prefix).resolve()
    repository = Path(expected["repository"]).resolve()
    require(not Path.cwd().is_relative_to(repository), "Probe cwd is inside checkout")
    require("PYTHONPATH" not in os.environ, "PYTHONPATH was inherited")
    locations = {}
    for distribution, namespace in expected["packages"].items():
        module = importlib.import_module(namespace)
        path = Path(module.__file__).resolve()
        require(path.is_relative_to(prefix), "Module outside fresh venv: " + namespace)
        require(not path.is_relative_to(repository), "Editable checkout import: " + namespace)
        locations[namespace] = str(path.relative_to(prefix))
        require(version(distribution) == expected["versions"][distribution], "Version mismatch")

    from mcp_workspace_api.main import create_app
    from mcp_workspace_api.core.config import Settings
    from mcp_workspace_api.db import Base
    from mcp_workspace_api.mcp.registry import tool_definitions
    from mcp_workspace_common.mock.fixtures import synthetic_workspace
    from mcp_workspace_evaluations.case_loader import cases
    from mcp_documents.artifacts import ArtifactEngine, ArtifactSpec
    from mcp_documents.resources.templates import template_catalog
    from fastapi.testclient import TestClient
    from sqlalchemy import inspect, text

    registry = tool_definitions()
    live_registry = tool_definitions("live")
    require("demo.ping" not in live_registry, "Demo tool leaked into live catalog")
    require({name: definition.digest for name, definition in live_registry.items()} == expected["live_policy_digests"], "Installed live tool definitions changed")
    require(len(registry) == 31, "Expected 31 installed tool definitions")
    require(
        {name: definition.digest for name, definition in registry.items()}
        == expected["policy_digests"],
        "Installed policy/schema digests differ from baseline",
    )
    mock_resources = files("mcp_workspace_common.mock").joinpath("assets")
    fixture = mock_resources.joinpath("workspace.json").read_bytes()
    require(hashlib.sha256(fixture).hexdigest() == expected["fixture_sha256"], "Fixture differs")
    require(synthetic_workspace() == json.loads(fixture), "Installed mock loader differs")
    require(
        hashlib.sha256(mock_resources.joinpath("manifest.json").read_bytes()).hexdigest()
        == expected["manifest_sha256"],
        "Installed fixture manifest differs",
    )
    packaged_cases = cases()
    require(len(packaged_cases) == 52, "Expected 52 installed evaluation cases")
    require(packaged_cases == expected["cases"], "Installed case IDs/assertions changed")

    migrations = files("mcp_workspace_api.db").joinpath("migrations")
    require(migrations.joinpath("env.py").is_file(), "Missing Alembic environment")
    require(migrations.joinpath("script.py.mako").is_file(), "Missing Alembic template")
    revision_names = [
        "0001_initial_owned_workspace_schema.py", "0002_credential_key_version.py",
        "0003_native_workspace_files.py", "0004_google_connection_status.py"
    ]
    for name in revision_names:
        require(migrations.joinpath("versions", name).is_file(), "Missing migration: " + name)

    settings = Settings(_env_file=None, mode="mock", llm_provider="fake",
                        data_dir=Path(os.environ["DATA_DIR"]))
    app = create_app(settings)
    require(app.openapi() == expected["openapi"], "Installed OpenAPI differs from baseline")
    with TestClient(app) as client:
        require(client.get("/api/health").status_code == 200, "Installed health failed")
        require(client.get("/api/ready").status_code == 200, "Installed readiness failed")
        inspector = inspect(app.state.db.engine)
        actual_schema = {
            name: {
                "columns": [
                    {key: str(value) if key == "type" else value for key, value in column.items()}
                    for column in inspector.get_columns(name)
                ],
                "foreign_keys": inspector.get_foreign_keys(name),
            }
            for name in inspector.get_table_names()
        }
        require(actual_schema == expected["db_schema"], "Installed database schema changed")
        require(
            set(Base.metadata.tables) == set(actual_schema) - {"alembic_version"},
            "Not all persisted models are registered",
        )
        with app.state.db.engine.connect() as connection:
            require(connection.execute(text("SELECT version_num FROM alembic_version")).scalar()
                    == "0004", "Installed migrations did not reach revision 0004")
        identity = client.post("/api/auth/demo").json()
        require(identity.get("mode") == "mock", "Installed fixture login failed")
        stdio = asyncio.run(stdio_probe(app.state.runtime, identity["user"]["id"]))

    fonts = files("mcp_documents").joinpath("assets", "fonts")
    for name in ("DejaVuSans.ttf", "DejaVuSans-Bold.ttf", "LICENSE-DejaVu.txt"):
        require(fonts.joinpath(name).is_file(), "Missing document resource: " + name)
    require("business_report" in template_catalog(), "Missing installed template catalog")
    formats = {}
    for kind in ("docx", "pdf", "xlsx", "pptx", "csv", "markdown", "html"):
        specification = {
            "format": kind, "title": "Installed café résumé",
            "blocks": [{"type": "paragraph", "text": "Synthetic wheel resource readback."}],
        }
        if kind in {"xlsx", "csv"}:
            specification.pop("blocks")
            specification["sheets"] = [{
                "name": "Budget", "columns": ["Task", "Cost", "Due", "Formula"],
                "rows": [[{"type": "string", "value": "Synthetic task"},
                          {"type": "number", "value": 42.5},
                          {"type": "date", "value": "2026-11-12"},
                          {"type": "formula", "value": "=SUM(B2:B2)"}]],
            }]
        rendered = ArtifactEngine().create(
            ArtifactSpec.model_validate(specification), Path.cwd() / "generated"
        )
        require(rendered.validation.get("semantic_readback") is True, "Semantic readback failed")
        require(ArtifactEngine().validate(rendered.path, kind)["valid"], "Readback failed")
        formats[kind] = {"status": "PASS", "size": rendered.size}
    return {
        "status": "PASS", "python": sys.version.split()[0], "mcp": version("mcp"),
        "import_locations": locations, "editable_imports": False, "pythonpath": "UNSET",
        "foreign_working_directory": True, "tool_count": len(registry),
        "policy_schema_digests": "EXACT", "openapi": "EXACT", "database_schema": "EXACT",
        "registered_model_tables": len(Base.metadata.tables), "alembic_revision": "0004",
        "live_tool_count": len(live_registry),
        "migration_files": revision_names, "mock_fixture": "EXACT", "fixture_manifest": "EXACT",
        "evaluation_case_count": len(packaged_cases), "evaluation_cases_and_assertions": "EXACT",
        "artifact_formats": formats, "fonts_license_templates": "PASS", "stdio": stdio,
        "google_requests": 0, "model_requests": 0,
    }


if __name__ == "__main__":
    output = Path(sys.argv[2])
    try:
        output.write_text(json.dumps(probe(json.loads(Path(sys.argv[1]).read_text())), indent=2))
    except Exception as error:
        # Only controlled assertions or the exception type enter public evidence.
        message = str(error) if isinstance(error, AssertionError) else type(error).__name__
        output.write_text(json.dumps({"status": "FAIL", "error": message}))
        raise SystemExit(1) from None
"""


def wheel_set(directory: Path) -> dict[str, tuple[Path, str]]:
    selected: dict[str, tuple[Path, str]] = {}
    for path in sorted(directory.glob("*.whl")):
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            if len(names) != len(set(names)):
                raise ValueError(f"Duplicate ZIP members in {path.name}")
            metadata = [name for name in names if name.endswith(".dist-info/METADATA")]
            if len(metadata) != 1:
                raise ValueError(f"Invalid wheel metadata in {path.name}")
            record = Parser().parsestr(archive.read(metadata[0]).decode())
        name, version = record["Name"], record["Version"]
        if name == "mcp-workspace-ai":
            continue  # Legacy root distribution is never installed; root owns its removal.
        if name not in PACKAGES or name in selected:
            raise ValueError(f"Unexpected or duplicate workspace wheel: {path.name}")
        selected[name] = (path.resolve(), version)
    if set(selected) != set(PACKAGES):
        raise ValueError("Expected exactly eight workspace member wheels")
    return selected


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, default=ROOT / "dist")
    parser.add_argument("--output", type=Path, default=ROOT / ".local/verification/wheels.json")
    args = parser.parse_args()
    started = time.monotonic()
    proof: dict[str, Any] = {"status": "FAIL", "measured_at": datetime.now(UTC).isoformat()}
    temporary = Path(tempfile.mkdtemp(prefix="workspace-installed-wheels-"))
    log = temporary / "private-diagnostics.log"
    log.touch(mode=0o600)
    env = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
    env["UV_CACHE_DIR"] = os.environ.get("UV_CACHE_DIR", "/tmp/workspace-ai-uv-cache")
    stage = "wheel_selection"

    def run(command: list[str], *, cwd: Path = ROOT) -> None:
        result = subprocess.run(command, cwd=cwd, env=env, capture_output=True, timeout=300)
        with log.open("ab") as stream:
            stream.write(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError(f"{stage} exited {result.returncode}")

    try:
        uv = shutil.which("uv")
        if uv is None:
            raise RuntimeError("uv is required")
        selected = wheel_set(args.dist)
        proof["wheels"] = {
            name: {
                "file": path.name,
                "version": version,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
            for name, (path, version) in selected.items()
        }
        requirements = temporary / "production-requirements.txt"
        stage = "locked_requirements_export"
        run(
            [
                uv,
                "export",
                "--locked",
                "--all-packages",
                "--no-emit-workspace",
                "--no-dev",
                "--format",
                "requirements-txt",
                "--output-file",
                str(requirements),
            ]
        )
        stage = "fresh_venv"
        run([uv, "venv", "--python", sys.executable, str(temporary / "venv")])
        python = temporary / "venv/bin/python"
        stage = "locked_third_party_install"
        run(
            [
                uv,
                "pip",
                "install",
                "--python",
                str(python),
                "--require-hashes",
                "--no-deps",
                "-r",
                str(requirements),
            ]
        )
        stage = "workspace_wheel_install"
        run(
            [
                uv,
                "pip",
                "install",
                "--python",
                str(python),
                "--no-deps",
                *[str(path) for path, _ in selected.values()],
            ]
        )
        expected = {
            "repository": str(ROOT),
            "packages": PACKAGES,
            "versions": {name: version for name, (_, version) in selected.items()},
        }
        expected.update(current_contracts(ROOT))
        for name in ("fixture", "manifest"):
            fixture_path = (
                ROOT
                / "tests/fixtures/synthetic"
                / ("workspace.json" if name == "fixture" else "manifest.json")
            )
            expected[name + "_sha256"] = hashlib.sha256(fixture_path.read_bytes()).hexdigest()
        work = temporary / "foreign-cwd"
        work.mkdir()
        inputs, output, probe = work / "expected.json", work / "result.json", work / "probe.py"
        inputs.write_text(json.dumps(expected))
        inputs.chmod(0o600)
        probe.write_text(PROBE)
        env.update(
            {
                "MODE": "mock",
                "LLM_PROVIDER": "fake",
                "LLM_MODEL": "",
                "LLM_API_KEY": "",
                "GOOGLE_CLIENT_ID": "",
                "GOOGLE_CLIENT_SECRET": "",
                "SESSION_SECRET": "",
                "TOKEN_ENCRYPTION_KEY": "",
                "DATA_DIR": str(work / "data"),
            }
        )
        stage = "foreign_cwd_package_probe"
        try:
            run([str(python), str(probe), str(inputs), str(output)], cwd=work)
        finally:
            if output.exists():
                proof["probe"] = json.loads(output.read_text())
        proof["status"] = "PASS"
        proof["elapsed_seconds"] = round(time.monotonic() - started, 2)
        proof["installation"] = (
            "Fresh venv; locked third-party hashes; eleven local wheels --no-deps"
        )
    except Exception as error:
        proof.update(
            failed_stage=stage,
            error=type(error).__name__,
            private_diagnostics_directory=str(temporary),
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(proof, indent=2) + "\n")
    print(
        json.dumps({key: value for key, value in proof.items() if key not in {"wheels", "probe"}})
    )
    if proof["status"] == "PASS":
        shutil.rmtree(temporary)
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
