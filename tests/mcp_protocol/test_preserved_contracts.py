"""Preserve published contracts and legacy storage while allowing additive features."""

import json
import sqlite3
from pathlib import Path

from mcp_workspace_common.hashing import digest
from sqlalchemy import inspect

from tests.support import Browser, LiveServer

ROOT = Path(__file__).resolve().parents[2]


async def test_raw_mcp_schemas_and_policy_digests_match_baseline(
    live_server: LiveServer, browser: Browser
) -> None:
    catalog = await live_server.runtime.catalog(browser.user_id)
    published = json.loads((ROOT / "config/tool-policies.yaml").read_text())["tools"]
    assert {tool["name"] for tool in catalog} == set(live_server.runtime.tools)
    for tool in catalog:
        policy = published[tool["name"]]
        assert tool["risk"] == policy["risk"]
        assert tool["digest"] == digest(
            {
                "input": tool["input_schema"],
                "output": tool["output_schema"],
                "policy": policy["digest"],
            }
        )
        assert tool["input_schema"]["type"] == "object"
        assert "request" in tool["input_schema"]["properties"]
    assert live_server.app.openapi() == json.loads(
        (ROOT / "packages/shared-types/openapi.json").read_text()
    )


def test_database_tables_columns_and_foreign_keys_match_baseline(live_server: LiveServer) -> None:
    inspector = inspect(live_server.runtime.db.engine)
    with sqlite3.connect(":memory:") as legacy:
        legacy.executescript((ROOT / "tests/fixtures/legacy-storage/workspace.sql").read_text())
        tables = [
            row[0] for row in legacy.execute("SELECT name FROM sqlite_master WHERE type='table'")
        ]
        assert set(tables) <= set(inspector.get_table_names())
        for name in tables:
            current = {column["name"]: column for column in inspector.get_columns(name)}
            for column in legacy.execute(f"PRAGMA table_info('{name}')"):
                assert column[1] in current, f"Legacy column removed: {name}.{column[1]}"
                assert bool(column[3]) == (not current[column[1]]["nullable"])
            current_keys = {
                (
                    tuple(key["constrained_columns"]),
                    key["referred_table"],
                    tuple(key["referred_columns"]),
                )
                for key in inspector.get_foreign_keys(name)
            }
            for key in legacy.execute(f"PRAGMA foreign_key_list('{name}')"):
                assert ((key[3],), key[2], (key[4],)) in current_keys
