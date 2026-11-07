"""Canonical schema and policy for artifact.create_xlsx."""

from mcp_workspace_common.contracts import Risk, ToolDefinition

from mcp_documents.schemas.artifact_spec import ArtifactSpec


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="artifact.create_xlsx",
        description="artifact: create xlsx. Access is limited to the signed-in user's authorized data.",
        input_model=ArtifactSpec,
        risk=Risk.LOCAL_WRITE,
    )
