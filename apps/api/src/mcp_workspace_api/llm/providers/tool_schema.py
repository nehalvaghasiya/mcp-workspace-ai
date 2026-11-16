"""Adapt advisory tool-schema metadata without weakening server validation."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


def model_tool_schema(schema: dict[str, Any], tool_name: str = "") -> dict[str, Any]:
    result = deepcopy(schema)
    artifact = tool_name.startswith("artifact.create_")
    definitions = result.get("$defs", {})
    if artifact:
        format_name = tool_name.removeprefix("artifact.create_")
        target = result.get("properties", {}).get("request", result)
        if "$ref" in target:
            target = definitions.get(target["$ref"].rsplit("/", 1)[-1], target)
        properties = target.get("properties", {})
        if "format" in properties:
            properties["format"] = {"type": "string", "const": format_name}
        if format_name in {"pdf", "docx", "markdown", "html"}:
            properties.pop("sheets", None)
            properties.pop("slides", None)

    def visit(node: Any) -> None:
        if isinstance(node, list):
            for child in node:
                visit(child)
        elif isinstance(node, dict):
            # Some gateways turn named union references into wrapper objects
            # such as {"ParagraphBlock": {...}}. Inline the same constraints
            # so the model sees the actual wire shape, with no class labels.
            reference = node.get("$ref", "")
            if artifact and reference.startswith("#/$defs/"):
                definition = definitions.get(reference.rsplit("/", 1)[-1])
                if definition is not None:
                    siblings = {key: value for key, value in node.items() if key != "$ref"}
                    node.clear()
                    node.update(deepcopy(definition) | siblings)
            if artifact:
                node.pop("title", None)
            # OpenAPI's discriminator is a selection hint; oneOf/const/required
            # still describe the union, and the original Pydantic schema is
            # enforced again before any tool can execute.
            node.pop("discriminator", None)
            for name in (
                "properties",
                "definitions",
                "patternProperties",
                "dependentSchemas",
            ):
                mapping = node.get(name)
                if isinstance(mapping, dict):
                    for child in mapping.values():
                        visit(child)
            if not artifact:
                for child in node.get("$defs", {}).values():
                    visit(child)
            for name in (
                "items",
                "additionalProperties",
                "additionalItems",
                "contains",
                "if",
                "then",
                "else",
                "not",
                "propertyNames",
                "unevaluatedProperties",
                "unevaluatedItems",
                "oneOf",
                "anyOf",
                "allOf",
                "prefixItems",
            ):
                visit(node.get(name))

    visit(result)
    if artifact:
        result.pop("$defs", None)
    return result
