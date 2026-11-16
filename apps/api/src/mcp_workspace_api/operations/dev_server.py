"""Supervise both development processes and propagate startup failures."""

from __future__ import annotations

import os
import shutil
import signal
import socket
import subprocess  # nosec B404
import sys
import time
from pathlib import Path
from urllib.parse import urlsplit

import httpx

from mcp_workspace_api.core.config import Settings
from mcp_workspace_api.core.runtime_identity import runtime_identity
from mcp_workspace_api.core.runtime_settings import load_settings, validate_live_configuration


def stop(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    process.send_signal(signal.SIGINT)
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def port_is_open(url: str) -> bool:
    parsed = urlsplit(url)
    try:
        with socket.create_connection(
            (parsed.hostname or "127.0.0.1", parsed.port or 80), timeout=0.25
        ):
            return True
    except OSError:
        return False


def existing_service(
    client: httpx.Client, url: str, settings: Settings, *, frontend: bool = False
) -> bool:
    try:
        response = client.get(url + "/api/health")
    except httpx.HTTPError:
        if not port_is_open(url):
            return False
    else:
        try:
            health = response.json()
            matches = (
                response.status_code == 200
                and isinstance(health, dict)
                and health.get("application") == "mcp-workspace-ai"
                and health.get("instance_id") == runtime_identity(settings)
                and health.get("status") == "ok"
            )
            if matches:
                if frontend:
                    page = client.get(url + "/")
                    if page.status_code == 200 and "<title>MCP Workspace AI</title>" in page.text:
                        return True
                else:
                    ready = client.get(url + "/api/ready")
                    if ready.status_code == 200 and ready.json().get("status") == "ready":
                        return True
        except (httpx.HTTPError, ValueError, AttributeError):
            pass
    raise RuntimeError(
        f"Port {urlsplit(url).port} is already in use by another configuration or an unready service. Stop that instance before running make dev; keep the registered Google callback address unchanged."
    )


def run_dev() -> int:
    settings = load_settings()
    validate_live_configuration(settings)
    settings.prepare()
    frontend = Path("apps/web")
    pnpm = shutil.which("pnpm") or str(Path(".local/tools/pnpm/node_modules/.bin/pnpm").resolve())
    if not frontend.is_dir() or not Path(pnpm).is_file():
        raise SystemExit("Run make setup and make dev from the project root")
    port = urlsplit(settings.api_url).port or 8000
    web_port = urlsplit(settings.web_origin).port or 5173
    api_url = f"http://127.0.0.1:{port}"
    web_url = f"http://127.0.0.1:{web_port}"
    env = {**os.environ, "DATA_DIR": str(settings.data_dir.resolve()), "WORKSPACE_API_URL": api_url}
    processes: list[subprocess.Popen[bytes]] = []
    try:
        with httpx.Client(timeout=1, trust_env=False) as client:
            if existing_service(client, api_url, settings):
                print(f"Using existing workspace API at {api_url}")
            else:
                api = subprocess.Popen(
                    [sys.executable, "-m", "mcp_workspace_api.cli", "api", "--port", str(port)],
                    env=env,
                )  # nosec B603
                processes.append(api)
                deadline = time.monotonic() + 30
                while time.monotonic() < deadline:
                    if api.poll() is not None:
                        return api.returncode or 1
                    try:
                        if client.get(api_url + "/api/ready").status_code == 200:
                            break
                    except httpx.HTTPError:
                        pass
                    time.sleep(0.1)
                else:
                    print("API did not become ready within 30 seconds", file=sys.stderr)
                    return 1
            if existing_service(client, web_url, settings, frontend=True):
                print(f"Using existing workspace frontend at {settings.web_origin}")
            else:
                web = subprocess.Popen(
                    [pnpm, "run", "dev", "--port", str(web_port)], cwd=frontend, env=env
                )  # nosec B603
                processes.append(web)
        if not processes:
            return 0
        while True:
            for process in processes:
                if process.poll() is not None:
                    return process.returncode or 1
            time.sleep(0.1)
    except KeyboardInterrupt:
        return 0
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        return 1
    finally:
        for process in reversed(processes):
            stop(process)
