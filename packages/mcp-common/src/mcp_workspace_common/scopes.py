from __future__ import annotations

from collections.abc import Iterable

GOOGLE_SERVICES = ("gmail", "calendar", "drive", "docs", "sheets", "slides")
PREFIX = "https://www.googleapis.com/auth/"
READ_SCOPES = {
    "gmail": (PREFIX + "gmail.readonly",),
    "calendar": (
        PREFIX + "calendar.events.readonly",
        PREFIX + "calendar.calendarlist.readonly",
        PREFIX + "calendar.freebusy",
    ),
    "drive": (PREFIX + "drive.readonly",),
    "docs": (PREFIX + "documents.readonly",),
    "sheets": (PREFIX + "spreadsheets.readonly",),
    "slides": (PREFIX + "presentations.readonly",),
}
WRITE_SCOPES = {
    "gmail": (PREFIX + "gmail.modify",),
    "calendar": (PREFIX + "calendar.events",),
    "drive": (PREFIX + "drive",),
    "docs": (PREFIX + "documents", PREFIX + "drive.file"),
    "sheets": (PREFIX + "spreadsheets", PREFIX + "drive.file"),
    "slides": (PREFIX + "presentations", PREFIX + "drive.file"),
}


def expanded_scopes(scopes: Iterable[str]) -> set[str]:
    granted = set(scopes)
    implications = {
        "gmail.modify": ("gmail.readonly", "gmail.compose", "gmail.send"),
        "gmail.compose": ("gmail.send",),
        "calendar.events": ("calendar.events.readonly",),
        "calendar.calendarlist": ("calendar.calendarlist.readonly",),
        "calendar.readonly": (
            "calendar.events.readonly",
            "calendar.calendarlist.readonly",
            "calendar.freebusy",
        ),
        "calendar": (
            "calendar.events",
            "calendar.events.readonly",
            "calendar.calendarlist.readonly",
            "calendar.calendarlist",
            "calendar.freebusy",
        ),
        "drive": (
            "drive.readonly",
            "drive.file",
            "drive.metadata.readonly",
            "drive.metadata",
            "documents",
            "documents.readonly",
            "spreadsheets",
            "spreadsheets.readonly",
            "presentations",
            "presentations.readonly",
        ),
        "drive.readonly": (
            "drive.metadata.readonly",
            "documents.readonly",
            "spreadsheets.readonly",
            "presentations.readonly",
        ),
        "documents": ("documents.readonly",),
        "spreadsheets": ("spreadsheets.readonly",),
        "presentations": ("presentations.readonly",),
    }
    for scope, includes in implications.items():
        if PREFIX + scope in granted:
            granted.update(PREFIX + included for included in includes)
    if "https://mail.google.com/" in granted:
        granted.update(
            PREFIX + name
            for name in ("gmail.readonly", "gmail.compose", "gmail.send", "gmail.modify")
        )
    return granted


def scope_options_satisfied(
    granted: Iterable[str], required: Iterable[str], alternatives: Iterable[Iterable[str]] = ()
) -> bool:
    expanded = expanded_scopes(granted)
    options = tuple(alternatives)
    return (
        any(set(option) <= expanded for option in options) if options else set(required) <= expanded
    )
