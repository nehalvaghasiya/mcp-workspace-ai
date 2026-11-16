from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import httpx
import pytest
from mcp_workspace_api.operations import dev_server

from tests.support.isolated_settings import IsolatedSettings


def test_make_dev_reuses_existing_workspace_services(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = IsolatedSettings(data_dir=tmp_path)
    monkeypatch.setattr(dev_server, "load_settings", lambda: settings)
    monkeypatch.setattr(dev_server, "existing_service", lambda *args, **kwargs: True, raising=False)
    spawn = Mock(side_effect=AssertionError("Already-running services must not be started twice"))
    monkeypatch.setattr(dev_server.subprocess, "Popen", spawn)
    assert dev_server.run_dev() == 0
    spawn.assert_not_called()


def test_existing_service_rejects_another_workspace(tmp_path: Path) -> None:
    settings = IsolatedSettings(data_dir=tmp_path)
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json={
                "status": "ok",
                "application": "mcp-workspace-ai",
                "instance_id": "another-workspace",
                "mode": "mock",
            },
        )
    )
    with httpx.Client(transport=transport) as client:
        with pytest.raises(RuntimeError, match="already in use"):
            dev_server.existing_service(client, "http://127.0.0.1:8000", settings)


def test_existing_service_checks_identity_and_readiness(tmp_path: Path) -> None:
    from mcp_workspace_api.core.runtime_identity import runtime_identity

    settings = IsolatedSettings(data_dir=tmp_path)

    def handle(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/ready":
            return httpx.Response(200, json={"status": "ready"})
        return httpx.Response(
            200,
            json={
                "status": "ok",
                "application": "mcp-workspace-ai",
                "instance_id": runtime_identity(settings),
                "mode": "mock",
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        assert dev_server.existing_service(client, "http://127.0.0.1:8000", settings)


def test_frontend_reuse_requires_this_apps_html(tmp_path: Path) -> None:
    from mcp_workspace_api.core.runtime_identity import runtime_identity

    settings = IsolatedSettings(data_dir=tmp_path)

    def handle(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/":
            return httpx.Response(200, text="<html><title>Another site</title></html>")
        return httpx.Response(
            200,
            json={
                "status": "ok",
                "application": "mcp-workspace-ai",
                "instance_id": runtime_identity(settings),
                "mode": "mock",
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        with pytest.raises(RuntimeError, match="already in use"):
            dev_server.existing_service(client, "http://127.0.0.1:5173", settings, frontend=True)
