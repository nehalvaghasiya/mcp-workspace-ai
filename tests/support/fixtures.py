from __future__ import annotations

import socket
import threading
import time
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
import uvicorn
from mcp_workspace_api.core.config import Settings
from mcp_workspace_api.main import create_app

from tests.support.browser import Browser
from tests.support.live_server import LiveServer


@pytest.fixture
def live_server(tmp_path: Path) -> Iterator[LiveServer]:
    # The listener is reserved before the worker starts, avoiding port selection races.
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    port = listener.getsockname()[1]
    # Pydantic Settings supports _env_file at runtime; its generated init omits it.
    settings = Settings(  # type: ignore[call-arg]
        _env_file=None,
        mode="mock",
        data_dir=tmp_path,
        api_url=f"http://127.0.0.1:{port}",
        web_origin="http://localhost:5173",
        llm_provider="fake",
    )
    app = create_app(settings)
    server = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning", access_log=False)
    )
    thread = threading.Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
    thread.start()
    deadline = time.monotonic() + 10
    try:
        while not server.started and thread.is_alive() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert server.started, "Real TCP application did not complete startup and migrations"
        yield LiveServer(app, settings)
    finally:
        server.should_exit = True
        thread.join(timeout=10)
        if thread.is_alive():
            server.force_exit = True
            thread.join(timeout=5)
        listener.close()
        assert not thread.is_alive(), "Application thread failed to shut down"


@pytest.fixture
async def browser(live_server: LiveServer) -> AsyncIterator[Browser]:
    async with live_server.browser() as session:
        yield session
