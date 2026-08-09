from __future__ import annotations

import base64
import io
import json
import zipfile
from pathlib import Path

import pytest
from PIL import Image

from certgen.icml2027.released_samples import build_manifest, import_archive, validate_archive


PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def _png(color: tuple[int, int, int]) -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (2, 2), color).save(output, format="PNG")
    return output.getvalue()


def _archive(path: Path, duplicate: bool = False) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        first = _png((255, 0, 0))
        archive.writestr("weird/name-a.png", first)
        archive.writestr("another/name-b.png", first if duplicate else _png((0, 0, 255)))


def test_secure_released_sample_validate_manifest_import(tmp_path: Path) -> None:
    archive = tmp_path / "samples.zip"
    _archive(archive)
    validation = validate_archive(archive, expected_count=2)
    assert validation["passed"]
    metadata = {
        "source_name": "synthetic_fixture",
        "source_type": "test_fixture",
        "source_url_or_repository": "local-fixture",
        "revision": "v1",
        "sampling_protocol": "fixture-only",
        "sampling_protocol_verified": False,
        "model_id": "fixture-model",
        "benchmark_id": "fixture-benchmark",
        "resolution": "1x1",
        "conditioning": "none",
        "class_balance": "not_applicable",
        "license_status": "synthetic_fixture_only",
        "redistribution_allowed": False,
        "provenance_notes": "not empirical evidence",
    }
    metadata_path = tmp_path / "metadata.json"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    manifest_path = tmp_path / "manifest.json"
    manifest = build_manifest(metadata_path, archive, manifest_path)
    assert manifest["sample_count"] == 2
    imported = import_archive(archive, manifest_path, tmp_path / "imported")
    assert imported["sample_count"] == 2
    assert imported["source_protocol_verified"] is False
    with pytest.raises(FileExistsError):
        import_archive(archive, manifest_path, tmp_path / "imported")


def test_released_sample_rejects_duplicates_and_traversal(tmp_path: Path) -> None:
    duplicate = tmp_path / "duplicate.zip"
    _archive(duplicate, duplicate=True)
    assert not validate_archive(duplicate)["passed"]
    traversal = tmp_path / "traversal.zip"
    with zipfile.ZipFile(traversal, "w") as archive:
        archive.writestr("../escape.png", PNG_1X1)
    result = validate_archive(traversal)
    assert not result["passed"]
    assert any("unsafe archive member" in error for error in result["errors"])
