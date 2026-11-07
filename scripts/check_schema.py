"""Fail on backend/OpenAPI drift without changing the committed browser contract."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from mcp_workspace_api.core.config import Settings
from mcp_workspace_api.main import create_app


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="workspace-schema-") as temporary:
        # pydantic-settings supports _env_file; its generated mypy signature omits it.
        settings = Settings(
            mode="mock", llm_provider="fake", data_dir=Path(temporary), _env_file=None
        )  # type: ignore[call-arg]
        generated = create_app(settings).openapi()
    committed = json.loads(Path("packages/shared-types/openapi.json").read_text())
    if generated != committed:
        print(
            "API schema changed. Export the schema and regenerate browser types before committing."
        )
        return 1
    print("Backend OpenAPI matches the browser contract.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
