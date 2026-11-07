"""Official SDK artifact server assembled from one authoritative tool registry."""

from __future__ import annotations

from typing import Any

from mcp.server import MCPServer
from mcp_workspace_common.contracts import ToolDefinition
from mcp_workspace_common.mcp.factory import build_server

from mcp_documents.resources.templates import template_catalog
from mcp_documents.tools.create_csv import definition as create_csv
from mcp_documents.tools.create_excel import definition as create_xlsx
from mcp_documents.tools.create_html import definition as create_html
from mcp_documents.tools.create_markdown import definition as create_markdown
from mcp_documents.tools.create_pdf import definition as create_pdf
from mcp_documents.tools.create_powerpoint import definition as create_pptx
from mcp_documents.tools.create_word import definition as create_docx
from mcp_documents.tools.get_artifact_metadata import definition as get_artifact_metadata
from mcp_documents.tools.list_artifacts import definition as list_artifacts
from mcp_documents.tools.validate_artifact import definition as validate_artifact


def tool_definitions() -> dict[str, ToolDefinition]:
    definitions = [
        create_docx(),
        create_pdf(),
        create_xlsx(),
        create_pptx(),
        create_csv(),
        create_markdown(),
        create_html(),
        get_artifact_metadata(),
        validate_artifact(),
        list_artifacts(),
    ]
    return {definition.name: definition for definition in definitions}


def create_server(runtime: Any) -> MCPServer[Any]:
    return build_server("artifact", tool_definitions(), runtime, template_catalog=template_catalog)
