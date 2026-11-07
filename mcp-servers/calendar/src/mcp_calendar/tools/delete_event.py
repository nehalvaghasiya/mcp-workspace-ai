from mcp_workspace_common.contracts import CAL, Risk, ToolDefinition

from mcp_calendar.schemas.event_id import EventId


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="calendar.cancel_event",
        description="calendar: cancel event. Access is limited to the signed-in user's authorized data.",
        input_model=EventId,
        risk=Risk.DESTRUCTIVE,
        scopes=(CAL + "events",),
    )
