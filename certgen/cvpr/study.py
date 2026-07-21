"""Prospective study freezing derived from a named pilot profile."""

from __future__ import annotations

import csv
from pathlib import Path
from collections.abc import Sequence
from typing import Any, Mapping

import yaml  # type: ignore[import-untyped]

from certgen.core.hashing import stable_hash_json
from certgen.cvpr.contracts import configuration_hash
from certgen.cvpr.profiles import load_profile, validate_profile
from certgen.cvpr.registries import validate_preregistration


def _yaml(path: str | Path) -> dict[str, Any]:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected a YAML mapping: {path}")
    return payload


def _selected(rows: Sequence[Mapping[str, Any]], identity: str, wanted: list[str]) -> list[dict[str, Any]]:
    indexed = {str(row[identity]): dict(row) for row in rows}
    missing = sorted(set(wanted) - set(indexed))
    if missing:
        raise ValueError(f"study freeze cannot resolve {identity}: {missing}")
    return [indexed[value] for value in wanted]


def freeze_study(
    profile_id: str,
    *,
    out_path: str | Path,
    profile_root: str | Path = "configs/cvpr/profiles",
    model_registry: str | Path = "registry/cvpr/model_registry.yaml",
    feature_registry: str | Path = "registry/cvpr/feature_space_registry.yaml",
    comparison_registry: str | Path = "registry/cvpr/comparison_registry.csv",
    alpha: float = 0.05,
) -> dict[str, Any]:
    """Freeze every claim-relevant choice without inspecting result artifacts."""

    if not 0.0 < float(alpha) < 1.0:
        raise ValueError("alpha must lie in (0,1)")
    profile = load_profile(profile_id, profile_root)
    profile_verdict = validate_profile(profile)
    if not profile_verdict["passed"]:
        raise ValueError("invalid pilot profile: " + "; ".join(profile_verdict["errors"]))
    models = _selected(
        list(_yaml(model_registry).get("models", [])),
        "model_id",
        list(map(str, profile["models"])),
    )
    extractors = _selected(
        list(_yaml(feature_registry).get("feature_spaces", [])),
        "feature_space_id",
        list(map(str, profile["extractors"])),
    )
    with Path(comparison_registry).open(encoding="utf-8", newline="") as handle:
        comparison_rows = list(csv.DictReader(handle))
    comparisons = _selected(
        comparison_rows,
        "comparison_id",
        list(map(str, profile["comparisons"])),
    )
    if any(row.get("prospective_or_posthoc") != "prospective" for row in comparisons):
        raise ValueError("study freeze accepts prospective comparisons only")
    controls = list(map(str, profile["controls"]))
    if set(map(str, profile["comparisons"])) & set(controls):
        raise ValueError("study freeze refuses controls in the confirmatory family")
    model_pairs = [
        {
            "comparison_id": row["comparison_id"],
            "model_a": row["model_a"],
            "model_b": row["model_b"],
            "comparison_type": row.get("comparison_type"),
        }
        for row in comparisons
    ]
    feature_definitions = {
        str(row["feature_space_id"]): {
            "model_identifier": row.get("model_identifier"),
            "revision": row.get("revision"),
            "model_class": row.get("model_class"),
            "processor_class": row.get("processor_class"),
            "feature_definition": row.get("feature_definition"),
            "expected_dimension": row.get("expected_dimension"),
            "projection_applied": row.get("projection_applied"),
            "l2_normalization_applied": row.get("l2_normalization_applied"),
            "expected_preprocessing": row.get("expected_preprocessing"),
        }
        for row in extractors
    }
    preprocessing_hash = stable_hash_json(feature_definitions)
    payload: dict[str, Any] = {
        "study_id": f"certgen_cvpr_{profile_id}",
        "version": 1,
        "primary_question": "Which prospectively selected comparisons are directionally decided by bounded RBF-MMD evidence?",
        "primary_outcomes": ["family-wise-valid pairwise decisions", "certified partial ranking"],
        "secondary_outcomes": ["cross-feature agreement", "ranking stability", "samples to first decision"],
        "benchmarks": [str(profile["benchmark"])],
        "models": list(map(str, profile["models"])),
        "model_pairs": model_pairs,
        "controls": controls,
        "controls_in_confirmatory_family": False,
        "controls_claim_allowed": False,
        "feature_spaces": list(map(str, profile["feature_spaces"])),
        "metrics": list(map(str, profile["metrics"])),
        "kernel": {"name": "rbf", "normalize": "l2", "gamma": 0.5},
        "bandwidth_protocol": "prospectively_fixed_unit_sphere_gamma_0.5_v1",
        "alpha": float(alpha),
        "multiplicity_families": [str(profile["comparison_family"])],
        "sample_budgets": [int(value) for value in profile["sample_budgets"]],
        "stopping_rule": "first_boundary_crossing_union_hoeffding",
        "stream_seed": 0,
        "reference_draw_protocol": "iid_with_replacement_from_fixed_empirical_population_precommitted",
        "reference_count": int(profile["reference_count"]),
        "generation_count": int(profile["generation_count"]),
        "sanity_thresholds": {
            "null_max_absolute": 0.05,
            "obvious_gap_minimum": 1e-8,
            "repeated_batching_max_feature_difference": 1e-5,
            "repeated_batching_max_metric_difference": 1e-7,
            "repeated_shard_merge_max_feature_difference": 0.0,
            "repeated_shard_merge_max_metric_difference": 0.0,
            "corruption_ladder_minimum_aggregate_step": 1e-8,
        },
        "feature_definitions": feature_definitions,
        "model_revisions": {str(row["model_id"]): str(row["revision"]) for row in models},
        "preprocessing_hash": preprocessing_hash,
        "exclusion_rules": [
            "invalid provenance or license approval",
            "asset or preprocessing mismatch",
            "nonfinite or incomplete features",
            "failed metric reproduction or sanity gate",
        ],
        "failure_rules": ["fail closed; never substitute models, extractors, or pairs after outcomes are inspected"],
        "resume_rules": ["same study, configuration, asset, image-manifest, stream-order, draw, and alpha hashes only"],
        "missing_data_rules": ["block the affected comparison; do not impute"],
        "censoring_rules": ["UNDECIDED_AT_BUDGET is right-censored at the registered maximum budget"],
        "claim_thresholds": ["lineage, sanity, family, certificate, and paper gates must separately pass"],
        "scale_up_rules": list(map(str, profile.get("scale_up_rules", ["stop and interpret after the registered budget"]))),
        "pivot_rules": ["a scientific pivot requires a new prospective study version"],
        "profile_id": profile_id,
        "profile_hash": str(profile["profile_hash"]),
        "selection_policy": str(profile["selection_policy"]),
        "frozen": True,
        "evidence_class": str(profile["evidence_class"]),
        "claim_allowed": False,
    }
    payload["configuration_hash"] = configuration_hash(payload)
    target = Path(out_path)
    if target.exists():
        raise FileExistsError(f"refusing to overwrite frozen study: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    verdict = validate_preregistration(target, require_frozen=True)
    if not verdict["passed"]:
        target.unlink()
        raise ValueError("frozen study failed validation: " + "; ".join(verdict["errors"]))
    return {
        "status": "STUDY_FROZEN",
        "study_path": str(target),
        "study_hash": payload["configuration_hash"],
        "profile_id": profile_id,
        "profile_hash": profile["profile_hash"],
        "claim_allowed": False,
    }


def require_frozen_study(path: str | Path, *, profile: Mapping[str, Any] | None = None) -> dict[str, Any]:
    verdict = validate_preregistration(path, require_frozen=True)
    if not verdict["passed"]:
        raise ValueError("a valid frozen study is required: " + "; ".join(verdict["errors"]))
    payload = _yaml(path)
    if (
        profile is not None
        and profile.get("profile_hash") is not None
        and payload.get("profile_hash") != profile.get("profile_hash")
    ):
        raise ValueError("frozen study profile hash differs from the selected pilot profile")
    return payload
