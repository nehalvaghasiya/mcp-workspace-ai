from mcp_workspace_common.contracts import CAL, Risk, ToolDefinition

from mcp_calendar.schemas.calendar_list import CalendarList


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="calendar.list_calendars",
        description="calendar: list calendars. Access is limited to the signed-in user's authorized data.",
        input_model=CalendarList,
        risk=Risk.READ,
        scopes=(CAL + "calendarlist.readonly",),
    )
