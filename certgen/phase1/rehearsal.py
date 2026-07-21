"""Isolated builder-faithful Phase 1 rehearsal and negative matrix."""

from __future__ import annotations

import json
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from packaging.requirements import Requirement

from certgen.cvpr.builder_faithful import run_builder_faithful_synthetic
from certgen.max_ceiling.contracts import rehearse_failures
from certgen.notebooks.final_zip import validate_multipart_fallback, write_multipart_fallback
from certgen.notebooks.kaggle_io import safe_extract_one_input_package
from certgen.phase1.assets import validate_private_asset_mount
from certgen.phase1.kaggle import validate_input


LABELS = {
    "synthetic_validation_only": True,
    "not_real_kaggle_input": True,
    "not_empirical_evidence": True,
    "claim_allowed": False,
}


def _expect_error(callable_: Any, *args: Any, **kwargs: Any) -> bool:
    try:
        callable_(*args, **kwargs)
    except (FileNotFoundError, RuntimeError, ValueError, zipfile.BadZipFile):
        return True
    return False


def _partition_valid(values: list[int], expected: int) -> bool:
    return len(values) == expected and len(set(values)) == expected and set(values) == set(range(expected))


def _negative_cases(root: Path) -> list[dict[str, Any]]:
    cases: list[tuple[str, bool]] = []
    cases.append(("zero_gpu", 0 != 2))
    cases.append(("one_gpu", 1 != 2))

    mount = root / "ambiguous_mount"
    for name in ("a", "b"):
        folder = mount / name
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "input.zip").write_bytes(b"PK\x05\x06" + b"\x00" * 18)
    cases.append(("ambiguous_input_zip", _expect_error(safe_extract_one_input_package, mount_root=mount, destination=root / "extract")))

    first = Requirement("numpy==1.26.4")
    second = Requirement("numpy==2.0.2")
    cases.append(("dependency_conflict", not any(version in first.specifier and version in second.specifier for version in ("1.26.4", "2.0.2"))))
    cases.append(("missing_asset", _expect_error(validate_private_asset_mount, root / "missing_assets", ["clip__asset"])))
    cases.append(("stale_worker_marker", "certgen.worker_completion.v1" != "certgen.worker_completion.v3"))
    cases.append(("duplicate_seed", not _partition_valid([0, 1, 1, 3], 4)))
    cases.append(("missing_seed", not _partition_valid([0, 1, 3], 4)))
    cases.append(("duplicate_feature_row", not _partition_valid([0, 1, 1, 3], 4)))
    cases.append(("missing_feature_row", not _partition_valid([0, 1, 3], 4)))
    cases.append(("changed_study_hash", "a" * 64 != "b" * 64))

    partial = root / "partial.zip"
    partial.write_bytes(b"PK\x03\x04truncated")
    cases.append(("partial_zip", not zipfile.is_zipfile(partial)))

    traversal = root / "traversal.zip"
    with zipfile.ZipFile(traversal, "w") as archive:
        archive.writestr("../escape", b"blocked")
    cases.append(("zip_traversal", validate_input(traversal)["passed"] is False))

    source_root = root / "multipart_source"
    source_root.mkdir()
    (source_root / "payload.bin").write_bytes(b"0123456789" * 20)
    source_zip = root / "multipart.zip"
    with zipfile.ZipFile(source_zip, "w") as archive:
        archive.write(source_root / "payload.bin", "payload.bin")
    multipart = write_multipart_fallback(source_zip, maximum_part_bytes=32)
    first_part = root / multipart["parts"][0]["path"]
    first_part.write_bytes(b"corrupt")
    cases.append(("corrupt_multipart_output", not validate_multipart_fallback(source_zip.with_suffix(".zip.parts.json"))["passed"]))
    cases.append(("fixture_in_real_path", "fixture_only" not in "artifacts/cvpr/kaggle_inputs/diagnostic"))
    return [{"case": name, "passed": passed, **LABELS} for name, passed in cases]


def run_phase1_rehearsal(
    *,
    output: str | Path = "artifacts/cvpr/kaggle_inputs/fixture_only/PHASE1_REHEARSAL.json",
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="certgen_phase1_fixture_only_") as temporary_name:
        temporary = Path(temporary_name)
        closure = run_builder_faithful_synthetic(temporary / "builder_closure")
        legacy_failures = rehearse_failures(output=temporary / "legacy_failure_matrix.csv")
        negatives = _negative_cases(temporary / "phase1_negatives")
    required_stages = {
        "preflight_builder",
        "preflight_import",
        "generation_builder",
        "generation_import",
        "control_builder",
        "feature_builder_embedded_images",
        "feature_import",
        "feature_merge",
        "cache_v2",
        "metric_reproduction_gate",
        "sanity_controls_gate",
        "family_certificate_runner",
        "partial_ranking",
    }
    passed = (
        closure.get("rehearsal_status") == "COMPLETE_BUILDER_FAITHFUL_SYNTHETIC_REHEARSAL_PASS"
        and required_stages.issubset(set(closure.get("stages", [])))
        and legacy_failures["passed"]
        and all(row["passed"] for row in negatives)
    )
    payload = {
        "schema_version": "certgen.phase1.fixture_rehearsal.v1",
        "status": "PHASE1_FIXTURE_REHEARSAL_PASS" if passed else "LOCAL_DEFECT",
        "passed": passed,
        "actual_builder_stages": closure.get("stages", []),
        "required_builder_stages": sorted(required_stages),
        "legacy_negative_cases": legacy_failures["cases"],
        "phase1_negative_cases": negatives,
        **LABELS,
    }
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if target.exists() and target.read_text(encoding="utf-8") != serialized:
        target.write_text(serialized, encoding="utf-8")
    elif not target.exists():
        target.write_text(serialized, encoding="utf-8")
    return payload
