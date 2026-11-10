"""Run the browser suite against a disposable mock backend on its documented port."""

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


def ready(process: subprocess.Popen[bytes]) -> None:
    deadline = time.monotonic() + 30
    with httpx.Client(base_url=API_URL, timeout=1, trust_env=False) as client:
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
            "API_URL": API_URL,
            "WEB_ORIGIN": "http://127.0.0.1:5173",
            "E2E_BACKEND": "1",
            "PATH": str(pnpm.parent) + os.pathsep + os.environ.get("PATH", ""),
        }
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
                try:
                    listener.bind(("127.0.0.1", 8000))
                except OSError as exc:
                    raise RuntimeError(
                        "Port 8000 is occupied; stop its server before running isolated E2E tests"
                    ) from exc
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
                    ready(backend)
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
