from mcp_workspace_api.agents.evidence_cache import merge_read_evidence
from mcp_workspace_api.mcp.registry import tool_definitions


def test_read_evidence_survives_followups_and_refresh_replaces_the_same_record() -> None:
    definitions = tool_definitions("live")
    original = {"tool": "gmail.get_message", "data": {"id": "one", "text": "Original"}}
    cached = merge_read_evidence(definitions, [original], [])
    assert cached == [original]
    refreshed = {"tool": "gmail.get_message", "data": {"id": "one", "text": "Updated"}}
    other = {"tool": "drive.read_file", "data": {"id": "file", "text": "Document"}}
    assert merge_read_evidence(definitions, cached, [refreshed, other]) == [refreshed, other]


def test_effects_are_not_cached_and_old_read_evidence_is_bounded() -> None:
    definitions = tool_definitions("live")
    records = [{"tool": "gmail.get_message", "data": {"id": str(index)}} for index in range(30)]
    records.append({"tool": "gmail.create_draft", "data": {"draft_id": "created"}})
    cached = merge_read_evidence(definitions, [], records)
    assert len(cached) == 24 and cached[0]["data"]["id"] == "6"
    assert all(row["tool"] == "gmail.get_message" for row in cached)
