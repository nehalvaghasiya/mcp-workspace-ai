from __future__ import annotations

import copy
import hashlib
import re
from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from mcp_workspace_common.errors import ConnectorError


def _event_time(value: Any, timezone: str = "America/Chicago") -> dict[str, str]:
    try:
        zone = ZoneInfo(timezone)
        if isinstance(value, dict):
            value = value.get("dateTime") or value.get("date")
        text = str(value)
        if len(text) == 10:
            return {"date": date.fromisoformat(text).isoformat()}
        instant = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if instant.tzinfo is None:
            raise ConnectorError(
                "invalid_time", "Date/time requires an explicit UTC offset and IANA timezone"
            )
        local = instant.astimezone(zone)
        if text.endswith("Z") or text.endswith("+00:00"):
            return {"dateTime": local.isoformat(), "timeZone": timezone}
        if (
            local.replace(tzinfo=None) != instant.replace(tzinfo=None)
            or local.utcoffset() != instant.utcoffset()
        ):
            raise ConnectorError(
                "invalid_time",
                "Date/time offset does not match the selected timezone or falls in a DST gap",
            )
        return {"dateTime": instant.isoformat(), "timeZone": timezone}
    except (ValueError, ZoneInfoNotFoundError):
        raise ConnectorError("invalid_time", "Invalid date/time or timezone") from None


def _instant(value: dict[str, Any], timezone: str = "America/Chicago") -> datetime:
    if value.get("dateTime"):
        result = datetime.fromisoformat(value["dateTime"].replace("Z", "+00:00"))
        return result if result.tzinfo else result.replace(tzinfo=ZoneInfo(timezone))
    return datetime.combine(
        date.fromisoformat(value["date"]), datetime.min.time(), ZoneInfo(timezone)
    )


def _range(args: dict[str, Any]) -> tuple[datetime, datetime]:
    try:
        start = datetime.fromisoformat(str(args["time_min"]).replace("Z", "+00:00"))
        end = datetime.fromisoformat(str(args["time_max"]).replace("Z", "+00:00"))
        if not start.tzinfo or not end.tzinfo or end <= start or end - start > timedelta(days=400):
            raise ValueError
        return start, end
    except (ValueError, KeyError):
        raise ConnectorError(
            "invalid_time", "A bounded increasing time range with explicit UTC offsets is required"
        ) from None


def _event_body(args: dict[str, Any]) -> dict[str, Any]:
    timezone = args.get("timezone", "America/Chicago")
    start, end = _event_time(args["start"], timezone), _event_time(args["end"], timezone)
    if ("date" in start) != ("date" in end) or _instant(end, timezone) <= _instant(start, timezone):
        raise ConnectorError(
            "invalid_time", "Event end must follow start with matching date or date/time types"
        )
    result: dict[str, Any] = {
        "summary": args.get("title", args.get("summary", "Untitled event")),
        "start": start,
        "end": end,
    }
    for key in ("location", "description", "recurrence"):
        if key in args:
            result[key] = args[key]
    if "attendees" in args:
        result["attendees"] = [
            {"email": item} if isinstance(item, str) else item for item in args["attendees"]
        ]
    if args.get("idempotency_key"):
        result["id"] = hashlib.sha256(str(args["idempotency_key"]).encode()).hexdigest()[:32]
    return result


def _expand_event(event: dict[str, Any]) -> list[dict[str, Any]]:
    if not event.get("recurrence"):
        return [event]
    rule = str(event["recurrence"][0])
    match = re.fullmatch(r"RRULE:FREQ=(DAILY|WEEKLY);COUNT=(\d+)", rule)
    if not match or int(match[2]) > 100:
        raise ConnectorError(
            "unsupported_recurrence", "Mock recurrence supports DAILY/WEEKLY COUNT up to 100"
        )
    results = []
    zone = ZoneInfo(event["start"].get("timeZone", "America/Chicago"))
    for index in range(int(match[2])):
        item = copy.deepcopy(event)
        shift = timedelta(days=index * (7 if match[1] == "WEEKLY" else 1))
        for endpoint in ("start", "end"):
            value = event[endpoint]
            if "date" in value:
                item[endpoint] = {"date": (date.fromisoformat(value["date"]) + shift).isoformat()}
            else:
                moment = _instant(value).astimezone(zone) + shift
                item[endpoint] = {"dateTime": moment.isoformat(), "timeZone": zone.key}
        item.update(
            {
                "id": f"{event['id']}_{index}",
                "recurringEventId": event["id"],
                "originalStartTime": item["start"],
            }
        )
        item.pop("recurrence", None)
        results.append(item)
    return results
