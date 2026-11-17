from __future__ import annotations

from typing import Any

from mcp_workspace_common.errors import ConnectorError
from mcp_workspace_common.providers.google_client import GoogleClient
from mcp_workspace_common.providers.identifiers import _identifier
from mcp_workspace_common.utils.results import _source

from mcp_calendar.providers.time import _event_body, _instant, _range


class GoogleCalendar:
    def __init__(self, transport: GoogleClient) -> None:
        self._request = transport.request

    async def call(self, tool: str, args: dict[str, Any]) -> dict[str, Any]:
        base = "https://www.googleapis.com/calendar/v3"
        if tool == "list_calendars":
            result = await self._request(
                "GET",
                base + "/users/me/calendarList",
                read=True,
                params={
                    "maxResults": min(int(args.get("max_results", 100)), 250),
                    **({"pageToken": args["page_token"]} if args.get("page_token") else {}),
                },
            )
            return {
                "calendars": result.get("items", []),
                "next_page_token": result.get("nextPageToken"),
            }
        if tool == "query_freebusy":
            _range(args)
            return await self._request(
                "POST",
                base + "/freeBusy",
                read=True,
                json={
                    "timeMin": args["time_min"],
                    "timeMax": args["time_max"],
                    "timeZone": args.get("timezone", "America/Chicago"),
                    "items": [{"id": cid} for cid in args["calendar_ids"]],
                },
            )
        url = base + "/calendars/" + _identifier(args.get("calendar_id", "primary")) + "/events"
        if tool == "list_events":
            _range(args)
            params: dict[str, Any] = {
                "timeMin": args["time_min"],
                "timeMax": args["time_max"],
                "maxResults": min(int(args.get("max_results", 20)), 100),
                "singleEvents": "true",
                "orderBy": "startTime",
                "timeZone": args.get("timezone", "America/Chicago"),
            }
            if args.get("page_token"):
                params["pageToken"] = args["page_token"]
            if args.get("query"):
                params["q"] = args["query"]
            result = await self._request("GET", url, read=True, params=params)
            return {
                "events": result.get("items", []),
                "next_page_token": result.get("nextPageToken"),
                "timezone": result.get("timeZone"),
                "sources": [_source("calendar", x) for x in result.get("items", [])],
            }
        if tool == "get_event":
            result = await self._request(
                "GET", url + "/" + _identifier(args["event_id"]), read=True
            )
            return result | {"sources": [_source("calendar", result)]}
        if tool == "create_event":
            body = _event_body(args)
            created = await self._request(
                "POST",
                url,
                json=body,
                params={"sendUpdates": "all" if body.get("attendees") else "none"},
            )
            if args.get("idempotency_key"):
                created = await self._readback(url, created.get("id"), body)
            return created
        if tool in {"update_event", "cancel_event"}:
            approved = args.get("_snapshot")
            if not approved or not approved.get("etag"):
                raise ConnectorError(
                    "stale_action", "Approved event snapshot and ETag are required"
                )
            current = await self.snapshot(tool, args)
            if approved != current or (args.get("etag") and args["etag"] != current.get("etag")):
                raise ConnectorError("stale_action", "Event changed after approval")
            headers = {"If-Match": current["etag"]}
            params = {
                "sendUpdates": "all"
                if current.get("attendees") or args.get("changes", {}).get("attendees")
                else "none"
            }
            target = url + "/" + _identifier(args["event_id"])
            if tool == "cancel_event":
                await self._request("DELETE", target, headers=headers, params=params)
                return {"id": args["event_id"], "status": "cancelled"}
            changes = dict(args["changes"])
            body = _event_body(
                {
                    "title": current.get("summary", ""),
                    "start": current["start"],
                    "end": current["end"],
                    "timezone": current["start"].get(
                        "timeZone", args.get("timezone", "America/Chicago")
                    ),
                }
                | changes
            )
            updated = await self._request(
                "PATCH", target, json=body, headers=headers, params=params
            )
            if args.get("idempotency_key"):
                updated = await self._readback(url, args["event_id"], body)
            return updated
        raise ConnectorError("unknown_tool", "Unknown Calendar tool")

    async def _readback(
        self, url: str, event_id: str | None, expected: dict[str, Any]
    ) -> dict[str, Any]:
        if not event_id:
            raise ConnectorError(
                "outcome_unknown",
                "Calendar write returned no event ID; inspect the calendar before retrying",
            )
        current = await self._request("GET", url + "/" + _identifier(event_id), read=True)
        for key, value in expected.items():
            if key == "id":
                continue
            if key in {"start", "end"}:
                same = key in current and _instant(current[key]) == _instant(value)
            elif key == "attendees":
                same = sorted(
                    row.get("email", "").casefold() for row in current.get(key, [])
                ) == sorted(row.get("email", "").casefold() for row in value)
            else:
                same = current.get(key, [] if isinstance(value, list) else "") == value
            if not same:
                raise ConnectorError(
                    "outcome_unknown",
                    "Calendar readback differs from the approved event; inspect it before retrying",
                )
        return current | {"readback_verified": True}

    async def snapshot(self, tool: str, args: dict[str, Any]) -> dict[str, Any]:
        if tool not in {"update_event", "cancel_event"}:
            return {}
        return await self._request(
            "GET",
            f"https://www.googleapis.com/calendar/v3/calendars/{_identifier(args.get('calendar_id', 'primary'))}/events/{_identifier(args['event_id'])}",
            read=True,
        )
