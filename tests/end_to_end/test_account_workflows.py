from __future__ import annotations

import httpx

from tests.support import Browser, LiveServer
from tests.support.api_actions import stage_action


async def test_rejected_and_cancelled_actions_have_zero_effects(
    live_server: LiveServer, browser: Browser
) -> None:
    before = live_server.runtime.adapter(browser.user_id)._load()
    conversation, run_id = await browser.start(
        "Draft a reply to Alex with the launch decisions, do not send"
    )
    run = await browser.wait(conversation, run_id)
    assert run["status"] == "needs_approval", run
    approvals = (await browser.http.get("/api/approvals")).json()
    approval = next(item for item in approvals if item["run_id"] == run_id)
    assert approval["tool"] == "gmail.create_draft"
    assert approval["arguments"]["to"] == ["alex@example.invalid"]
    assert live_server.runtime.adapter(browser.user_id)._load() == before
    rejected = await browser.http.post(
        f"/api/approvals/{approval['id']}/decide", json={"decision": "reject"}
    )
    assert rejected.status_code == 200
    assert (await browser.wait(conversation, run_id))["status"] == "cancelled"
    assert live_server.runtime.adapter(browser.user_id)._load() == before
    assert (
        await browser.http.post(
            f"/api/approvals/{approval['id']}/decide", json={"decision": "approve"}
        )
    ).status_code == 409
    conversation, run_id = await browser.start("Create an event on the calendar")
    assert (await browser.wait(conversation, run_id))["status"] == "needs_approval"
    pending = next(
        item
        for item in (await browser.http.get("/api/approvals")).json()
        if item["run_id"] == run_id
    )
    assert (await browser.http.post(f"/api/runs/{run_id}/cancel")).status_code == 200
    assert (
        await browser.http.post(
            f"/api/approvals/{pending['id']}/decide", json={"decision": "approve"}
        )
    ).status_code == 409
    assert live_server.runtime.adapter(browser.user_id)._load() == before


async def test_owner_isolation_for_conversation_artifact_trace_approval_and_headers(
    live_server: LiveServer, browser: Browser
) -> None:
    conversation, run_id = await browser.start("Create a PDF summary of launch emails")
    assert (await browser.wait(conversation, run_id))["status"] == "completed"
    artifact = (await browser.http.get("/api/artifacts")).json()[0]
    _, _, approval_id = await stage_action(
        live_server, browser, "drive.create_folder", {"name": "Private folder"}
    )
    async with live_server.browser() as other:
        assert other.user_id != browser.user_id
        assert (await other.http.get("/api/conversations")).json() == []
        assert (await other.http.get("/api/artifacts")).json() == []
        assert (await other.http.get("/api/approvals")).json() == []
        for path in (
            f"/api/conversations/{conversation}",
            f"/api/runs/{run_id}/trace",
            f"/api/runs/{run_id}/events",
            f"/api/artifacts/{artifact['id']}",
            artifact["download_url"],
        ):
            response = await other.http.get(path, headers={"X-User-ID": browser.user_id})
            assert response.status_code == 404, response.text
        response = await other.http.post(
            f"/api/approvals/{approval_id}/decide", json={"decision": "approve"}
        )
        assert response.status_code == 404


async def test_auth_csrf_origin_and_security_headers(
    live_server: LiveServer, browser: Browser
) -> None:
    async with httpx.AsyncClient(base_url=live_server.url) as anonymous:
        assert (await anonymous.get("/api/artifacts")).status_code == 401
        assert (await anonymous.post("/api/conversations", json={})).status_code == 401
    for headers in (
        {"X-CSRF-Token": ""},
        {"X-CSRF-Token": "wrong"},
        {"Origin": "https://attacker.invalid"},
        {"Sec-Fetch-Site": "cross-site"},
    ):
        response = await browser.http.post(
            "/api/conversations", json={"title": "Rejected"}, headers=headers
        )
        assert response.status_code == 403
    assert (await browser.http.get("/api/conversations")).json() == []
    response = await browser.http.get("/api/session")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.json()["mode"] == "mock"


async def test_disabled_connector_is_removed_from_authorized_catalog_and_chat_fails(
    browser: Browser,
) -> None:
    assert (
        await browser.http.patch("/api/connectors/gmail", json={"enabled": False})
    ).status_code == 200
    catalog = (await browser.http.get("/api/mcp/tools")).json()
    assert all(not tool["enabled"] for tool in catalog if tool["server"] == "gmail")
    conversation, run_id = await browser.start("Summarize launch emails")
    run = await browser.wait(conversation, run_id)
    assert run["status"] == "failed"
    assert (await browser.http.get(f"/api/runs/{run_id}/trace")).json() == []


async def test_prompt_injection_in_sources_cannot_authorize_writes(
    live_server: LiveServer, browser: Browser
) -> None:
    before = live_server.runtime.adapter(browser.user_id)._load()
    conversation, run_id = await browser.start("Summarize launch emails and the Drive proposal")
    run = await browser.wait(conversation, run_id)
    assert run["status"] == "completed", run
    assert (await browser.http.get("/api/approvals")).json() == []
    assert live_server.runtime.adapter(browser.user_id)._load() == before
    trace = (await browser.http.get(f"/api/runs/{run_id}/trace")).json()
    assert all(
        not live_server.runtime.policy.needs_approval(live_server.runtime.tools[entry["tool"]])
        for entry in trace
    )


async def test_conversation_deletion_removes_derived_artifacts_and_history(
    browser: Browser,
) -> None:
    conversation, run_id = await browser.start("Make a PDF summary of launch emails")
    assert (await browser.wait(conversation, run_id))["status"] == "completed"
    artifact = (await browser.http.get("/api/artifacts")).json()[0]
    assert (await browser.http.delete(f"/api/conversations/{conversation}")).status_code == 200
    assert (await browser.http.get(f"/api/conversations/{conversation}")).status_code == 404
    assert (await browser.http.get(artifact["download_url"])).status_code == 404
    assert (await browser.http.get("/api/artifacts")).json() == []
