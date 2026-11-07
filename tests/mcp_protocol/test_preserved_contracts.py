"""The package split must preserve wire contracts and the existing table schema."""

import json
from pathlib import Path

from sqlalchemy import inspect

from tests.support import Browser, LiveServer

BASELINE = Path(__file__).resolve().parents[2] / "docs/verification/reorganization"


async def test_raw_mcp_schemas_and_policy_digests_match_baseline(
    live_server: LiveServer, browser: Browser
) -> None:
    catalog = await live_server.runtime.catalog(browser.user_id)
    for tool in catalog:
        tool.pop("enabled")
    assert catalog == json.loads((BASELINE / "baseline-mcp.json").read_text())
    assert {name: tool.digest for name, tool in live_server.runtime.tools.items()} == json.loads(
        (BASELINE / "baseline-policy-digests.json").read_text()
    )
    assert live_server.app.openapi() == json.loads((BASELINE / "baseline-openapi.json").read_text())


def test_database_tables_columns_and_foreign_keys_match_baseline(live_server: LiveServer) -> None:
    inspector = inspect(live_server.runtime.db.engine)
    actual = {
        name: {
            "columns": [
                {key: str(value) if key == "type" else value for key, value in column.items()}
                for column in inspector.get_columns(name)
            ],
            "foreign_keys": inspector.get_foreign_keys(name),
        }
        for name in inspector.get_table_names()
    }
    assert actual == json.loads((BASELINE / "baseline-db-schema.json").read_text())
