from __future__ import annotations

import copy
import uuid
from typing import Any

from mcp_workspace_common.errors import ConnectorError
from mcp_workspace_common.mock.lookup import _find
from mcp_workspace_common.utils.results import _page, _source

from mcp_calendar.providers.time import _event_body, _expand_event, _instant, _range


class MockCalendar:
    _find = staticmethod(_find)

    def _calendar_access(
        self, state: dict[str, Any], calendar_id: str, write: bool = False
    ) -> dict[str, Any]:
        calendar = self._find(state["calendars"], calendar_id)
        role = calendar.get("accessRole")
        if role == "none" or (write and role not in {"owner", "writer"}):
            raise ConnectorError("permission_denied", "Calendar is inaccessible or read only")
        return calendar

    def _event(self, state: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
        self._calendar_access(state, args.get("calendar_id", "primary"))
        event_id = args["event_id"]
        if "_" in event_id:
            instances = [instance for item in state["events"] for instance in _expand_event(item)]
            event = self._find(instances, event_id)
        else:
            event = self._find(state["events"], event_id)
        if event["calendar_id"] != args.get("calendar_id", "primary"):
            raise ConnectorError("not_found", "Event not found in this calendar")
        return event

    def call(
        self, state: dict[str, Any], tool: str, args: dict[str, Any]
    ) -> tuple[dict[str, Any], bool]:
        if tool == "list_calendars":
            return {"calendars": state["calendars"]}, False
        if tool == "query_freebusy":
            start, end = _range(args)
            calendars = {}
            for calendar_id in args["calendar_ids"]:
                try:
                    calendar_result, _ = self.call(
                        state,
                        "list_events",
                        args | {"calendar_id": calendar_id, "max_results": 100},
                    )
                    calendars[calendar_id] = {
                        "busy": [
                            {
                                "start": max(start, _instant(x["start"])).isoformat(),
                                "end": min(end, _instant(x["end"])).isoformat(),
                            }
                            for x in calendar_result["events"]
                            if x.get("transparency") != "transparent"
                        ]
                    }
                except ConnectorError:
                    calendars[calendar_id] = {
                        "errors": [{"reason": "permission_denied"}],
                        "busy": [],
                    }
            return {
                "calendars": calendars,
                "time_min": start.isoformat(),
                "time_max": end.isoformat(),
            }, False
        calendar_id = args.get("calendar_id", "primary")
        calendar = self._calendar_access(
            state, calendar_id, tool in {"create_event", "update_event", "cancel_event"}
        )
        if tool == "list_events":
            start, end = _range(args)
            events = [
                instance
                for event in state["events"]
                if event["calendar_id"] == calendar_id
                for instance in _expand_event(event)
                if instance.get("status") != "cancelled"
                and _instant(instance["start"]) < end
                and _instant(instance["end"]) > start
            ]
            events.sort(key=lambda x: _instant(x["start"]))
            result = _page(events, args, "events")
            result["timezone"] = args.get("timezone", calendar.get("timeZone", "America/Chicago"))
            result["sources"] = [_source("calendar", x, True) for x in result["events"]]
            return result, False
        if tool == "get_event":
            event = self._event(state, args)
            return event | {"sources": [_source("calendar", event, True)]}, False
        if tool == "create_event":
            body = _event_body(args)
            rid = body.get("id") or f"event-{uuid.uuid4().hex[:12]}"
            for existing in state["events"]:
                if existing["id"] == rid:
                    return existing, False
            event = body | {
                "id": rid,
                "calendar_id": calendar_id,
                "status": "confirmed",
                "etag": f'"{uuid.uuid4().hex}"',
            }
            state["events"].append(event)
            return event, True
        if tool in {"update_event", "cancel_event"}:
            if "_" in args["event_id"]:
                raise ConnectorError(
                    "unsupported_recurrence",
                    "Mock changes to individual recurring instances are not supported; choose the recurring series",
                )
            event = self._event(state, args)
            if args.get("_snapshot") != event or (
                args.get("etag") and args["etag"] != event.get("etag")
            ):
                raise ConnectorError(
                    "stale_action", "Event changed or approved snapshot is missing"
                )
            if tool == "cancel_event":
                event["status"] = "cancelled"
            else:
                changes = args["changes"]
                merged = {
                    "title": event["summary"],
                    "start": event["start"],
                    "end": event["end"],
                    "timezone": event["start"].get("timeZone", "America/Chicago"),
                } | changes
                event.update(_event_body(merged))
            event["etag"] = f'"{uuid.uuid4().hex}"'
            return event, True
        raise ConnectorError("unknown_tool", "Unknown Calendar tool")

    def snapshot(self, state: dict[str, Any], tool: str, args: dict[str, Any]) -> dict[str, Any]:
        return (
            copy.deepcopy(self._event(state, args))
            if tool in {"update_event", "cancel_event"}
            else {}
        )
