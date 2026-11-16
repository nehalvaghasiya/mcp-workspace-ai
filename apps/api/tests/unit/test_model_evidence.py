import json

from mcp_workspace_api.agents.model_evidence import evidence_json, paired_messages


def test_large_bodies_keep_all_five_sources_and_valid_json() -> None:
    records = [
        {
            "tool": "gmail.get_message",
            "data": {"id": str(i), "text": "x" * 50000, "body_text": "x" * 50000},
            "sources": [{"provider": "gmail", "resource_id": str(i)}],
        }
        for i in range(5)
    ]
    encoded = evidence_json(records, 20000)
    decoded = json.loads(encoded)
    assert len(encoded) <= 20000 and len(decoded) == 5
    assert [row["sources"][0]["resource_id"] for row in decoded] == [str(i) for i in range(5)]
    assert all(row["data"]["truncated"] and "text" not in row["data"] for row in decoded)


def test_incomplete_tool_pairs_are_not_sent_as_orphan_results() -> None:
    assistant = {"role": "assistant", "tool_calls": [{"id": "one"}]}
    result = {
        "role": "tool",
        "tool_call_id": "one",
        "content": json.dumps({"data": {"text": "Evidence"}}),
    }
    assert paired_messages([result]) == []
    assert paired_messages([assistant]) == []
    assert paired_messages([assistant, result]) == [assistant, result]


def test_oversized_structure_is_disclosed_instead_of_slicing_json() -> None:
    encoded = evidence_json([{"data": {str(i): "x" for i in range(5000)}}], 2000)
    assert len(encoded) <= 2000
    assert json.loads(encoded)[0]["truncated"]
