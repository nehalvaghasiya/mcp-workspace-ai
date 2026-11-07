from mcp_workspace_common.contracts import GMAIL, Risk, ToolDefinition

from mcp_gmail.schemas.draft import Draft


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="gmail.create_draft",
        description="gmail: create draft. Access is limited to the signed-in user's authorized data.",
        input_model=Draft,
        risk=Risk.ACCOUNT_WRITE,
        scopes=(GMAIL + "compose",),
    )
