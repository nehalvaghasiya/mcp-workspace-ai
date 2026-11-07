# Calendar workflows

Ask “What do I have tomorrow afternoon?” The fixture clock is November 5, 2026 in America/Chicago. Inspect explicit dates and timezone in calendar.list_events results.

Ask “Give me 3 meeting slots next Wednesday.” calendar.query_freebusy grounds suggestions without booking. Inaccessible calendars are not treated as empty availability.

“Reschedule that meeting to 3” requires clarification when ambiguous. An explicit new time preserves the selected event's date/duration and still requires exact approval before calendar.update_event. See [workflow guidance](../../demo/walkthrough.md).
