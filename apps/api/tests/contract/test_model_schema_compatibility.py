from __future__ import annotations

import copy
import json

import httpx
import pytest
import respx
from mcp_documents.schemas.artifact_spec import ArtifactSpec
from mcp_workspace_api.db import User
from mcp_workspace_api.llm.providers.openai_compatible import cloud_step
from pydantic import ValidationError

from tests.support import Browser, LiveServer


async def test_full_catalog_works_with_provider_rejecting_discriminator_annotations(
    live_server: LiveServer,
    browser: Browser,
) -> None:
    runtime = live_server.runtime
    catalog = await runtime.catalog(browser.user_id)
    original = copy.deepcopy(catalog)
    assert '"discriminator":' in json.dumps(catalog)
    runtime.settings.llm_provider = "openai_compatible"
    runtime.settings.llm_base_url = "https://model.example.invalid/v1"
    runtime.settings.llm_model = "configured-model"
    runtime.settings.llm_api_key = "SYNTHETIC_KEY"
    with runtime.db.session() as session:
        user = session.get(User, browser.user_id)
        assert user is not None
        user.llm_consent = True
        user.consent_provider = runtime.settings.llm_base_url + ":configured-model"

    def provider(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        if '"discriminator":' in json.dumps(body["tools"]):
            return httpx.Response(
                400,
                json={"error": {"message": "Unknown name discriminator in function parameters"}},
            )
        assert '"oneOf":' in json.dumps(body["tools"])
        return httpx.Response(200, json={"choices": [{"message": {"content": "Hello!"}}]})

    with respx.mock() as router:
        router.post(runtime.settings.llm_base_url + "/chat/completions").mock(side_effect=provider)
        result = await cloud_step(runtime, browser.user_id, "hi", [], catalog)
    assert result["content"] == "Hello!"
    assert catalog == original
    with pytest.raises(ValidationError):
        ArtifactSpec.model_validate(
            {
                "format": "pdf",
                "title": "Test",
                "blocks": [{"type": "unsupported", "text": "Must stay invalid"}],
            }
        )


def test_provider_schema_keeps_property_names_and_literal_data() -> None:
    from mcp_workspace_api.llm.providers.tool_schema import model_tool_schema

    original = {
        "type": "object",
        "properties": {
            "discriminator": {"type": "string"},
            "payload": {
                "discriminator": {"propertyName": "kind"},
                "oneOf": [{"type": "object", "properties": {"kind": {"const": "one"}}}],
            },
        },
        "default": {"discriminator": "literal data"},
    }
    unchanged = copy.deepcopy(original)
    result = model_tool_schema(original)
    assert "discriminator" in result["properties"]
    assert "discriminator" not in result["properties"]["payload"]
    assert result["properties"]["payload"]["oneOf"] == original["properties"]["payload"]["oneOf"]
    assert result["default"] == original["default"]
    assert original == unchanged


def test_pdf_model_schema_omits_other_formats_without_changing_server_contract() -> None:
    from mcp_workspace_api.llm.providers.tool_schema import model_tool_schema

    original = ArtifactSpec.model_json_schema()
    projected = model_tool_schema(original, "artifact.create_pdf")
    assert projected["properties"]["format"]["const"] == "pdf"
    assert "sheets" not in projected["properties"] and "slides" not in projected["properties"]
    assert "Sheet" not in projected.get("$defs", {})
    assert "$defs" not in projected and '"$ref"' not in json.dumps(projected)
    assert "title" in projected["properties"]
    assert "oneOf" in projected["properties"]["blocks"]["items"]
    assert '"ParagraphBlock"' not in json.dumps(projected)
    assert "sheets" in original["properties"] and "const" not in original["properties"]["format"]
    validated = ArtifactSpec.model_validate(
        {
            "format": "pdf",
            "title": "Brief",
            "blocks": [{"type": "paragraph", "text": "Existing findings"}],
        }
    )
    assert validated.format == "pdf"
