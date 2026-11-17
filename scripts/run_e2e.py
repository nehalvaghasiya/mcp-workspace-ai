"""Run disposable browser fixtures on isolated ports without stopping live services."""

from __future__ import annotations

import argparse
import os
import signal
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.bootstrap_pnpm import pnpm_executable

ROOT = Path(__file__).resolve().parents[1]
API_URL = "http://127.0.0.1:8000"


def stop(process: subprocess.Popen[bytes] | None) -> None:
    if process is None or process.poll() is not None:
        return
    if os.name == "posix":
        os.killpg(process.pid, signal.SIGTERM)
    else:
        process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
        process.wait(timeout=5)


def ready(process: subprocess.Popen[bytes], api_url: str) -> None:
    deadline = time.monotonic() + 30
    with httpx.Client(base_url=api_url, timeout=1, trust_env=False) as client:
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError("The isolated mock backend exited during startup")
            try:
                response = client.get("/api/health")
                if response.status_code == 200 and response.json().get("mode") == "mock":
                    if client.get("/api/ready").status_code == 200:
                        return
            except (httpx.HTTPError, ValueError):
                pass
            time.sleep(0.1)
    raise RuntimeError("The isolated mock backend did not become ready within 30 seconds")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "playwright_args",
        nargs=argparse.REMAINDER,
        help="Arguments forwarded after -- to Playwright",
    )
    args = parser.parse_args()
    pnpm = pnpm_executable()
    if os.name != "posix":
        parser.error("This supervisor currently requires POSIX socket inheritance")
    forwarded = (
        args.playwright_args[1:] if args.playwright_args[:1] == ["--"] else args.playwright_args
    )
    backend: subprocess.Popen[bytes] | None = None
    browser: subprocess.Popen[bytes] | None = None
    with tempfile.TemporaryDirectory(prefix="workspace-ai-e2e-") as temporary:
        directory = Path(temporary)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as frontend_listener:
            frontend_listener.bind(("127.0.0.1", 0))
            web_url = f"http://127.0.0.1:{frontend_listener.getsockname()[1]}"
        env = {
            **os.environ,
            "MODE": "mock",
            "LLM_PROVIDER": "fake",
            "LLM_MODEL": "",
            "LLM_API_KEY": "",
            "GOOGLE_CLIENT_ID": "",
            "GOOGLE_CLIENT_SECRET": "",
            "SESSION_SECRET": "",
            "TOKEN_ENCRYPTION_KEY": "",
            "DATA_DIR": str(directory / "data"),
            "WORKSPACE_DATA_DIR": str(directory / "data"),
            "API_URL": API_URL,
            "WEB_ORIGIN": web_url,
            "E2E_WEB_URL": web_url,
            "E2E_ARTIFACT_DIR": str(ROOT / ".local/e2e-captures"),
            "E2E_BACKEND": "1",
            "PATH": str(pnpm.parent) + os.pathsep + os.environ.get("PATH", ""),
        }
        local_libraries = ROOT / ".local/browser-libs/extracted/usr/lib/x86_64-linux-gnu"
        if local_libraries.is_dir():
            env["LD_LIBRARY_PATH"] = (
                str(local_libraries) + os.pathsep + os.environ.get("LD_LIBRARY_PATH", "")
            )
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
                listener.bind(("127.0.0.1", 0))
                api_url = f"http://127.0.0.1:{listener.getsockname()[1]}"
                env.update(API_URL=api_url, WORKSPACE_API_URL=api_url)
                listener.listen(128)
                with (directory / "backend.log").open("wb") as log:
                    backend = subprocess.Popen(
                        [
                            sys.executable,
                            "-m",
                            "uvicorn",
                            "mcp_workspace_api.main:create_app",
                            "--factory",
                            "--fd",
                            str(listener.fileno()),
                            "--no-access-log",
                        ],
                        cwd=ROOT,
                        env=env,
                        stdout=log,
                        stderr=subprocess.STDOUT,
                        pass_fds=(listener.fileno(),),
                        start_new_session=True,
                    )
                    ready(backend, api_url)
                    print(
                        "Isolated mock backend ready; running real browser workflows.", flush=True
                    )
                    browser = subprocess.Popen(
                        [str(pnpm), "--filter", "@mcp-workspace/web", "test:e2e", *forwarded],
                        cwd=ROOT,
                        env=env,
                        start_new_session=True,
                    )
                    return browser.wait()
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            log_path = directory / "backend.log"
            if log_path.exists():
                print(log_path.read_text(errors="replace")[-8_000:], file=sys.stderr)
            return 2
        except KeyboardInterrupt:
            return 130
        finally:
            stop(browser)
            stop(backend)


if __name__ == "__main__":
    raise SystemExit(main())
