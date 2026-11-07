"""Programmatic Alembic entrypoint, also used by the application startup."""

from importlib.resources import files

from alembic import command
from alembic.config import Config

from mcp_workspace_api.db import Database


def migrate(database: Database, revision: str = "head") -> None:
    config = Config()
    config.set_main_option(
        "script_location", str(files("mcp_workspace_api.db").joinpath("migrations"))
    )
    with database.engine.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, revision)
