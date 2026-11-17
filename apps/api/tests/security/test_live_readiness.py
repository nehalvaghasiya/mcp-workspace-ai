from __future__ import annotations

from typing import Any

import pytest
from mcp_workspace_api.db import Approval, GoogleAccount, Operation
from mcp_workspace_common.scopes import PREFIX, scope_options_satisfied
from sqlalchemy import select

from tests.support import Browser, LiveServer
from tests.support.security_actions import DRAFT, authorized_action, mcp_call


def test_readonly_drive_never_authorizes_file_writes() -> None:
    granted = [PREFIX + "drive.readonly"]
    assert scope_options_satisfied(granted, [PREFIX + "documents.readonly"])
    assert not scope_options_satisfied(granted, [PREFIX + "drive.file"])
    assert not scope_options_satisfied(granted, (), [(PREFIX + "documents",), (PREFIX + "drive",)])


async def test_approval_expiring_during_snapshot_causes_no_operation(
    live_server: LiveServer,
    browser: Browser,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import mcp_workspace_api.services.approval_service as approvals

    run_id, authorization = await authorized_action(
        live_server, browser.user_id, "gmail.create_draft", DRAFT
    )
    adapter = live_server.runtime.adapter(browser.user_id)
    original = adapter.snapshot
    moment = approvals.now()
    with live_server.runtime.db.session() as session:
        row = session.get(Approval, authorization["id"])
        assert row is not None
        row.expires_at = moment + 1

    async def expired_snapshot(*args: Any) -> dict[str, Any]:
        result = await original(*args)
        monkeypatch.setattr(approvals, "now", lambda: moment + 2)
        return result

    monkeypatch.setattr(adapter, "snapshot", expired_snapshot)
    result = await mcp_call(
        live_server, browser.user_id, "gmail.create_draft", DRAFT, run_id, authorization
    )
    assert result["code"] == "APPROVAL_EXPIRED"
    assert not adapter._load()["drafts"]
    with live_server.runtime.db.session() as session:
        assert (
            session.scalar(select(Operation).where(Operation.approval_id == authorization["id"]))
            is None
        )
        row = session.get(Approval, authorization["id"])
        assert row is not None and row.status == "approved"


async def test_connection_errors_are_sanitized_and_do_not_disable_connector(
    live_server: LiveServer,
    browser: Browser,
) -> None:
    vault = live_server.runtime.token_vault
    vault.record_connection_result(browser.user_id, "auth_required", "gmail")
    with live_server.runtime.db.session() as session:
        account = session.scalar(
            select(GoogleAccount).where(GoogleAccount.user_id == browser.user_id)
        )
        assert account is not None and "gmail" in account.enabled
        assert account.connection_error == "auth_required"
    vault.record_connection_result(browser.user_id, "PRIVATE_UNKNOWN_ERROR", "gmail")
    vault.record_connection_result(browser.user_id, None, "gmail")
    with live_server.runtime.db.session() as session:
        account = session.scalar(
            select(GoogleAccount).where(GoogleAccount.user_id == browser.user_id)
        )
        assert account is not None and account.connection_error == ""
        assert account.connector_errors == {}
        assert account.connection_checked_at is not None
