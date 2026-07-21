"""Operational-completeness gate for frozen CVPR multiplicity families."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Mapping

from certgen.core.hashing import stable_hash_json
from certgen.cvpr.contracts import atomic_write_json
from certgen.cvpr.certificate_inputs import _bundle_dir, _family_path, validate_bundle
from certgen.cvpr.registries import validate_family_record
from certgen.cvpr.study import require_frozen_study


def validate_family_operational(
    *,
    family_path: str | Path,
    study_path: str | Path,
    inputs_root: str | Path = "artifacts/cvpr/certificate_inputs",
    coverage_path: str | Path | None = None,
    out_path: str | Path | None = None,
    write_result: bool = True,
) -> dict[str, Any]:
    study = require_frozen_study(study_path)
    family_file = _family_path(family_path)
    family = json.loads(family_file.read_text(encoding="utf-8"))
    errors: list[str] = []
    family_verdict = validate_family_record(family, require_frozen=True)
    errors.extend(family_verdict["errors"])
    if family.get("study_hash") != study["configuration_hash"]:
        errors.append("family does not bind the frozen study hash")
    hypotheses = family.get("hypotheses") if isinstance(family.get("hypotheses"), list) else []
    identifiers = [str(row.get("hypothesis_id", "")) for row in hypotheses if isinstance(row, Mapping)]
    if len(identifiers) != len(hypotheses) or any(not value for value in identifiers):
        errors.append("every family hypothesis must have an ID")
    if len(identifiers) != len(set(identifiers)):
        errors.append("family contains duplicate hypothesis IDs")
    if len(hypotheses) != family.get("number_of_hypotheses"):
        errors.append("family hypothesis enumeration differs from declared size")
    if hypotheses and abs(
        float(family.get("alpha_per_hypothesis", 0.0))
        - float(family.get("alpha_total", 0.0)) / len(hypotheses)
    ) > 1e-15:
        errors.append("alpha allocation differs from family size")
    family_features = {str(row.get("feature_space")) for row in hypotheses}
    if family_features != set(map(str, family.get("feature_spaces", []))):
        errors.append("not all frozen feature spaces are represented")
    frozen_pairs = {
        str(row["comparison_id"])
        for row in study.get("model_pairs", [])
        if isinstance(row, Mapping)
    }
    family_pairs = {str(row.get("comparison_id")) for row in hypotheses}
    if family_pairs != frozen_pairs:
        errors.append(
            f"family comparison coverage differs from frozen study: missing={sorted(frozen_pairs-family_pairs)}, "
            f"extra={sorted(family_pairs-frozen_pairs)}"
        )
    controls = set(map(str, study.get("controls", [])))
    if family_pairs & controls:
        errors.append("sanity controls are present in the confirmatory family")
    if family.get("controls_in_confirmatory_family") is not False:
        errors.append("family does not explicitly exclude controls")
    if family.get("controls_claim_allowed") is not False:
        errors.append("family does not keep controls claim-ineligible")

    root = Path(inputs_root)
    family_root = root / study["configuration_hash"] / str(family.get("family_id"))
    rows: list[dict[str, Any]] = []
    expected_sidecars: set[Path] = set()
    for hypothesis in hypotheses:
        destination = _bundle_dir(root, study["configuration_hash"], family, hypothesis)
        sidecar_path = destination / "sidecar.json"
        expected_sidecars.add(sidecar_path.resolve())
        verdict = validate_bundle(
            destination / "certificate_inputs.npz",
            study_hash=study["configuration_hash"],
            family_hash=family.get("configuration_hash"),
        )
        blocker = "" if verdict["passed"] else "; ".join(verdict["errors"])
        if not verdict["passed"]:
            errors.extend(f"{hypothesis['hypothesis_id']}: {error}" for error in verdict["errors"])
            sidecar: dict[str, Any] = {}
        else:
            sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
            frozen_definition = study.get("feature_definitions", {}).get(hypothesis["feature_space"])
            if sidecar.get("frozen_feature_definition_hash") != stable_hash_json(frozen_definition):
                errors.append(f"{hypothesis['hypothesis_id']}: extractor/preprocessing differs from frozen declaration")
            if int(sidecar.get("budget", 0)) not in set(map(int, study.get("sample_budgets", []))):
                errors.append(f"{hypothesis['hypothesis_id']}: bundle budget is not frozen")
            if sidecar.get("claim_allowed") is not False:
                errors.append(f"{hypothesis['hypothesis_id']}: pre-execution bundle is claim-eligible")
        rows.append(
            {
                "family_id": family.get("family_id"),
                "hypothesis_id": hypothesis.get("hypothesis_id"),
                "comparison_type": hypothesis.get("comparison_id"),
                "feature_space": hypothesis.get("feature_space"),
                "budget": hypothesis.get("sample_budget"),
                "input_bundle": str(destination / "certificate_inputs.npz"),
                "bundle_valid": str(bool(verdict["passed"])).lower(),
                "certificate_status": "PENDING_REAL_EXECUTION",
                "ranking_edge_status": "PENDING_CERTIFICATE",
                "paper_eligible": "false",
                "blocker": blocker or "real certificate execution and all paper gates remain",
            }
        )
    actual_sidecars = {path.resolve() for path in family_root.rglob("sidecar.json")} if family_root.is_dir() else set()
    extras = sorted(str(path) for path in actual_sidecars - expected_sidecars)
    if extras:
        errors.append("extra unregistered certificate-input bundles: " + ", ".join(extras))
    if coverage_path is not None:
        target = Path(coverage_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else [
                "family_id", "hypothesis_id", "comparison_type", "feature_space", "budget",
                "input_bundle", "bundle_valid", "certificate_status", "ranking_edge_status",
                "paper_eligible", "blocker",
            ])
            writer.writeheader()
            writer.writerows(rows)
    result = {
        "status": "FAMILY_OPERATIONALLY_READY" if not errors else "FAMILY_OPERATIONALLY_BLOCKED",
        "passed": not errors,
        "family_id": family.get("family_id"),
        "study_hash": study["configuration_hash"],
        "hypotheses": len(hypotheses),
        "valid_bundles": sum(row["bundle_valid"] == "true" for row in rows),
        "errors": sorted(set(errors)),
        "coverage_path": str(coverage_path) if coverage_path is not None else None,
        "claim_allowed": False,
    }
    target = (
        Path(out_path)
        if out_path is not None
        else family_root / "family_operational_status.json"
    )
    if write_result:
        atomic_write_json(result, target)
    return {**result, "operational_artifact": str(target) if write_result else None}
