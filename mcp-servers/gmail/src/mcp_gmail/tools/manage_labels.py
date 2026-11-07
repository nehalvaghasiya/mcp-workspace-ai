from mcp_workspace_common.contracts import GMAIL, Risk, ToolDefinition

from mcp_gmail.schemas.labels import Labels


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="gmail.apply_labels",
        description="gmail: apply labels. Access is limited to the signed-in user's authorized data.",
        input_model=Labels,
        risk=Risk.ACCOUNT_WRITE,
        scopes=(GMAIL + "modify",),
    )
