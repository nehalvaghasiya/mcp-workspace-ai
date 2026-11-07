"""Canonical schema and policy for artifact.create_pdf."""

from mcp_workspace_common.contracts import Risk, ToolDefinition

from mcp_documents.schemas.artifact_spec import ArtifactSpec


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="artifact.create_pdf",
        description="artifact: create pdf. Access is limited to the signed-in user's authorized data.",
        input_model=ArtifactSpec,
        risk=Risk.LOCAL_WRITE,
    )
