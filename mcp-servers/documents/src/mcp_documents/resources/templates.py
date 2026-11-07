"""Installed, safe template metadata; no user content or credentials."""

from importlib.resources import files


def template_catalog() -> str:
    return files("mcp_documents").joinpath("templates", "catalog.json").read_text(encoding="utf-8")
