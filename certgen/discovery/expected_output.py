"""Exact current-run output discovery derived from the active input identity."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from certgen.discovery.classify import classify_package
from certgen.discovery.models import PackageRequirement, PackageType, SelectionStatus


ACTIVE_INPUT_BUNDLES = {
    "diagnostic": Path("artifacts/cvpr/kaggle_inputs/diagnostic/certgen_kaggle_environment_diagnostic_input.zip"),
    "preflight": Path("artifacts/cvpr/kaggle_inputs/preflight/certgen_cvpr_preflight_input.zip"),
}
OUTPUT_TYPES = {
    "diagnostic": PackageType.DIAGNOSTIC_OUTPUT,
    "preflight": PackageType.PREFLIGHT_OUTPUT,
    "generation": PackageType.GENERATION_OUTPUT,
    "features": PackageType.FEATURE_OUTPUT,
}
COMPLETION_STATUSES = {
    "diagnostic": ("KAGGLE_DIAGNOSTIC_PASS",),
    "preflight": ("PREFLIGHT_PASS",),
    "generation": ("GENERATION_COMPLETE", "VALIDATED_GENERATED_PILOT"),
    "features": ("FEATURE_EXTRACTION_SHARDS_COMPLETE",),
}


def active_input_candidate(root: str | Path, stage: str):  # type: ignore[no-untyped-def]
    base = Path(root).resolve()
    direct = ACTIVE_INPUT_BUNDLES.get(stage)
    if direct is not None and (base / direct).is_file():
        candidate = classify_package(base / direct)
        return candidate if candidate.valid else None
    package_root = base / "artifacts/cvpr/kaggle_inputs" / stage
    candidates = [classify_package(path) for path in sorted(package_root.rglob("*.zip"))] if package_root.is_dir() else []
    matches = [
        row
        for row in candidates
        if row.valid and row.identity.stage == stage and row.identity.package_type.value == f"{stage.upper()}_INPUT"
    ]
    return matches[0] if len(matches) == 1 else None


def expected_output_requirement(root: str | Path, stage: str) -> PackageRequirement | None:
    if stage not in OUTPUT_TYPES:
        raise ValueError(f"unsupported expected-output stage: {stage}")
    active = active_input_candidate(root, stage)
    if active is None:
        return None
    identity = active.identity
    return PackageRequirement(
        expected_package_type=OUTPUT_TYPES[stage],
        expected_stage=stage,
        expected_study_hash=identity.study_hash,
        expected_profile_id=identity.profile_id,
        expected_configuration_hash=identity.configuration_hash,
        expected_run_id=identity.run_id,
        expected_scale=identity.scale,
        expected_source_code_hash=identity.source_code_hash,
        expected_output_schema_version=identity.output_schema_version,
        expected_input_package_sha256=active.package_sha256,
        required_completion_status=COMPLETION_STATUSES[stage],
    )


def discover_expected_output(
    root: str | Path,
    stage: str,
    search_roots: Iterable[str | Path],
) -> dict[str, Any]:
    requirement = expected_output_requirement(root, stage)
    roots = tuple(Path(path).resolve(strict=False) for path in search_roots)
    if requirement is None:
        return {
            "schema_version": "certgen.discovery.expected_output.v1",
            "status": "NO_ACTIVE_INPUT_IDENTITY",
            "stage": stage,
            "search_roots": [str(path) for path in roots],
            "expected_identity": None,
            "candidate_count": 0,
            "candidates": [],
            "selected": None,
            "remediation": "Build and validate the current stage input package before selecting returned output.",
            "claim_allowed": False,
        }
    from certgen.discovery import discover_packages

    result = discover_packages(roots, requirement=requirement)
    payload = result.to_dict()
    payload.update(
        {
            "schema_version": "certgen.discovery.expected_output.v1",
            "stage": stage,
            "expected_identity": requirement.to_dict(),
            "candidate_count": len(result.candidates),
            "historical_valid_outputs_preserved": True,
            "stale_outputs_ignored": True,
            "claim_allowed": False,
        }
    )
    if result.status is SelectionStatus.DUPLICATE_IDENTICAL_COPY_DEDUPED:
        payload["status"] = "DUPLICATE_IDENTICAL_COPY_DEDUPED"
    elif result.status is SelectionStatus.AMBIGUOUS_DIFFERENT_CONTENT:
        payload["status"] = "AMBIGUOUS_DIFFERENT_CONTENT"
    return payload
