"""Profile/study-bound reference draw-plan builder for the canonical CVPR route."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from certgen.core.hashing import file_sha256, stable_hash_json
from certgen.cvpr.contracts import atomic_write_json
from certgen.cvpr.profiles import load_profile
from certgen.cvpr.study import require_frozen_study
from certgen.packaging.artifact_registry import append_artifact_entry, build_artifact_entry
from certgen.stats.reference_sampling import build_reference_draw_plan, validate_reference_draw_plan


CANONICAL_SCHEMA_VERSION = "certgen.cvpr.reference_draw_plan.v2"


def _reference_rows(path: Path) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows or any(not isinstance(row, dict) for row in rows):
        raise ValueError("reference manifest must contain JSON objects")
    ids = [str(row.get("sample_id", "")) for row in rows]
    if any(not value for value in ids) or len(ids) != len(set(ids)):
        raise ValueError("reference manifest sample IDs must be non-empty and unique")
    return rows


def _control_roles(profile: dict[str, Any], ids: list[str], seed: int) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    controls = set(map(str, profile.get("controls", [])))
    budget = max(map(int, profile["sample_budgets"]))
    needed = (2 * budget if "null_reference_split" in controls else 0) + (
        budget if "obvious_gap_corruption" in controls else 0
    )
    if len(ids) < needed:
        raise ValueError(
            f"reference population is insufficient for frozen disjoint control roles: required={needed}, available={len(ids)}"
        )
    order = np.random.Generator(np.random.PCG64(seed + 1)).permutation(len(ids)).astype(int).tolist()
    offset = 0
    allocations: dict[str, Any] = {}
    constraints: list[dict[str, Any]] = []
    if "null_reference_split" in controls:
        split_a = [ids[index] for index in order[offset : offset + budget]]
        offset += budget
        split_b = [ids[index] for index in order[offset : offset + budget]]
        offset += budget
        allocations["null_control_split_a"] = split_a
        allocations["null_control_split_b"] = split_b
        constraints.append(
            {
                "left_role": "null_control_split_a",
                "right_role": "null_control_split_b",
                "required_relation": "disjoint_source_ids",
            }
        )
    if "obvious_gap_corruption" in controls:
        clean = [ids[index] for index in order[offset : offset + budget]]
        allocations["obvious_gap_clean"] = clean
        allocations["obvious_gap_corrupted"] = clean
        constraints.append(
            {
                "left_role": "obvious_gap_clean",
                "right_role": "obvious_gap_corrupted",
                "required_relation": "same_sources_distinct_output_ids",
            }
        )
    return allocations, constraints


def validate_canonical_reference_draw(
    plan: dict[str, Any],
    *,
    study: dict[str, Any] | None = None,
    profile: dict[str, Any] | None = None,
    source_ids: list[str] | None = None,
) -> dict[str, Any]:
    errors = list(validate_reference_draw_plan(plan, source_ids=source_ids).get("errors", []))
    required = {
        "draw_plan_id", "study_hash", "profile_id", "benchmark_id", "reference_population_hash",
        "draw_method", "with_or_without_replacement", "seed", "ordered_reference_ids",
        "source_population_ids", "time_index",
        "roles", "non_overlap_constraints", "control_allocations", "configuration_hash", "created_at",
        "claim_allowed",
    }
    errors.extend(f"missing canonical draw-plan field: {field}" for field in sorted(required - set(plan)))
    if plan.get("canonical_schema_version") != CANONICAL_SCHEMA_VERSION:
        errors.append("canonical reference draw-plan schema version mismatch")
    if plan.get("with_or_without_replacement") != "with_replacement":
        errors.append("model-comparison reference draw must use replacement")
    raw_draws = plan.get("draws")
    draws: list[dict[str, Any]] = (
        [row for row in raw_draws if isinstance(row, dict)] if isinstance(raw_draws, list) else []
    )
    if plan.get("ordered_reference_ids") != [row.get("source_id") for row in draws]:
        errors.append("ordered_reference_ids differ from canonical draw order")
    if plan.get("time_index") != list(range(len(draws))):
        errors.append("time_index must be the canonical ordered range")
    allocations = plan.get("control_allocations")
    if not isinstance(allocations, dict):
        errors.append("control_allocations must be an object")
        allocations = {}
    null_a = set(map(str, allocations.get("null_control_split_a", [])))
    null_b = set(map(str, allocations.get("null_control_split_b", [])))
    if null_a & null_b:
        errors.append("null-control source allocations overlap")
    if study is not None and plan.get("study_hash") != study.get("configuration_hash"):
        errors.append("reference draw plan study hash mismatch")
    if profile is not None:
        if plan.get("profile_id") != profile.get("profile_id"):
            errors.append("reference draw plan profile mismatch")
        expected_roles = set(map(str, profile.get("controls", [])))
        actual_roles = set(map(str, plan.get("roles", {}).get("frozen_controls", []))) if isinstance(plan.get("roles"), dict) else set()
        if expected_roles != actual_roles:
            errors.append("reference draw plan contains a post-hoc or missing control role")
    without_configuration = {
        key: value for key, value in plan.items() if key not in {"configuration_hash", "plan_sha256"}
    }
    if plan.get("configuration_hash") != stable_hash_json(without_configuration):
        errors.append("reference draw plan configuration_hash mismatch")
    return {"passed": not errors, "errors": errors, "claim_allowed": False}


def prepare_reference_draw(
    *,
    profile_id: str,
    study_path: str | Path,
    reference_manifest: str | Path,
    out_path: str | Path = "registry/manifests/cvpr/reference_draw_plan.json",
    seed: int = 0,
    profile_root: str | Path = "configs/cvpr/profiles",
    registry_path: str | Path | None = "data/artifact_registry.jsonl",
    dry_run: bool = False,
) -> dict[str, Any]:
    profile = load_profile(profile_id, profile_root)
    study = require_frozen_study(study_path, profile=profile)
    manifest = Path(reference_manifest)
    if not manifest.is_file():
        raise FileNotFoundError(f"materialized reference manifest missing: {manifest}")
    rows = _reference_rows(manifest)
    try:
        portable_manifest = manifest.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        portable_manifest = str(manifest)
    source_ids = [str(row["sample_id"]) for row in rows]
    allocations, constraints = _control_roles(profile, source_ids, seed)
    plan = build_reference_draw_plan(
        source_ids,
        num_draws=int(profile["reference_count"]),
        seed=seed,
        population_id=f"{profile['benchmark']}__materialized_reference",
        source_manifest_sha256=file_sha256(manifest),
    )
    plan.update(
        {
            "canonical_schema_version": CANONICAL_SCHEMA_VERSION,
            "study_hash": study["configuration_hash"],
            "profile_id": profile_id,
            "profile_hash": profile["profile_hash"],
            "benchmark_id": profile["benchmark"],
            "reference_manifest_path": portable_manifest,
            "reference_population_hash": stable_hash_json(source_ids),
            "draw_method": plan["sampling_scheme"],
            "with_or_without_replacement": "with_replacement",
            "ordered_reference_ids": [row["source_id"] for row in plan["draws"]],
            "source_population_ids": source_ids,
            "time_index": list(range(len(plan["draws"]))),
            "roles": {
                "model_comparison_reference": [row["draw_id"] for row in plan["draws"]],
                "frozen_controls": list(map(str, profile.get("controls", []))),
            },
            "non_overlap_constraints": constraints,
            "control_allocations": allocations,
            "created_at": "prospectively_frozen_by_certgen_reference_draw_v2",
            "evidence_class": "planning_or_input_artifact",
            "synthetic_validation_only": False,
            "not_empirical_evidence": True,
        }
    )
    plan["draw_plan_id"] = f"{profile_id}__{stable_hash_json(plan)[:16]}"
    hash_payload = {
        key: value for key, value in plan.items() if key not in {"configuration_hash", "plan_sha256"}
    }
    plan["plan_sha256"] = stable_hash_json(hash_payload)
    plan["configuration_hash"] = stable_hash_json(hash_payload)
    verdict = validate_canonical_reference_draw(plan, study=study, profile=profile, source_ids=source_ids)
    if not verdict["passed"]:
        raise ValueError("generated reference draw plan is invalid: " + "; ".join(verdict["errors"]))
    result = {
        "status": "REFERENCE_DRAW_PLAN_READY",
        "draw_plan": str(out_path),
        "draw_plan_id": plan["draw_plan_id"],
        "configuration_hash": plan["configuration_hash"],
        "study_hash": study["configuration_hash"],
        "dry_run": dry_run,
        "evidence_class": "planning_or_input_artifact",
        "claim_allowed": False,
    }
    if dry_run:
        return result
    atomic_write_json(plan, out_path)
    if registry_path is not None:
        entry = build_artifact_entry(
            path=out_path,
            artifact_type="cvpr_reference_draw_plan",
            stage="reference_draw",
            run_id=plan["draw_plan_id"],
            source=str(manifest),
            validation_status="canonical_draw_plan_validated",
            evidence_class="planning_or_input_artifact",
            notes="Profile/study-bound pre-run draw plan; not empirical evidence.",
        )
        entry["study_hash"] = study["configuration_hash"]
        entry["configuration_hash"] = plan["configuration_hash"]
        append_artifact_entry(
            entry,
            registry_path,
        )
    return result
