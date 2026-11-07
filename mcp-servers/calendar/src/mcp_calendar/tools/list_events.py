from mcp_workspace_common.contracts import CAL, Risk, ToolDefinition

from mcp_calendar.schemas.event_search import EventSearch


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="calendar.list_events",
        description="calendar: list events. Access is limited to the signed-in user's authorized data.",
        input_model=EventSearch,
        risk=Risk.READ,
        scopes=(CAL + "events.readonly",),
    )
