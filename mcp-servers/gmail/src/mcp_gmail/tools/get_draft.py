from mcp_workspace_common.contracts import GMAIL, Risk, ToolDefinition

from mcp_gmail.schemas.draft_id import DraftId


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="gmail.get_draft",
        description="Inspect the recipients, subject, body, and attachment metadata of an existing Gmail draft.",
        input_model=DraftId,
        risk=Risk.READ,
        scopes=(GMAIL + "compose",),
    )
