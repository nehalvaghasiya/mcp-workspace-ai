from mcp_workspace_common.contracts import GMAIL, Risk, ToolDefinition

from mcp_gmail.schemas.attachment import Attachment


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="gmail.get_attachment",
        description="Read supported attachment text from an identified Gmail message and attachment, with bounded extraction.",
        input_model=Attachment,
        risk=Risk.READ,
        scopes=(GMAIL + "readonly",),
    )
