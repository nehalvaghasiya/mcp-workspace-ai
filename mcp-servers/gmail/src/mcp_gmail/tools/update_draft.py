from mcp_workspace_common.contracts import GMAIL, Risk, ToolDefinition

from mcp_gmail.schemas.update_draft import UpdateDraft


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="gmail.update_draft",
        description="Replace a selected Gmail draft with the exact approved content and owned artifact attachments; sending remains a separate action.",
        input_model=UpdateDraft,
        risk=Risk.ACCOUNT_WRITE,
        scopes=(GMAIL + "compose",),
    )
