"""Behavioral regressions for demo grounding, limits, retention and replay."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest
from mcp_documents.artifacts import ArtifactEngine, ArtifactSpec
from mcp_workspace_api.agents import artifact_content, demo_range, fake_plan, summarize
from mcp_workspace_api.core.security import Denied
from mcp_workspace_api.db import Artifact, Conversation, Run, User, now
from sqlalchemy import select


def test_demo_relative_dates_use_frozen_clock_and_requested_daypart() -> None:
    assert demo_range("tomorrow afternoon") == (
        "2026-11-06T12:00:00-06:00",
        "2026-11-06T18:00:00-06:00",
    )
    assert demo_range("next Wednesday") == (
        "2026-11-11T00:00:00-06:00",
        "2026-11-12T00:00:00-06:00",
    )


def test_missing_recipients_and_ambiguous_meetings_require_clarification() -> None:
    for prompt in ("Send email", "Reschedule that meeting to 3"):
        with pytest.raises(Denied, match="recipient|meeting"):
            fake_plan(prompt, {})


def test_explicit_csv_tracker_does_not_generate_unrequested_workbook() -> None:
    assert [step["tool"] for step in fake_plan("Create a CSV tracker", {})] == [
        "artifact.create_csv"
    ]


def test_freebusy_suggestions_are_grounded_and_never_infer_inaccessible_calendars() -> None:
    result = {
        "data": {
            "time_min": "2026-11-11T09:00:00-06:00",
            "time_max": "2026-11-11T12:00:00-06:00",
            "calendars": {
                "primary": {
                    "busy": [
                        {"start": "2026-11-11T09:00:00-06:00", "end": "2026-11-11T10:00:00-06:00"}
                    ]
                }
            },
        }
    }
    answer = summarize([result])
    assert "10:00:00-06:00" in answer and "not booked" in answer
    assert "09:00:00-06:00 –" not in answer
    result["data"]["calendars"]["primary"]["errors"] = [{"reason": "permission_denied"}]
    assert "incomplete" in summarize([result])
    assert "suggestions" not in summarize([result])


@pytest.mark.parametrize("format", ["docx", "pdf", "xlsx", "pptx"])
def test_report_formats_reuse_retrieved_facts_and_source_ids(format: str, tmp_path: Path) -> None:
    evidence = [
        {
            "data": {
                "id": "proposal",
                "text": "Budget is $24000. Alex owns checklist; Jordan owns tests.",
            },
            "sources": [
                {"provider": "drive", "resource_id": "proposal", "title": "Launch proposal"}
            ],
        }
    ]
    payload = artifact_content({"format": format, "title": "Launch report"}, evidence)
    spec = ArtifactSpec.model_validate(payload)
    rendered = ArtifactEngine().create(spec, tmp_path)
    assert rendered.validation["semantic_readback"] is True
    encoded = spec.model_dump_json()
    assert "proposal" in encoded
    if format == "xlsx":
        assert spec.sheets[0].columns[:2] == ["Task", "Owner"]
        assert spec.sheets[0].rows[0][1].value == "Alex"
        assert spec.sheets[0].rows[0][2].value == ""
    else:
        assert "$24000" in encoded


async def test_artifact_quotas_do_not_publish_orphan_files(live_server: Any, browser: Any) -> None:
    live_server.settings.max_user_artifacts = 1
    conversation, first = await browser.start("Create a PDF report")
    assert (await browser.wait(conversation, first))["status"] == "completed"
    _, second = await browser.start("Create a Word report", conversation)
    result = await browser.wait(conversation, second)
    assert result["status"] == "failed" and "quota" in result["error"]
    artifacts = (await browser.http.get("/api/artifacts")).json()
    assert len(artifacts) == 1
    assert len(list((live_server.settings.storage / "artifacts" / browser.user_id).iterdir())) == 1


async def test_retention_removes_expired_conversations_and_artifacts(
    live_server: Any, browser: Any
) -> None:
    conversation, run_id = await browser.start("Create a PDF report")
    assert (await browser.wait(conversation, run_id))["status"] == "completed"
    with live_server.runtime.db.session() as session:
        row = session.get(Conversation, conversation)
        row.updated_at = now() - 31 * 86400
    future = asyncio.run_coroutine_threadsafe(
        live_server.app.state.prune_expired(), live_server.app.state.loop
    )
    result = await asyncio.wrap_future(future)
    assert result["conversations_removed"] == 1
    assert (await browser.http.get(f"/api/conversations/{conversation}")).status_code == 404
    assert (await browser.http.get("/api/artifacts")).json() == []


async def test_deleted_account_does_not_retain_profile_or_private_state(
    live_server: Any, browser: Any
) -> None:
    with live_server.runtime.db.session() as session:
        user = session.get(User, browser.user_id)
        user.email, user.display_name = "private@example.invalid", "Private profile"
    assert (await browser.http.delete("/api/account")).status_code == 200
    with live_server.runtime.db.session() as session:
        user = session.get(User, browser.user_id)
        assert user.deleted and not user.email and user.display_name == "Deleted user"
        assert user.subject == "deleted:" + user.id
        assert not list(session.scalars(select(Run).where(Run.user_id == user.id)))
        assert not list(session.scalars(select(Artifact).where(Artifact.user_id == user.id)))


def test_rescheduling_preserves_selected_date_duration_and_requires_unambiguous_time() -> None:
    previous = {
        "references": {
            "event": "event-001",
            "event_start": "2026-11-05T14:00:00-06:00",
            "event_end": "2026-11-05T15:00:00-06:00",
        }
    }
    with pytest.raises(Denied, match="AM/PM"):
        fake_plan("Reschedule that meeting to 3", previous)
    steps = fake_plan("Reschedule that meeting to 3 PM", previous)
    update = next(step for step in steps if step["tool"] == "calendar.update_event")
    assert update["arguments"]["changes"]["start"] == "2026-11-05T15:00:00-06:00"
    assert update["arguments"]["changes"]["end"] == "2026-11-05T16:00:00-06:00"
