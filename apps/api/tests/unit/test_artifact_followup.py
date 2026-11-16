from mcp_workspace_api.agents.artifact_followup import artifact_followup_format

HISTORY = [{"role": "assistant", "content": "The prioritized findings and their sources."}]


def test_local_conversion_has_one_explicit_format_and_existing_content() -> None:
    assert (
        artifact_followup_format(
            "Create a downloadable local PDF brief from this action list", HISTORY
        )
        == "pdf"
    )
    assert artifact_followup_format("Turn these findings into a Word report", HISTORY) == "docx"
    assert artifact_followup_format("Create a PDF from this action list", []) is None


def test_new_retrieval_native_google_and_ambiguous_formats_are_not_forced() -> None:
    for prompt in [
        "Review new emails and create a PDF from these findings",
        "Create a Google Doc from this action list",
        "Create PDF and Excel from this action list",
        "Explain PDF formats",
    ]:
        assert artifact_followup_format(prompt, HISTORY) is None
