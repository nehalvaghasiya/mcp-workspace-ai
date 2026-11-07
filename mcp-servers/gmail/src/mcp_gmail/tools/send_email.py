from mcp_workspace_common.contracts import GMAIL, Risk, ToolDefinition

from mcp_gmail.schemas.draft_id import DraftId


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="gmail.send_draft",
        description="gmail: send draft. Access is limited to the signed-in user's authorized data.",
        input_model=DraftId,
        risk=Risk.EXTERNAL_EFFECT,
        scopes=(GMAIL + "compose",),
    )
