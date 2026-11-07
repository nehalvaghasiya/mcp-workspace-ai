"""Canonical schema and policy for artifact.get_artifact_metadata."""

from mcp_workspace_common.contracts import Risk, ToolDefinition

from mcp_documents.schemas.artifact_id import ArtifactId


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="artifact.get_artifact_metadata",
        description="artifact: get artifact metadata. Access is limited to the signed-in user's authorized data.",
        input_model=ArtifactId,
        risk=Risk.READ,
    )
