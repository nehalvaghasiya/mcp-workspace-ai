from mcp_workspace_common.contracts import CAL, Risk, ToolDefinition

from mcp_calendar.schemas.create_event import CreateEvent


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="calendar.create_event",
        description="calendar: create event. Access is limited to the signed-in user's authorized data.",
        input_model=CreateEvent,
        risk=Risk.EXTERNAL_EFFECT,
        scopes=(CAL + "events",),
    )
