from mcp_workspace_common.contracts import Risk, ToolDefinition
from mcp_workspace_common.schemas.no_args import NoArgs


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="demo.ping",
        description="demo: ping. Access is limited to the signed-in user's authorized data.",
        input_model=NoArgs,
        risk=Risk.READ,
        scopes=(),
    )
