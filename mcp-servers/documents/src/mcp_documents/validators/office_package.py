from __future__ import annotations

import zipfile
from pathlib import Path, PurePosixPath

from defusedxml import ElementTree

from mcp_documents.constants import MAX_EXPANDED_BYTES, MAX_ZIP_MEMBERS
from mcp_documents.exceptions.artifact_error import ArtifactError


def check_package(path: Path, format: str) -> None:
    required = {
        "docx": "word/document.xml",
        "xlsx": "xl/workbook.xml",
        "pptx": "ppt/presentation.xml",
    }[format]
    with zipfile.ZipFile(path) as package:
        members = package.infolist()
        if (
            len(members) > MAX_ZIP_MEMBERS
            or sum(item.file_size for item in members) > MAX_EXPANDED_BYTES
        ):
            raise ArtifactError("Office package exceeds expanded ZIP limits")
        names = [member.filename for member in members]
        if (
            len(names) != len(set(names))
            or required not in names
            or "[Content_Types].xml" not in names
        ):
            raise ArtifactError("Invalid Office package structure")
        for member in members:
            name = PurePosixPath(member.filename)
            if name.is_absolute() or ".." in name.parts or "\\" in member.filename:
                raise ArtifactError("Unsafe ZIP member path")
            if member.flag_bits & 1 or member.file_size > 5 * 1024 * 1024:
                raise ArtifactError("Encrypted or oversized ZIP member")
            if member.file_size > max(1, member.compress_size) * 200:
                raise ArtifactError("Office package compression ratio exceeds limit")
            lowered = member.filename.casefold()
            if "vbaproject" in lowered or "/embeddings/" in lowered or "/activex/" in lowered:
                raise ArtifactError("Macros and embedded executable content are unsupported")
            content = package.read(member)
            if lowered.endswith((".xml", ".rels")):
                root = ElementTree.fromstring(content)
                for element in root.iter():
                    if element.attrib.get("TargetMode", "").casefold() == "external":
                        raise ArtifactError("External Office relationships are unsupported")
            if lowered == "[content_types].xml" and b"macroenabled" in content.lower():
                raise ArtifactError("Macro-enabled Office documents are unsupported")
