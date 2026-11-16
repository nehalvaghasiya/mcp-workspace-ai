"""Explicit live verification using synthetic model prompts and read-only Google calls."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError
from sqlalchemy import select

from mcp_workspace_api.core.execution_context import Runtime
from mcp_workspace_api.db import GoogleAccount, User
from mcp_workspace_api.llm.providers.completion_transport import completion

NATIVE = {
    "docs": ("application/vnd.google-apps.document", "docs.get_document", "document_id"),
    "sheets": (
        "application/vnd.google-apps.spreadsheet",
        "sheets.get_spreadsheet",
        "spreadsheet_id",
    ),
    "slides": (
        "application/vnd.google-apps.presentation",
        "slides.get_presentation",
        "presentation_id",
    ),
}


async def verify_live(runtime: Runtime, user_id: str = "") -> dict[str, Any]:
    settings = runtime.settings
    if settings.mode != "live" or settings.llm_provider != "openai_compatible":
        return {
            "status": "FAIL",
            "reason": "Live verification requires real Google and model providers",
        }
    report: dict[str, Any] = {"status": "PARTIAL", "model": {}, "google": {}}
    try:
        payload = await completion(
            settings.llm_base_url + "/chat/completions",
            settings.llm_api_key,
            {
                "model": settings.llm_model,
                "messages": [
                    {
                        "role": "user",
                        "content": "Reply with a brief greeting. This is a connection test with no account data.",
                    }
                ],
            },
        )
        content = payload["choices"][0]["message"].get("content")
        report["model"]["chat"] = "PASS" if isinstance(content, str) and content.strip() else "FAIL"
        function = {
            "name": "workspace_connection_check",
            "description": "A connection check with no side effects",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
        }
        payload = await completion(
            settings.llm_base_url + "/chat/completions",
            settings.llm_api_key,
            {
                "model": settings.llm_model,
                "messages": [
                    {
                        "role": "user",
                        "content": "Call workspace_connection_check with no arguments.",
                    }
                ],
                "tools": [{"type": "function", "function": function}],
                "tool_choice": {"type": "function", "function": {"name": function["name"]}},
                "parallel_tool_calls": False,
            },
        )
        calls = payload["choices"][0]["message"].get("tool_calls") or []
        report["model"]["tool_calling"] = (
            "PASS"
            if calls and calls[0].get("function", {}).get("name") == function["name"]
            else "FAIL"
        )
    except Exception as error:
        report["model"]["error"] = getattr(error, "code", "MODEL_INVALID_RESPONSE")
    with runtime.db.session() as session:
        users = list(session.scalars(select(User).where(User.deleted.is_(False))))
        users = [
            user
            for user in users
            if not user.subject.startswith("demo:") and (not user_id or user.id == user_id)
        ]
        if len(users) != 1:
            report["google"]["status"] = (
                "SIGN_IN_REQUIRED" if not users else "USER_SELECTION_REQUIRED"
            )
            return report
        owner = users[0].id
        account = session.scalar(select(GoogleAccount).where(GoogleAccount.user_id == owner))
        if not account:
            report["google"]["status"] = "CONNECT_GOOGLE_REQUIRED"
            return report
    for service, tool, arguments in (
        ("gmail", "gmail.search_messages", {"query": "in:anywhere", "max_results": 1}),
        ("calendar", "calendar.list_calendars", {"max_results": 1}),
        ("drive", "drive.search_files", {"query": "trashed = false", "max_results": 1}),
    ):
        try:
            result = await runtime.invoke(owner, tool, arguments)
            report["google"][service] = "PASS" if result.status == "success" else result.code
        except Exception as error:
            report["google"][service] = (
                "VERIFICATION_INPUT_ERROR"
                if isinstance(error, ValidationError)
                else getattr(error, "code", "PROVIDER_UNAVAILABLE")
            )
    for service, (mime, tool, field) in NATIVE.items():
        try:
            files = await runtime.invoke(
                owner,
                "drive.search_files",
                {"query": "trashed = false", "mime_types": [mime], "max_results": 1},
            )
            if files.status != "success":
                report["google"][service] = files.code
                continue
            found = files.data.get("files", [])
            if (
                not isinstance(found, list)
                or not found
                or not isinstance(found[0], dict)
                or not isinstance(found[0].get("id"), str)
            ):
                report["google"][service] = "NO_EXISTING_FILE_TO_VERIFY"
                continue
            identifier = found[0]["id"]
            result = await runtime.invoke(owner, tool, {field: identifier})
            report["google"][service] = "PASS" if result.status == "success" else result.code
        except Exception as error:
            report["google"][service] = (
                "VERIFICATION_INPUT_ERROR"
                if isinstance(error, ValidationError)
                else getattr(error, "code", "PROVIDER_UNAVAILABLE")
            )
    expected = [*report["model"].values(), *report["google"].values()]
    report["status"] = (
        "PASS" if expected and all(value == "PASS" for value in expected) else "PARTIAL"
    )
    return report
