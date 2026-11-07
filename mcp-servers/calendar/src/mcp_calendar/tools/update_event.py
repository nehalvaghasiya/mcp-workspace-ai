from mcp_workspace_common.contracts import CAL, Risk, ToolDefinition

from mcp_calendar.schemas.update_event import UpdateEvent


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="calendar.update_event",
        description="calendar: update event. Access is limited to the signed-in user's authorized data.",
        input_model=UpdateEvent,
        risk=Risk.EXTERNAL_EFFECT,
        scopes=(CAL + "events",),
    )
