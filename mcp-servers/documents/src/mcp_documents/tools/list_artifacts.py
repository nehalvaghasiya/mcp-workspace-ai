"""Canonical schema and policy for artifact.list_artifacts."""

from mcp_workspace_common.contracts import Risk, ToolDefinition

from mcp_documents.schemas.pagination import Pagination


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="artifact.list_artifacts",
        description="artifact: list artifacts. Access is limited to the signed-in user's authorized data.",
        input_model=Pagination,
        risk=Risk.READ,
    )
