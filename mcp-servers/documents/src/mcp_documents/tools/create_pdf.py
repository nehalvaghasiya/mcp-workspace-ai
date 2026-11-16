"""Canonical schema and policy for artifact.create_pdf."""

from mcp_workspace_common.contracts import Risk, ToolDefinition

from mcp_documents.schemas.artifact_spec import ArtifactSpec


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="artifact.create_pdf",
        description="Create a validated downloadable local PDF. Supply format='pdf', a title, and report blocks such as headings, paragraphs, or bullet lists. Include source titles and links in a Sources section when available. Returns the actual owned download URL. Does not modify Google files.",
        input_model=ArtifactSpec,
        risk=Risk.LOCAL_WRITE,
    )
