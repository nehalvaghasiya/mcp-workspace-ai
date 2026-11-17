from mcp_workspace_api.agents.model_catalog import model_catalog

CATALOG = [
    {"name": name, "enabled": True}
    for name in [
        "gmail.search_messages",
        "gmail.get_messages",
        "calendar.list_events",
        "drive.search_files",
        "artifact.create_pdf",
    ]
]


def test_email_requests_keep_only_relevant_schemas_until_full_reads_complete() -> None:
    prompt = "Summarize my five most recent inbox emails"
    selected = [
        {"tool": "gmail.search_messages", "data": {"messages": [{"id": "one"}, {"id": "two"}]}}
    ]
    assert {row["name"] for row in model_catalog(CATALOG, prompt, [], selected, [])} == {
        "gmail.search_messages",
        "gmail.get_messages",
    }
    selected.append({"tool": "gmail.get_messages", "data": {"messages": [{"id": "one"}]}})
    assert model_catalog(CATALOG, prompt, [], selected, [])
    selected[-1]["data"]["messages"].append({"id": "two"})
    assert model_catalog(CATALOG, prompt, [], selected, []) == []
    assert model_catalog(CATALOG, "2", [{"role": "user", "content": prompt}], selected, []) == []


def test_cross_service_requests_and_ambiguous_requests_keep_needed_capabilities() -> None:
    names = {
        row["name"]
        for row in model_catalog(
            CATALOG,
            "Review inbox emails, calendar meetings and Drive files; create a PDF",
            [],
            [],
            [],
        )
    }
    assert names == {row["name"] for row in CATALOG}
    assert model_catalog(CATALOG, "Help organize my work", [], [], []) == CATALOG
    assert model_catalog(
        CATALOG,
        "Summarize emails and draft a reply",
        [],
        [{"tool": "gmail.search_messages", "data": {"messages": []}}],
        [],
    )
