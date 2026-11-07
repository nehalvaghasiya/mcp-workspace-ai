from mcp_workspace_common.contracts import CAL, Risk, ToolDefinition

from mcp_calendar.schemas.free_busy import FreeBusy


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="calendar.query_freebusy",
        description="calendar: query freebusy. Access is limited to the signed-in user's authorized data.",
        input_model=FreeBusy,
        risk=Risk.READ,
        scopes=(CAL + "freebusy",),
    )
