"""Canonical schema and policy for artifact.validate_artifact."""

from mcp_workspace_common.contracts import Risk, ToolDefinition

from mcp_documents.schemas.artifact_id import ArtifactId


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="artifact.validate_artifact",
        description="artifact: validate artifact. Access is limited to the signed-in user's authorized data.",
        input_model=ArtifactId,
        risk=Risk.READ,
    )
