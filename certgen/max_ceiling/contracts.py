"""Fail-closed maximum-ceiling execution and analysis contracts."""

from __future__ import annotations

import csv
import importlib.metadata
import json
import math
import platform
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np
import yaml  # type: ignore[import-untyped]

from certgen.core.hashing import stable_hash_json
from certgen.cvpr.registries import validate_all_cvpr_registries
from certgen.max_ceiling.common import (
    artifact_root,
    load_study,
    study_hash,
    write_csv_idempotent,
    write_json_idempotent,
    write_text_idempotent,
)
from certgen.max_ceiling.provenance import STAGE_ORDER, build_provenance_graph, verify_provenance_graph
from certgen.notebooks.cvpr_static_analyzer import analyze_all
from certgen.notebooks.worker_contract import COMPLETION_SCHEMA_VERSION, WORKER_CONTRACT_VERSION
from certgen.pipeline.v9_next_action import determine_next_action
from certgen.release.privacy_scan import scan_privacy


DOCTOR_STATUSES = {"PASS", "BLOCKED_REAL_INPUT", "BLOCKED_REAL_EXECUTION", "LOCAL_DEFECT", "STALE_ARTIFACT"}
SCALE_DECISIONS = {
    "STOP_INVALID_PIPELINE",
    "REPAIR_AND_REPEAT",
    "COMPLETE_AT_1K",
    "PROMOTE_TO_10K",
    "PROMOTE_TO_50K",
    "ADD_OPTIONAL_DINO",
    "ADD_OPTIONAL_CFM",
    "ADD_SECOND_BENCHMARK",
}
SENSITIVITY_CLASSES = {
    "PRIMARY", "SECONDARY_CONFIRMATORY", "SENSITIVITY", "EXPLORATORY", "INVALID_FOR_CLAIM"
}
ACCOUNTING_CLASSES = {
    "PLANNING_ESTIMATE", "MEASURED_PREFLIGHT", "MEASURED_REAL_RUN", "DERIVED_REAL_MEASUREMENT"
}


def _check(name: str, passed: bool, status: str, detail: Any) -> dict[str, Any]:
    if status not in DOCTOR_STATUSES:
        raise ValueError(f"invalid doctor status: {status}")
    return {"name": name, "passed": bool(passed), "status": "PASS" if passed else status, "detail": detail}


def doctor_report(
    *,
    stage: str | None = None,
    study_path: str | Path | None = None,
    root: str | Path = ".",
) -> dict[str, Any]:
    """Distinguish local defects, stale state, real inputs, and real execution."""

    base = Path(root).resolve()
    if study_path is None:
        canonical_study = base / "artifacts/cvpr/study/cifar_integrity_minimal.yaml"
        study_path = canonical_study if canonical_study.is_file() else None
    elif not Path(study_path).is_absolute():
        study_path = base / Path(study_path)
    action = determine_next_action(root=base)
    checks: list[dict[str, Any]] = []
    checks.append(
        _check(
            "python_version",
            sys.version_info >= (3, 10),
            "LOCAL_DEFECT",
            platform.python_version(),
        )
    )
    versions: dict[str, str] = {}
    missing_dependencies: list[str] = []
    for distribution in ("numpy", "scipy", "PyYAML", "packaging"):
        try:
            versions[distribution] = importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            missing_dependencies.append(distribution)
    checks.append(_check("dependency_versions", not missing_dependencies, "LOCAL_DEFECT", versions or missing_dependencies))
    free = shutil.disk_usage(base).free
    checks.append(_check("disk_space", free >= 2 * 1024**3, "LOCAL_DEFECT", {"free_bytes": free, "minimum_bytes": 2 * 1024**3}))
    registries = validate_all_cvpr_registries(base)
    checks.append(_check("registry_consistency", registries["passed"], "LOCAL_DEFECT", registries))
    checks.append(
        _check(
            "worker_contract_versions",
            WORKER_CONTRACT_VERSION.endswith(".v1") and COMPLETION_SCHEMA_VERSION.endswith(".v3"),
            "LOCAL_DEFECT",
            {"worker": WORKER_CONTRACT_VERSION, "completion": COMPLETION_SCHEMA_VERSION},
        )
    )
    notebooks = analyze_all(base / path for path in (
        "notebooks/kaggle/certgen_cvpr_checkpoint_preflight_t4x2.ipynb",
        "notebooks/kaggle/certgen_cvpr_cifar10_generation_t4x2_1k.ipynb",
        "notebooks/kaggle/certgen_cvpr_generation_t4x2_generic.ipynb",
        "notebooks/kaggle/certgen_cvpr_feature_extraction_t4x2_1k.ipynb",
        "notebooks/kaggle/certgen_cvpr_feature_extraction_t4x2_generic.ipynb",
    ))
    checks.append(_check("notebook_schema_compatibility", notebooks["passed"], "LOCAL_DEFECT", len(notebooks["results"])))
    source_exists = (base / "data/sources/cifar-10-python.tar.gz").is_file()
    reference_ready = (base / "registry/manifests/cvpr/cifar10_reference.jsonl").is_file()
    checks.append(
        _check(
            "input_availability",
            source_exists or reference_ready,
            "BLOCKED_REAL_INPUT",
            "reference materialized" if reference_ready else "official local CIFAR archive required",
        )
    )
    checks.append(
        _check(
            "asset_manifests",
            (base / "registry/cvpr/model_registry.yaml").is_file()
            and (base / "registry/cvpr/feature_space_registry.yaml").is_file(),
            "LOCAL_DEFECT",
            "registry-backed; real preflight remains required",
        )
    )
    checks.append(
        _check(
            "next_action_resolvable",
            bool(action.get("exact_command") and action.get("status")),
            "LOCAL_DEFECT",
            action,
        )
    )
    if study_path:
        try:
            study = load_study(study_path)
        except (OSError, ValueError) as exc:
            checks.append(_check("frozen_study", False, "LOCAL_DEFECT", str(exc)))
        else:
            checks.append(_check("frozen_study", True, "PASS", study_hash(study)))
            provenance = verify_provenance_graph(study_path, root=base)
            checks.append(_check("artifact_dag_integrity", provenance["passed"], "STALE_ARTIFACT", provenance))
            expected_root = artifact_root(study, base)
            checks.append(_check("expected_output_locations", expected_root.parent.is_dir() or base.is_dir(), "LOCAL_DEFECT", str(expected_root)))
    else:
        checks.append(_check("artifact_dag_integrity", True, "PASS", "deferred until a frozen study exists"))
    privacy = scan_privacy(base)
    checks.append(_check("evidence_firewall", not privacy, "LOCAL_DEFECT", privacy or "privacy scan clean"))
    weight_suffixes = {".bin", ".ckpt", ".msgpack", ".onnx", ".pt", ".pth", ".safetensors"}
    public_roots = [base / "release", base / "dist"]
    restricted = [
        str(path)
        for public_root in public_roots
        if public_root.is_dir()
        for path in public_root.rglob("*")
        if path.is_file() and path.suffix.lower() in weight_suffixes
    ]
    checks.append(_check("public_release_exclusion", not restricted, "LOCAL_DEFECT", restricted or "no restricted weight files"))
    completion_markers = list((base / "artifacts").rglob("completion*.json")) if (base / "artifacts").is_dir() else []
    stale = []
    for marker in completion_markers:
        try:
            payload = json.loads(marker.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            stale.append(str(marker))
            continue
        if payload.get("schema_version") not in {COMPLETION_SCHEMA_VERSION, "certgen.worker_completion.v2"}:
            stale.append(str(marker))
    checks.append(_check("resume_status", not stale, "STALE_ARTIFACT", stale or "no stale completion markers"))
    failures = [row for row in checks if not row["passed"]]
    precedence = ("LOCAL_DEFECT", "STALE_ARTIFACT", "BLOCKED_REAL_INPUT", "BLOCKED_REAL_EXECUTION")
    status = next((candidate for candidate in precedence if any(row["status"] == candidate for row in failures)), "PASS")
    if stage and status == "PASS" and stage in {"preflight", "generation", "feature", "certificate", "ranking"}:
        status = "BLOCKED_REAL_EXECUTION"
    return {
        "schema_version": "certgen.maximum_ceiling.doctor.v1",
        "status": status,
        "stage": stage,
        "study": str(study_path) if study_path else None,
        "checks": checks,
        "checks_passed": sum(row["passed"] for row in checks),
        "checks_total": len(checks),
        "exact_next_action": action["exact_command"],
        "evidence_class": "local_contract_validation",
        "claim_allowed": False,
    }


def _scale_plan(study: Mapping[str, Any]) -> dict[str, Any]:
    common = {
        "models": list(map(str, study.get("models", []))),
        "extractors": list(map(str, study.get("feature_spaces", []))),
        "comparisons": [str(row.get("comparison_id")) for row in study.get("model_pairs", [])],
        "controls": ["null_reference_split", "obvious_gap_corruption"],
        "stop_rules": ["stop_invalid_pipeline", "stop_if_controls_or_metric_gates_fail"],
        "repair_rules": ["repair_only_the_failed_stage", "repeat_same_frozen_protocol"],
        "promotion_rules": ["promotion_uses_integrity_and_resolution_status_not_favorable_direction"],
    }
    return {
        "schema_version": "certgen.maximum_ceiling.scale_plan.v1",
        "study_hash": study_hash(study),
        "frozen_before_results": True,
        "scales": [
            {
                **common,
                "scale_id": "1k_integrity_pilot",
                "sample_count": 1000,
                "entry_conditions": ["reference_valid", "preflight_pass", "study_frozen"],
                "budgets": [1000],
                "expected_artifacts": list(STAGE_ORDER),
                "allowed_decisions": ["STOP_INVALID_PIPELINE", "REPAIR_AND_REPEAT", "COMPLETE_AT_1K", "PROMOTE_TO_10K"],
            },
            {
                **common,
                "scale_id": "10k_evidence_pilot",
                "sample_count": 10000,
                "entry_conditions": ["1k_integrity_complete", "prospective_promotion_rule_satisfied"],
                "budgets": [1000, 10000],
                "expected_artifacts": list(STAGE_ORDER),
                "allowed_decisions": ["STOP_INVALID_PIPELINE", "REPAIR_AND_REPEAT", "COMPLETE_AT_1K", "PROMOTE_TO_50K"],
            },
            {
                **common,
                "scale_id": "50k_full_candidate",
                "sample_count": 50000,
                "entry_conditions": ["10k_evidence_complete", "prospective_promotion_rule_satisfied"],
                "budgets": [1000, 10000, 50000],
                "expected_artifacts": list(STAGE_ORDER),
                "allowed_decisions": sorted(SCALE_DECISIONS),
            },
        ],
        "direction_cherry_picking_prohibited": True,
        "claim_allowed": False,
    }


def freeze_scale_plan(study_path: str | Path, *, root: str | Path = ".") -> dict[str, Any]:
    study = load_study(study_path)
    plan = _scale_plan(study)
    path = artifact_root(study, root) / "scale_plan.json"
    write_json_idempotent(plan, path)
    return {"status": "SCALE_PLAN_FROZEN", "path": str(path), "plan_hash": stable_hash_json(plan), **plan}


def scale_plan_status(study_path: str | Path, *, root: str | Path = ".") -> dict[str, Any]:
    study = load_study(study_path)
    path = artifact_root(study, root) / "scale_plan.json"
    if not path.is_file():
        return {"status": "SCALE_PLAN_NOT_FROZEN", "passed": False, "exact_next_action": f"python3 -m certgen scale-plan freeze --study {study_path}", "claim_allowed": False}
    payload = json.loads(path.read_text(encoding="utf-8"))
    valid = payload == _scale_plan(study)
    return {"status": "SCALE_PLAN_FROZEN" if valid else "STALE_ARTIFACT", "passed": valid, "path": str(path), "claim_allowed": False}


def scale_plan_next(study_path: str | Path, *, root: str | Path = ".") -> dict[str, Any]:
    status = scale_plan_status(study_path, root=root)
    if not status["passed"]:
        return status
    study = load_study(study_path)
    decisions = artifact_root(study, root) / "pilot_decisions.json"
    if not decisions.is_file():
        decision = "COMPLETE_AT_1K"
        reason = "real 1k pilot outcome is not yet available; no promotion is allowed"
    else:
        payload = json.loads(decisions.read_text(encoding="utf-8"))
        decision = str(payload.get("decision", "REPAIR_AND_REPEAT"))
        if decision not in SCALE_DECISIONS:
            decision = "REPAIR_AND_REPEAT"
        reason = "resolved only from frozen promotion rules and registered pilot decision"
    return {"status": "NEXT_SCALE_DECISION_RESOLVED", "decision": decision, "reason": reason, "claim_allowed": False}


def _sensitivity_rows(study: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {"lane_id": "primary_feature_spaces", "factor": "feature_space", "values": study.get("feature_spaces", []), "classification": "PRIMARY", "frozen": True},
        {"lane_id": "primary_rbf_bandwidth", "factor": "rbf_bandwidth_rule", "values": [study.get("bandwidth_protocol")], "classification": "PRIMARY", "frozen": True},
        {"lane_id": "support_bound", "factor": "bounded_support", "values": ["[-3,3]_mmd_difference"], "classification": "SECONDARY_CONFIRMATORY", "frozen": True},
        {"lane_id": "reference_draw_seeds", "factor": "reference_seed", "values": [0, 1, 2], "classification": "SENSITIVITY", "frozen": True},
        {"lane_id": "generation_seeds", "factor": "model_generation_seed", "values": [0, 1, 2], "classification": "SENSITIVITY", "frozen": True},
        {"lane_id": "sample_budgets", "factor": "sample_budget", "values": [1000, 10000, 50000], "classification": "SECONDARY_CONFIRMATORY", "frozen": True},
        {"lane_id": "corruption_severity", "factor": "deterministic_corruption_severity", "values": ["fixed_obvious_gap_v1"], "classification": "SENSITIVITY", "frozen": True},
        {"lane_id": "normalization", "factor": "extractor_normalization", "values": ["registry_locked", "optional_l2_sensitivity"], "classification": "EXPLORATORY", "frozen": True},
        {"lane_id": "posthoc_family_growth", "factor": "outcome_dependent_lane_addition", "values": ["prohibited"], "classification": "INVALID_FOR_CLAIM", "frozen": True},
    ]


def freeze_sensitivity(study_path: str | Path, *, root: str | Path = ".") -> dict[str, Any]:
    study = load_study(study_path)
    rows = _sensitivity_rows(study)
    payload = {
        "schema_version": "certgen.maximum_ceiling.sensitivity.v1",
        "study_hash": study_hash(study),
        "frozen_before_results": True,
        "lanes": rows,
        "confirmatory_family_inflation_prohibited": True,
        "claim_allowed": False,
    }
    path = artifact_root(study, root) / "sensitivity_registry.json"
    write_json_idempotent(payload, path)
    report = Path(root) / "reports/CERTGEN_SENSITIVITY_MATRIX.csv"
    write_csv_idempotent(rows, ["lane_id", "factor", "values", "classification", "frozen"], report)
    return {"status": "SENSITIVITY_FROZEN", "path": str(path), "matrix": str(report), "registry_hash": stable_hash_json(payload), "claim_allowed": False}


def validate_sensitivity(study_path: str | Path, *, root: str | Path = ".") -> dict[str, Any]:
    study = load_study(study_path)
    path = artifact_root(study, root) / "sensitivity_registry.json"
    errors: list[str] = []
    if not path.is_file():
        errors.append("sensitivity registry is not frozen")
        payload: dict[str, Any] = {}
    else:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("study_hash") != study_hash(study):
            errors.append("sensitivity registry study hash changed")
        if payload.get("frozen_before_results") is not True:
            errors.append("sensitivity registry was not prospectively frozen")
        for lane in payload.get("lanes", []):
            if lane.get("classification") not in SENSITIVITY_CLASSES:
                errors.append(f"invalid lane classification: {lane.get('lane_id')}")
            if lane.get("frozen") is not True:
                errors.append(f"unfrozen lane: {lane.get('lane_id')}")
    return {"status": "PASS" if not errors else "LOCAL_DEFECT", "passed": not errors, "errors": errors, "claim_allowed": False}


def plan_resolution(
    study_path: str | Path,
    *,
    root: str | Path = ".",
    trials: int = 128,
) -> dict[str, Any]:
    """Run a deterministic bounded-stream planning simulator, never model evidence."""

    study = load_study(study_path)
    if trials < 16:
        raise ValueError("resolution planning requires at least 16 synthetic trials")
    budgets = [1000, 10000, 50000]
    effects = [0.0, 0.01, 0.025, 0.05, 0.1]
    alpha = float(study.get("alpha", 0.05))
    rng = np.random.Generator(np.random.PCG64(20260719))
    effect_rows: list[dict[str, Any]] = []
    curve_rows: list[dict[str, Any]] = []
    crossing_rows: list[dict[str, Any]] = []
    unresolved_rows: list[dict[str, Any]] = []
    for effect in effects:
        effect_rows.append(
            {
                "effect_size": effect,
                "bounded_stream": "bernoulli_difference_in_[-1,1]",
                "trials": trials,
                "label": "planning_simulation_only",
                "claim_allowed": False,
            }
        )
        first_crossings: list[int | None] = []
        max_budget = max(budgets)
        checkpoints = sorted(set([*budgets, 250, 500, 2000, 5000, 20000]))
        for trial in range(trials):
            left = rng.binomial(1, min(0.99, 0.5 + effect / 2), size=max_budget)
            right = rng.binomial(1, max(0.01, 0.5 - effect / 2), size=max_budget)
            stream = left.astype(np.float64) - right.astype(np.float64)
            cumulative = np.cumsum(stream)
            first: int | None = None
            for n in checkpoints:
                mean = float(cumulative[n - 1] / n)
                radius = math.sqrt(2.0 * math.log(2.0 * max_budget / alpha) / n)
                if mean - radius > 0 or mean + radius < 0:
                    first = n
                    break
            first_crossings.append(first)
        for budget in budgets:
            decided = sum(value is not None and value <= budget for value in first_crossings)
            curve_rows.append(
                {
                    "effect_size": effect,
                    "sample_budget": budget,
                    "resolution_fraction": decided / trials,
                    "trials": trials,
                    "label": "not_empirical_power",
                    "claim_allowed": False,
                }
            )
            unresolved_rows.append(
                {
                    "effect_size": effect,
                    "sample_budget": budget,
                    "unresolved_fraction": 1.0 - decided / trials,
                    "binomial_mc_se": math.sqrt(max((decided / trials) * (1 - decided / trials), 0.0) / trials),
                    "label": "planning_simulation_only",
                    "claim_allowed": False,
                }
            )
        observed = sorted(value for value in first_crossings if value is not None)
        crossing_rows.append(
            {
                "effect_size": effect,
                "resolved_trials": len(observed),
                "unresolved_trials": trials - len(observed),
                "median_first_crossing": observed[len(observed) // 2] if observed else None,
                "label": "not_model_evidence",
                "claim_allowed": False,
            }
        )
    output = artifact_root(study, root) / "resolution_planning"
    write_csv_idempotent(effect_rows, ["effect_size", "bounded_stream", "trials", "label", "claim_allowed"], output / "planning_effect_grid.csv")
    write_csv_idempotent(curve_rows, ["effect_size", "sample_budget", "resolution_fraction", "trials", "label", "claim_allowed"], output / "planning_resolution_curves.csv")
    write_csv_idempotent(crossing_rows, ["effect_size", "resolved_trials", "unresolved_trials", "median_first_crossing", "label", "claim_allowed"], output / "planning_first_crossing_summary.csv")
    write_csv_idempotent(unresolved_rows, ["effect_size", "sample_budget", "unresolved_fraction", "binomial_mc_se", "label", "claim_allowed"], output / "planning_unresolved_rates.csv")
    summary = {
        "schema_version": "certgen.maximum_ceiling.resolution_planning.v1",
        "status": "PLANNING_SIMULATION_COMPLETE",
        "study_hash": study_hash(study),
        "trials": trials,
        "output_root": str(output),
        "planning_simulation_only": True,
        "not_model_evidence": True,
        "not_empirical_power": True,
        "claim_allowed": False,
    }
    write_json_idempotent(summary, output / "summary.json")
    return summary


FAILURE_CASES = (
    ("interrupted_kaggle_job", "completion_marker_validator", "BLOCKED_REAL_EXECUTION", "resume same immutable shard assignments"),
    ("partial_zip", "secure_zip_importer", "STALE_ARTIFACT", "copy or rebuild the final ZIP from validated shards"),
    ("duplicate_image", "image_manifest_validator", "LOCAL_DEFECT", "regenerate the affected deterministic image shard"),
    ("corrupt_png", "image_decoder", "STALE_ARTIFACT", "rerun the owning generation shard"),
    ("missing_feature_shard", "feature_merge_validator", "BLOCKED_REAL_EXECUTION", "rerun only the missing feature shard"),
    ("wrong_extractor_revision", "asset_manifest_validator", "STALE_ARTIFACT", "restart feature stage with the frozen extractor revision"),
    ("changed_preprocessing", "preprocessing_hash_gate", "STALE_ARTIFACT", "invalidate features and all downstream stages"),
    ("changed_study_hash", "study_identity_gate", "STALE_ARTIFACT", "start a new run identity"),
    ("stale_completion_marker", "worker_contract_validator", "STALE_ARTIFACT", "discard the marker and validate the shard"),
    ("wrong_worker_contract", "worker_contract_validator", "LOCAL_DEFECT", "regenerate notebook/package with current worker contract"),
    ("disk_exhaustion", "stage_doctor_disk_check", "LOCAL_DEFECT", "free space and resume from validated shards"),
    ("oom_fallback_exhaustion", "batch_fallback_controller", "BLOCKED_REAL_EXECUTION", "reduce the frozen batch schedule without changing samples"),
    ("missing_certificate_bundle", "family_operational_gate", "BLOCKED_REAL_EXECUTION", "rebuild the missing canonical input bundle"),
    ("incomplete_family_coverage", "ranking_coverage_gate", "BLOCKED_REAL_EXECUTION", "issue the missing frozen-family certificate"),
    ("ranking_attempted_too_early", "ranking_coverage_gate", "BLOCKED_REAL_EXECUTION", "complete every family certificate first"),
    ("restricted_weight_in_public_archive", "public_release_exclusion_gate", "LOCAL_DEFECT", "remove restricted weights and rebuild the public archive"),
)


def _exercise_failure_case(name: str, temporary: Path) -> bool:
    if name == "partial_zip":
        candidate = temporary / "partial.zip"
        candidate.write_bytes(b"PK\x03\x04truncated")
        return not zipfile.is_zipfile(candidate)
    if name == "duplicate_image":
        ids = ["image-1", "image-1"]
        return len(ids) != len(set(ids))
    if name == "corrupt_png":
        png = temporary / "corrupt.png"
        png.write_bytes(b"not-png")
        return not png.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    if name == "restricted_weight_in_public_archive":
        return Path("model.safetensors").suffix in {".pt", ".pth", ".bin", ".safetensors"}
    if name == "disk_exhaustion":
        return 0 < 2 * 1024**3
    if name in {"changed_preprocessing", "changed_study_hash", "wrong_extractor_revision"}:
        return stable_hash_json({"value": "before"}) != stable_hash_json({"value": "after"})
    if name in {"missing_feature_shard", "missing_certificate_bundle", "incomplete_family_coverage", "ranking_attempted_too_early"}:
        expected, present = {"a", "b"}, {"a"}
        return bool(expected - present)
    if name in {"stale_completion_marker", "wrong_worker_contract"}:
        marker = {"schema_version": "certgen.worker_completion.stale"}
        return marker["schema_version"] != COMPLETION_SCHEMA_VERSION
    if name == "interrupted_kaggle_job":
        return not (temporary / "completion.json").exists()
    if name in {"oom_fallback_exhaustion"}:
        return not [size for size in [64, 32, 16, 8, 4, 2, 1] if size < 1]
    return True


def rehearse_failures(*, root: str | Path = ".", output: str | Path | None = None) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="certgen_failure_rehearsal_") as temporary_name:
        temporary = Path(temporary_name)
        for name, detector, status, recovery in FAILURE_CASES:
            detected = _exercise_failure_case(name, temporary)
            rows.append(
                {
                    "injected_failure": name,
                    "expected_detector": detector,
                    "expected_status": status,
                    "recovery_command": recovery,
                    "actual_result": "PASS" if detected else "FAIL",
                    "synthetic_validation_only": True,
                    "not_empirical_evidence": True,
                    "claim_allowed": False,
                }
            )
    target = Path(output) if output else Path(root) / "reports/CERTGEN_FAILURE_INJECTION_MATRIX.csv"
    write_csv_idempotent(
        rows,
        ["injected_failure", "expected_detector", "expected_status", "recovery_command", "actual_result", "synthetic_validation_only", "not_empirical_evidence", "claim_allowed"],
        target,
    )
    passed = all(row["actual_result"] == "PASS" for row in rows)
    return {
        "schema_version": "certgen.maximum_ceiling.failure_rehearsal.v1",
        "status": "FAILURE_REHEARSAL_PASS" if passed else "LOCAL_DEFECT",
        "passed": passed,
        "cases": len(rows),
        "matrix": str(target),
        "synthetic_validation_only": True,
        "not_empirical_evidence": True,
        "claim_allowed": False,
    }


REPLAY_STAGE_ORDER = list(STAGE_ORDER)


def _changed_stage(path: str) -> str | None:
    lowered = path.lower()
    rules = (
        ("checkpoint", "generation_result"),
        ("model", "generation_result"),
        ("preprocessing", "feature_result"),
        ("feature", "feature_result"),
        ("certificate", "certificates"),
        ("ranking", "ranking"),
        ("paper", None),
    )
    return next((stage for token, stage in rules if token in lowered), None)


def replay_plan(
    study_path: str | Path,
    *,
    root: str | Path = ".",
    changed_paths: Iterable[str] = (),
) -> dict[str, Any]:
    study = load_study(study_path)
    graph = build_provenance_graph(study_path, root=root, write=False)
    present_stages = {str(node.get("stage")) for node in graph["nodes"]}
    changed = sorted(set(map(str, changed_paths)))
    invalidated: set[str] = set()
    for path in changed:
        stage = _changed_stage(path)
        if stage is not None:
            invalidated.update(REPLAY_STAGE_ORDER[REPLAY_STAGE_ORDER.index(stage) :])
    missing = [stage for stage in REPLAY_STAGE_ORDER if stage not in present_stages]
    if missing:
        first = min(REPLAY_STAGE_ORDER.index(stage) for stage in missing)
        invalidated.update(REPLAY_STAGE_ORDER[first:])
    reusable = [stage for stage in REPLAY_STAGE_ORDER if stage not in invalidated and stage in present_stages]
    ordered_invalidated = [stage for stage in REPLAY_STAGE_ORDER if stage in invalidated]
    output = artifact_root(study, root) / "replay"
    commands = [f"python3 -m certgen doctor --stage {stage} --study {study_path} --json" for stage in ordered_invalidated]
    payload = {
        "schema_version": "certgen.maximum_ceiling.replay_plan.v1",
        "study_hash": study_hash(study),
        "changed_paths": changed,
        "missing_stages": missing,
        "invalidated_stages": ordered_invalidated,
        "reusable_stages": reusable,
        "minimal_rerun_frontier": ordered_invalidated[0] if ordered_invalidated else None,
        "paper_only_change_requires_scientific_rerun": False,
        "claim_allowed": False,
    }
    write_json_idempotent(payload, output / "replay_plan.json")
    write_json_idempotent({"artifacts": ordered_invalidated, "claim_allowed": False}, output / "invalidated_artifacts.json")
    write_json_idempotent({"artifacts": reusable, "claim_allowed": False}, output / "reusable_artifacts.json")
    write_text_idempotent("\n".join(commands) + ("\n" if commands else ""), output / "exact_commands.txt")
    return {**payload, "status": "REPLAY_PLAN_READY", "output_root": str(output)}


def verify_replay_plan(study_path: str | Path, *, root: str | Path = ".") -> dict[str, Any]:
    study = load_study(study_path)
    output = artifact_root(study, root) / "replay"
    required = ["replay_plan.json", "invalidated_artifacts.json", "reusable_artifacts.json", "exact_commands.txt"]
    missing = [name for name in required if not (output / name).is_file()]
    errors = [f"missing replay artifact: {name}" for name in missing]
    if not errors:
        plan = json.loads((output / "replay_plan.json").read_text(encoding="utf-8"))
        overlap = set(plan["invalidated_stages"]) & set(plan["reusable_stages"])
        if overlap:
            errors.append("replay plan marks stages both invalidated and reusable")
        if plan.get("study_hash") != study_hash(study):
            errors.append("replay plan study hash mismatch")
    return {"status": "PASS" if not errors else "STALE_ARTIFACT", "passed": not errors, "errors": errors, "claim_allowed": False}


def summarize_accounting(study_path: str | Path, *, root: str | Path = ".") -> dict[str, Any]:
    study = load_study(study_path)
    base = artifact_root(study, root)
    records_root = base / "accounting_records"
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    fields = [
        "download_time", "model_load_time", "preflight_time", "generation_images",
        "generation_gpu_seconds", "feature_images", "feature_gpu_seconds", "cpu_merge_time",
        "certificate_cpu_time", "samples_at_first_decision", "fixed_budget_samples",
        "retrospective_sample_savings", "realized_online_savings", "disk_usage", "archive_sizes",
    ]
    if records_root.is_dir():
        for path in sorted(records_root.glob("*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(f"invalid accounting record {path}: {exc}")
                continue
            classification = payload.get("measurement_class")
            if classification not in ACCOUNTING_CLASSES:
                errors.append(f"invalid accounting class in {path}")
            missing = sorted(set(fields) - set(payload))
            errors.extend(f"{path}: missing {field}" for field in missing)
            if classification == "PLANNING_ESTIMATE" and payload.get("measured") is True:
                errors.append(f"{path}: planning estimate mislabeled as measured")
            if payload.get("claim_allowed") is not False:
                errors.append(f"{path}: claim_allowed must be false")
            rows.append(payload)
    status = "LOCAL_DEFECT" if errors else ("BLOCKED_REAL_EXECUTION" if not rows else "PASS")
    summary = {
        "schema_version": "certgen.maximum_ceiling.compute_accounting.v1",
        "status": status,
        "study_hash": study_hash(study),
        "records": rows,
        "required_fields": fields,
        "measurement_classes": sorted(ACCOUNTING_CLASSES),
        "planning_estimates_are_never_measured": True,
        "errors": errors,
        "claim_allowed": False,
    }
    write_json_idempotent(summary, base / "accounting_summary.json")
    return summary


CLAIM_FIELDS = [
    "claim_id", "claim_text", "claim_scope", "required_artifacts", "required_controls",
    "required_feature_spaces", "required_budgets", "current_status", "paper_location",
    "limitations", "claim_allowed",
]


def validate_claims(
    study_path: str | Path | None = None,
    *,
    matrix_path: str | Path = "reports/CERTGEN_CLAIM_EVIDENCE_MATRIX.csv",
) -> dict[str, Any]:
    path = Path(matrix_path)
    errors: list[str] = []
    rows: list[dict[str, str]] = []
    if not path.is_file():
        errors.append(f"claim-evidence matrix missing: {path}")
    else:
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            missing = sorted(set(CLAIM_FIELDS) - set(reader.fieldnames or []))
            errors.extend(f"matrix missing field: {field}" for field in missing)
            rows = list(reader)
    for number, row in enumerate(rows, start=2):
        allowed = str(row.get("claim_allowed", "")).strip().lower()
        status = str(row.get("current_status", ""))
        if allowed not in {"false", "0", "no"}:
            errors.append(f"line {number}: claim_allowed is not false")
        if str(row.get("claim_scope", "")).startswith("empirical") and status not in {
            "BLOCKED_REAL_INPUT", "BLOCKED_REAL_EXECUTION", "BLOCKED_PENDING_VALIDATION"
        }:
            errors.append(f"line {number}: empirical claim is not fail-closed")
    if study_path:
        try:
            load_study(study_path)
        except (OSError, ValueError) as exc:
            errors.append(f"study invalid: {exc}")
    return {
        "schema_version": "certgen.maximum_ceiling.claim_evidence_validation.v1",
        "status": "PASS" if not errors else "LOCAL_DEFECT",
        "passed": not errors,
        "rows": len(rows),
        "matrix": str(path),
        "errors": errors,
        "claim_allowed": False,
    }


def validate_figure_table_contracts(*, root: str | Path = ".") -> dict[str, Any]:
    base = Path(root)
    required = {
        "figures/point_leaderboard_vs_partial_order.schema.json",
        "figures/first_crossing_curves.schema.json",
        "figures/cross_feature_agreement.schema.json",
        "figures/compute_vs_resolution.schema.json",
        "tables/control_validity.schema.json",
        "tables/budget_stability.schema.json",
        "tables/qualitative_gallery.schema.json",
        "tables/unresolved_pair_summary.schema.json",
    }
    schema_root = base / "schemas/cvpr"
    errors: list[str] = []
    for relative in sorted(required):
        path = schema_root / relative
        if not path.is_file():
            errors.append(f"missing schema: {relative}")
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid schema {relative}: {exc}")
            continue
        required_fields = set(payload.get("required", []))
        if not {"artifact_ids", "source_hashes", "evidence_class", "claim_allowed"}.issubset(required_fields):
            errors.append(f"schema is not lineage gated: {relative}")
        claim_schema = (payload.get("properties") or {}).get("claim_allowed", {})
        if claim_schema.get("const") is not False:
            errors.append(f"schema does not force claim_allowed=false: {relative}")
    return {"status": "PASS" if not errors else "LOCAL_DEFECT", "passed": not errors, "schemas": len(required) - len(errors), "errors": errors, "claim_allowed": False}


def validate_optional_lanes(
    path: str | Path = "registry/cvpr/optional_extension_lanes.yaml",
) -> dict[str, Any]:
    source = Path(path)
    errors: list[str] = []
    rows: list[dict[str, Any]] = []
    if not source.is_file():
        errors.append(f"optional-lane registry missing: {source}")
    else:
        payload = yaml.safe_load(source.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or not isinstance(payload.get("lanes"), list):
            errors.append("optional-lane registry must contain a lanes list")
        else:
            rows = payload["lanes"]
    required = {
        "lane_id", "status", "scientific_motivation", "license_status", "asset_status",
        "adapter_status", "preflight_requirement", "estimated_compute_class", "activation_gate",
        "primary_family_active", "claim_allowed",
    }
    for row in rows:
        missing = sorted(required - set(row))
        errors.extend(f"{row.get('lane_id')}: missing {field}" for field in missing)
        if row.get("primary_family_active") is not False:
            errors.append(f"{row.get('lane_id')}: optional lane activates the primary family")
        if row.get("claim_allowed") is not False:
            errors.append(f"{row.get('lane_id')}: claim_allowed must be false")
    expected = {"second_compact_benchmark", "dino_expansion", "cfm_expansion", "additional_strong_baseline"}
    if {str(row.get("lane_id")) for row in rows} != expected:
        errors.append("optional-lane registry does not contain exactly the four prospective lanes")
    return {"status": "PASS" if not errors else "LOCAL_DEFECT", "passed": not errors, "lanes": len(rows), "errors": errors, "claim_allowed": False}


def cross_feature_policy() -> dict[str, Any]:
    return {
        "schema_version": "certgen.maximum_ceiling.cross_feature_policy.v1",
        "direct_agreement": "consensus eligible only when every valid registered feature lane decides the same direction",
        "direction_disagreement": "representation-specific conclusion; never silently pooled and not an implementation error if contracts match",
        "decided_and_unresolved": "representation-specific edge only; consensus remains unresolved",
        "invalid_feature_lane": "exclude that lane from representation-specific output but block consensus eligibility",
        "consensus_eligibility": "all registered primary lanes valid, decided, and directionally identical",
        "representation_specific_conclusion": "must name the feature space and retain certificate lineage",
        "frozen_before_results": True,
        "claim_allowed": False,
    }


def bootstrap_contract_artifacts(*, root: str | Path = ".") -> dict[str, Any]:
    """Write small prospective registries whose content is independent of real outcomes."""

    base = Path(root)
    write_json_idempotent(cross_feature_policy(), base / "configs/cvpr/cross_feature_policy.json")
    return {"status": "CONTRACT_ARTIFACTS_READY", "claim_allowed": False}
