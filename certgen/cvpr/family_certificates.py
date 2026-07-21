"""Family-complete certificate execution with immutable coverage tracking."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from certgen.core.hashing import file_sha256
from certgen.cvpr.certificate import certify_feature_bundle
from certgen.cvpr.certificate_inputs import validate_bundle
from certgen.cvpr.contracts import atomic_write_json
from certgen.cvpr.registries import validate_family_record
from certgen.cvpr.study import require_frozen_study
from certgen.packaging.artifact_registry import append_artifact_entry, build_artifact_entry


def _json(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _family_file(path: str | Path) -> Path:
    source = Path(path)
    return source / "family.json" if source.is_dir() else source


def _require_pass(path: str | Path, *, label: str, key: str = "status", expected: str = "PASS") -> dict[str, Any]:
    payload = _json(path)
    if payload.get(key) != expected:
        raise ValueError(f"{label} must be {expected} before family certificates run")
    return payload


def _bundle_map(inputs_root: Path, study_hash: str, family: dict[str, Any]) -> dict[str, tuple[Path, dict[str, Any]]]:
    base = inputs_root / study_hash / str(family["family_id"])
    rows: dict[str, tuple[Path, dict[str, Any]]] = {}
    for sidecar_path in sorted(base.glob("**/sidecar.json")):
        sidecar = _json(sidecar_path)
        hypothesis_id = str(sidecar.get("hypothesis_id", ""))
        bundle_path = sidecar_path.with_name("certificate_inputs.npz")
        if not hypothesis_id:
            continue
        verdict = validate_bundle(
            bundle_path,
            study_hash=study_hash,
            family_hash=str(family["configuration_hash"]),
        )
        if not verdict["passed"]:
            raise ValueError(f"invalid certificate bundle {hypothesis_id}: " + "; ".join(verdict["errors"]))
        if hypothesis_id in rows:
            raise ValueError(f"duplicate certificate bundle for hypothesis: {hypothesis_id}")
        rows[hypothesis_id] = (bundle_path, sidecar)
    return rows


def _existing_certificate_valid(path: Path, *, hypothesis: dict[str, Any], sidecar: dict[str, Any], family: dict[str, Any]) -> bool:
    if not path.is_file():
        return False
    try:
        payload = _json(path)
    except (OSError, ValueError, json.JSONDecodeError):
        return False
    return (
        payload.get("hypothesis_id") == hypothesis.get("hypothesis_id")
        and payload.get("comparison_id") == hypothesis.get("comparison_id")
        and payload.get("feature_space") == hypothesis.get("feature_space")
        and payload.get("family_configuration_hash") == family.get("configuration_hash")
        and (payload.get("feature_cache_hashes") or {}).get("bundle") == sidecar.get("bundle_sha256")
        and payload.get("claim_allowed") is False
    )


def run_family_certificates(
    *,
    study_path: str | Path,
    family_path: str | Path,
    inputs_root: str | Path,
    reference_draw_plan: str | Path,
    metric_result: str | Path,
    sanity_result: str | Path,
    operational_status: str | Path,
    out_dir: str | Path = "data/results/cvpr/certificates",
    registry_path: str | Path = "data/artifact_registry.jsonl",
) -> dict[str, Any]:
    """Run every missing frozen-family certificate exactly once by lineage."""

    study = require_frozen_study(study_path)
    family_file = _family_file(family_path)
    family = _json(family_file)
    verdict = validate_family_record(family, require_frozen=True)
    if not verdict["passed"]:
        raise ValueError("family invalid: " + "; ".join(verdict["errors"]))
    if family.get("study_hash") != study.get("configuration_hash"):
        raise ValueError("family and study hashes differ")
    _require_pass(metric_result, label="metric reproduction")
    _require_pass(sanity_result, label="sanity controls")
    _require_pass(operational_status, label="family operational gate", expected="FAMILY_OPERATIONALLY_READY")

    bundles = _bundle_map(Path(inputs_root), study["configuration_hash"], family)
    expected = {str(row["hypothesis_id"]): row for row in family.get("hypotheses", [])}
    if set(bundles) != set(expected):
        raise ValueError(
            f"certificate bundle coverage mismatch: missing={sorted(set(expected)-set(bundles))}, "
            f"extra={sorted(set(bundles)-set(expected))}"
        )
    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)
    completed: list[dict[str, Any]] = []
    reused: list[str] = []
    for hypothesis_id in sorted(expected):
        hypothesis = expected[hypothesis_id]
        bundle_path, sidecar = bundles[hypothesis_id]
        output = target / f"{hypothesis_id}.json"
        if _existing_certificate_valid(output, hypothesis=hypothesis, sidecar=sidecar, family=family):
            reused.append(hypothesis_id)
        else:
            if output.exists():
                raise FileExistsError(f"existing certificate is stale or incompatible: {output}")
            result = certify_feature_bundle(
                study_path=study_path,
                family_path=family_file,
                feature_bundle_path=bundle_path,
                reference_draw_plan_path=reference_draw_plan,
                comparison_id=str(hypothesis["comparison_id"]),
                feature_space=str(hypothesis["feature_space"]),
                out_path=output,
                evidence_class="pilot_only",
                registry_path=registry_path,
            )
            if result.get("hypothesis_id") != hypothesis_id:
                raise AssertionError(f"certificate hypothesis identity mismatch: {hypothesis_id}")
        completed.append(
            {
                "hypothesis_id": hypothesis_id,
                "certificate": str(output),
                "certificate_sha256": file_sha256(output),
            }
        )
    coverage = {
        "schema_version": "certgen.cvpr.family_certificate_coverage.v1",
        "status": "FAMILY_CERTIFICATES_COMPLETE",
        "study_hash": study["configuration_hash"],
        "family_id": family["family_id"],
        "family_hash": family["configuration_hash"],
        "expected_hypotheses": len(expected),
        "completed_hypotheses": len(completed),
        "missing_hypotheses": [],
        "certificates": completed,
        "metric_result_sha256": file_sha256(metric_result),
        "sanity_result_sha256": file_sha256(sanity_result),
        "operational_status_sha256": file_sha256(operational_status),
        "claim_allowed": False,
    }
    coverage_path = target / "family_certificate_coverage.json"
    if coverage_path.exists():
        existing = _json(coverage_path)
        if existing != coverage:
            raise FileExistsError(f"refusing to overwrite non-identical family coverage: {coverage_path}")
    else:
        atomic_write_json(coverage, coverage_path)
    append_artifact_entry(
        build_artifact_entry(
            path=coverage_path,
            artifact_type="cvpr_family_certificate_coverage",
            stage="certificate",
            run_id=str(family["family_id"]),
            source=str(inputs_root),
            validation_status="family_certificates_complete",
            evidence_class="pilot_only",
            notes="All frozen hypotheses have one lineage-valid claim-ineligible certificate.",
        ),
        registry_path,
    )
    return {**coverage, "reused_hypotheses": reused}
