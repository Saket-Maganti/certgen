#!/usr/bin/env python3
"""Build the deterministic prospective ICML 2027 research-control layer."""

from __future__ import annotations

import csv
import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from certgen.icml2027.baselines import BASELINES  # noqa: E402
from certgen.icml2027.common import file_sha256, stable_hash  # noqa: E402
from certgen.icml2027.dinov2 import DinoV2Contract  # noqa: E402
from certgen.icml2027.notebooks import generate_notebooks  # noqa: E402


ROOT = WORKSPACE_ROOT
CONFIG = ROOT / "configs" / "icml2027"
REGISTRY = ROOT / "registry" / "icml2027"
REPORTS = ROOT / "reports" / "icml2027"
ARTIFACTS = ROOT / "artifacts" / "icml2027"
DOCS = ROOT / "docs" / "icml2027"
NOTEBOOKS = ROOT / "notebooks" / "kaggle" / "icml2027"
TESTS = ROOT / "tests" / "icml2027"
TRUTH = {
    "synthetic_validation_only": True,
    "not_real_generator_evidence": True,
    "not_empirical_paper_evidence": True,
    "claim_allowed": False,
}
PLAN = {"planning_only": True, "claim_allowed": False}


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    write_text(path, json.dumps(payload, indent=2, sort_keys=True))


def write_yaml(path: Path, payload: Any) -> None:
    write_text(path, yaml.safe_dump(payload, sort_keys=False, allow_unicode=True))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = fields or list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def build_configs() -> None:
    defaults = {
        "dimension": 16,
        "sample_budget": 256,
        "alpha": 0.05,
        "kernel": "rbf",
        "bandwidth": "median",
        "multiplicity_rule": "bonferroni",
        "representation_count": 1,
        "model_count": 2,
        "look_step": 16,
    }
    scenarios = [
        {"scenario_id": "null_anytime", "family": "null_calibration", "stopping_rule": "anytime"},
        {"scenario_id": "null_naive", "family": "optional_stopping", "stopping_rule": "naive_repeated"},
        {"scenario_id": "null_fixed", "family": "optional_stopping", "stopping_rule": "fixed_n"},
        {"scenario_id": "null_spending", "family": "optional_stopping", "stopping_rule": "alpha_spending"},
        {"scenario_id": "power_mean", "family": "mean_shift", "stopping_rule": "anytime", "expand": {"effect_size": [0.05, 0.1, 0.2, 0.4, 0.6]}},
        {"scenario_id": "power_covariance", "family": "covariance_shift", "stopping_rule": "anytime", "effect_size": 0.4},
        {"scenario_id": "power_mixture", "family": "mixture_weight_shift", "stopping_rule": "anytime", "effect_size": 0.4},
        {"scenario_id": "power_mode_drop", "family": "mode_dropping", "stopping_rule": "anytime", "effect_size": 0.4},
        {"scenario_id": "power_rare_mode", "family": "rare_mode_change", "stopping_rule": "anytime", "effect_size": 0.4},
        {"scenario_id": "power_tail", "family": "tail_shift", "stopping_rule": "anytime", "effect_size": 0.4},
        {"scenario_id": "power_multimodal", "family": "multimodal_separation", "stopping_rule": "anytime", "effect_size": 0.4},
        {"scenario_id": "heavy_tail", "family": "heavy_tailed", "stopping_rule": "anytime", "effect_size": 0.4},
        {"scenario_id": "finite_reference", "family": "finite_reference_population", "stopping_rule": "anytime"},
        {"scenario_id": "reference_reuse", "family": "reference_reuse", "stopping_rule": "anytime", "reference_reuse": True},
        {"scenario_id": "near_equivalence", "family": "near_equivalence", "stopping_rule": "anytime", "effect_size": 0.0, "equivalence_margin": 0.5},
        {"scenario_id": "multiplicity", "family": "multiplicity", "stopping_rule": "anytime", "model_count": 10, "representation_count": 3},
        {"scenario_id": "representation", "family": "representation_disagreement", "stopping_rule": "anytime", "representation_count": 3, "effect_size": 0.4},
        {"scenario_id": "ranking", "family": "multi_model_ranking", "stopping_rule": "anytime", "expand": {"model_count": [2, 5, 10, 20, 50, 100]}, "effect_size": 0.08},
        {"scenario_id": "adaptive", "family": "adaptive_allocation", "stopping_rule": "anytime", "model_count": 10, "effect_size": 0.08},
    ]
    for tier, replicates, budget, workers in (
        ("quick", 24, 256, 2),
        ("medium", 512, 1000, 4),
        ("overnight", 4000, 5000, 4),
    ):
        resolved_defaults = {**defaults, "sample_budget": budget}
        write_yaml(
            CONFIG / f"synthetic_validation_{tier}.yaml",
            {
                "schema_version": "certgen.icml2027.synthetic_config.v1",
                "tier": tier,
                "master_seed": 20270809,
                "workers": workers,
                "replicates": replicates,
                "report_root": "reports/icml2027",
                "defaults": resolved_defaults,
                "scenarios": scenarios,
                **TRUTH,
            },
        )
    write_yaml(CONFIG / "synthetic_validation.yaml", yaml.safe_load((CONFIG / "synthetic_validation_quick.yaml").read_text()))
    write_yaml(
        CONFIG / "reviewer_attack_suite.yaml",
        {
            "schema_version": "certgen.icml2027.reviewer_attack_config.v1",
            "master_seed": 20270809,
            "replicates": 32,
            "alpha": 0.05,
            **TRUTH,
        },
    )
    write_yaml(
        CONFIG / "multi_model_scaling.yaml",
        {
            "schema_version": "certgen.icml2027.multi_model_config.v1",
            "master_seed": 20270809,
            "model_counts": [2, 5, 10, 20, 50, 100],
            "replicates": 2,
            "sample_budget": 128,
            "effect_spacing": 0.08,
            "alpha": 0.05,
            **TRUTH,
        },
    )
    write_yaml(
        CONFIG / "adaptive_allocation.yaml",
        {
            "schema_version": "certgen.icml2027.adaptive_config.v1",
            "policies": ["uniform", "round_robin", "uncertainty_first", "largest_confidence_width", "graph_frontier"],
            "master_seed": 20270809,
            "replicates": 4,
            "model_count": 8,
            "chunk_size": 16,
            "maximum_samples": 12000,
            "alpha": 0.05,
            **TRUTH,
        },
    )
    write_yaml(
        CONFIG / "baseline_synthetic.yaml",
        {
            "schema_version": "certgen.icml2027.baseline_study.v1",
            "alpha": 0.05,
            "master_seed": 20270809,
            "baseline_repetitions": 49,
            "block_size": 8,
            "family_size": 2,
            "looks": [4, 8, 16, 32],
            "true_mean": 0.0,
            **TRUTH,
        },
    )
    for name, margin_type, margin in (
        ("absolute", "absolute", 0.05),
        ("normalized", "normalized", 0.1),
        ("representation_specific", "representation_specific", 0.08),
    ):
        write_yaml(
            CONFIG / "equivalence" / f"{name}.yaml",
            {
                "schema_version": "certgen.icml2027.equivalence_config.v1",
                "margin_type": margin_type,
                "margin": margin,
                "alpha": 0.05,
                "exploratory_until_theory_verified": True,
                "claim_allowed": False,
            },
        )
    write_yaml(
        CONFIG / "compute_plan.yaml",
        {
            "model_count": 2,
            "sample_count": 10000,
            "reference_count": 10000,
            "gpu_count": 2,
            "session_limit_hours": 12,
            "planning_images_per_second": 3.0,
            "planning_extractor_throughput": 24.0,
            "expected_bytes_per_image": 50000,
            "feature_dimension": 768,
            "feature_space_count": 3,
            "overhead_fraction": 0.25,
            **PLAN,
        },
    )
    gates_false = {
        "source_verified": False,
        "license_reviewed": False,
        "revision_pinned": False,
        "adapter_validated": False,
        "reference_protocol_frozen": False,
        "feature_protocol_frozen": False,
        "compute_feasible": False,
        "released_sample_semantics_clear": False,
    }
    candidates = []
    for candidate_id, scores in (
        ("cifar10_cross_family", [5, 5, 2, 2, 1, 4, 2, 5, 2, 5, 3]),
        ("ffhq_released_samples", [4, 4, 5, 3, 2, 3, 4, 4, 3, 5, 4]),
        ("imagenet_class_conditional", [5, 5, 5, 2, 2, 5, 3, 5, 4, 5, 5]),
        ("public_text_to_image", [5, 5, 5, 3, 2, 5, 4, 5, 5, 5, 5]),
    ):
        candidates.append(
            {
                "candidate_id": candidate_id,
                "scores": dict(zip((
                    "scientific_value", "model_family_diversity", "benchmark_diversity", "public_availability",
                    "license_clarity", "compute_cost", "released_sample_availability", "feature_compatibility",
                    "preflight_complexity", "reviewer_value", "risk",
                ), scores, strict=True)),
                "gates": gates_false,
                "blocker": "source/license/adapter/protocol gates require real external verification",
                **PLAN,
            }
        )
    write_yaml(CONFIG / "study_selection.yaml", {"weights": {}, "candidates": candidates, **PLAN})

    cifar_study = {
        "schema_version": "certgen.icml2027.study.v1",
        "study_id": "icml2027_cifar_confirmatory_10k_v1",
        "status": "PROSPECTIVELY_FROZEN_WAITING_FOR_REAL_GPU_EXECUTION",
        "result_agnostic": True,
        "legacy_pilot_result_inspected": False,
        "benchmark": "cifar10_test_reference",
        "models": ["google_ddpm_cifar10_candidate", "frank_ddpm_ema_cifar10_candidate"],
        "feature_spaces": ["inception", "clip"],
        "robustness_feature_spaces_excluded_from_confirmatory_family": ["dinov2"],
        "maximum_sample_budget_per_model": 10000,
        "reference_sample_budget": 10000,
        "prefixes": [100, 250, 500, 1000, 2000, 5000, 10000],
        "prefix_policy": "single_frozen_maximum_stream_no_outcome_adaptive_selection",
        "stopping_rule": "anytime_valid_bounded_rbf_mean_confidence_sequence",
        "multiplicity": "bonferroni_across_two_confirmatory_hypotheses",
        "alpha": 0.05,
        "reference_draw": {"source": "existing canonical CIFAR-10 test materialization", "seed": 20270809, "without_replacement": True},
        "seed_plan": {"master_seed": 20270809, "derivation": "sha256(study_id,model_id,sample_index)"},
        "controls": ["null_reference_split", "obvious_gap_corruption"],
        "controls_in_confirmatory_multiplicity": False,
        "cost_accounting": "typed measured/planning_estimate/unknown schema",
        "equivalence": "not_in_confirmatory_v1",
        "immutable": True,
        "claim_allowed": False,
    }
    cifar_study["contract_hash"] = stable_hash(cifar_study)
    write_yaml(CONFIG / "cifar_confirmatory_10k_v1.yaml", cifar_study)
    write_yaml(
        CONFIG / "cifar_cross_family" / "contract.yaml",
        {
            "status": "BLOCKED_REQUIRES_REAL_SOURCE_VERIFICATION",
            "ddpm_pipeline_compatibility_assumed": False,
            "required": [
                "official source URL", "immutable revision", "license review", "checkpoint hashes", "documented sampler API",
                "seed determinism smoke", "32x32 RGB uint8 output conformance",
            ],
            **PLAN,
        },
    )
    for benchmark in ("ffhq", "imagenet", "text_to_image", "lsun"):
        write_yaml(
            CONFIG / "benchmarks" / benchmark / "prospective_contract.yaml",
            {
                "schema_version": "certgen.icml2027.benchmark_contract.v1",
                "benchmark_id": benchmark,
                "status": "BLOCKED_SOURCE_LICENSE_AND_PROTOCOL_VERIFICATION",
                "reference_source_contract": "unresolved; must be exact and authenticated",
                "license_access_gate": "human legal/license review required",
                "split_definition": "must be frozen before feature inspection",
                "resolution_policy": "benchmark-specific; unresolved",
                "preprocessing_policy": "feature-space registry controls; must be frozen",
                "model_eligibility": "public source, pinned revision, usable license, validated adapter",
                "feature_space_eligibility": ["inception_if_valid", "clip_if_valid", "dinov2_robustness_if_valid"],
                "sample_budgets": [100, 250, 500, 1000, 2000, 5000, 10000],
                "released_sample_support": True,
                "kaggle_input_builder": "python3 scripts/icml2027/build_kaggle_input.py --lane " + benchmark,
                "kaggle_notebook_factory": f"notebooks/kaggle/icml2027/{benchmark}",
                "local_importer": "python3 -m certgen released-samples import",
                "cpu_analysis_continuation": "python3 -m certgen icml2027 replay study",
                **PLAN,
            },
        )


def build_registries() -> None:
    write_yaml(
        REGISTRY / "claim_registry.yaml",
        {
            "schema_version": "certgen.icml2027.claim_registry.v1",
            "claims": [
                {"claim_id": "engineering_layer_executes", "level": "C0", "evidence": [], "claim_allowed": False},
                {"claim_id": "synthetic_calibration_observed", "level": "C1", "evidence": [], "claim_allowed": False},
                {"claim_id": "legacy_1k_observation", "level": "C2", "evidence": [], "claim_allowed": False},
                {"claim_id": "cifar_10k_confirmatory", "level": "C3", "evidence": [], "prospective_contract_hash": stable_hash(yaml.safe_load((CONFIG / "cifar_confirmatory_10k_v1.yaml").read_text())), "claim_allowed": False},
                {"claim_id": "real_multi_model_ranking", "level": "C4", "evidence": [], "claim_allowed": False},
                {"claim_id": "real_multi_benchmark", "level": "C5", "evidence": [], "claim_allowed": False},
                {"claim_id": "general_anytime_methodology", "level": "C6", "evidence": [], "theorem_verified": False, "claim_allowed": False},
            ],
            "claim_allowed": False,
        },
    )
    studies: list[dict[str, Any]] = []
    for study_id, status, config_name, derivation in (
        ("icml2027_synthetic_validity_v1", "FROZEN_SYNTHETIC", "synthetic_validation_quick.yaml", "synthetic_suite"),
        ("icml2027_cifar_confirmatory_10k_v1", "FROZEN_WAITING_GPU", "cifar_confirmatory_10k_v1.yaml", "planning_only"),
        ("icml2027_multi_model_synthetic_v1", "FROZEN_SYNTHETIC", "multi_model_scaling.yaml", "planning_only"),
        ("icml2027_representation_robustness_v1", "FROZEN_SYNTHETIC", "synthetic_validation_quick.yaml", "planning_only"),
        ("icml2027_multibench_planning_v1", "FROZEN_PLANNING", "study_selection.yaml", "planning_only"),
        ("icml2027_adaptive_ranking_v1", "FROZEN_EXPLORATORY_SYNTHETIC", "adaptive_allocation.yaml", "planning_only"),
        ("icml2027_equivalence_v1", "FROZEN_EXPLORATORY_SYNTHETIC", "equivalence/absolute.yaml", "planning_only"),
    ):
        path = CONFIG / config_name
        row = {
            "study_id": study_id,
            "status": status,
            "config_path": path.relative_to(ROOT).as_posix(),
            "config_sha256": file_sha256(path),
            "replay_derivation": derivation,
            "authenticated_inputs": [],
            "immutable": True,
            "claim_allowed": False,
        }
        row["study_contract_hash"] = stable_hash(row)
        studies.append(row)
    write_yaml(REGISTRY / "study_registry.yaml", {"schema_version": "certgen.icml2027.study_registry.v1", "studies": studies, "claim_allowed": False})
    legacy_study = ROOT / "artifacts/cvpr/study/cifar_integrity_minimal.yaml"
    write_yaml(
        REGISTRY / "legacy_pilot_link.yaml",
        {
            "schema_version": "certgen.icml2027.legacy_pilot_link.v1",
            "baseline_commit": "64175fc355175ff316d0213c811d543865d119d2",
            "study_path": "artifacts/cvpr/study/cifar_integrity_minimal.yaml",
            "study_file_sha256": file_sha256(legacy_study),
            "study_semantic_hash": "b6882b9e1be0b9f12868c47be44c0f41a522ed45c7a4529ceabd08f38cc991aa",
            "diagnostic_bundle_sha256": "d9b056f220fdd3ef87d5a0c2b41df0d8012452f0f912cb2e378bbc8f764e718d",
            "preflight_bundle_sha256": "d3a5b585383e12cfad82d94694fa1d8e2701de399617e8e515bafae57f33e93f",
            "purpose": "pilot_and_end_to_end_validation",
            "not_main_icml_confirmatory_study": True,
            "immutable": True,
            "claim_allowed": False,
        },
    )
    benchmark_rows = []
    for benchmark_id, status in (
        ("cifar10", "LEGACY_REFERENCE_VERIFIED_NEW_PROTOCOL_FROZEN"),
        ("ffhq", "BLOCKED_SOURCE_LICENSE_AND_PROTOCOL_VERIFICATION"),
        ("imagenet", "BLOCKED_ACCESS_LICENSE_AND_SPLIT_VERIFICATION"),
        ("text_to_image_public", "BLOCKED_PROMPT_REFERENCE_LICENSE_AND_MODEL_VERIFICATION"),
        ("lsun_optional", "BLOCKED_SOURCE_LICENSE_AND_SPLIT_VERIFICATION"),
        ("video_planning_only", "PLANNING_SKELETON_ONLY"),
    ):
        benchmark_rows.append(
            {
                "benchmark_id": benchmark_id,
                "verification_status": status,
                "source_url": "" if benchmark_id != "cifar10" else "https://www.cs.toronto.edu/~kriz/cifar.html",
                "revision": "unresolved" if benchmark_id != "cifar10" else "cifar-10-python canonical MD5",
                "license": "unresolved" if benchmark_id != "cifar10" else "source terms reviewed in legacy lane; new study reuses local authenticated reference",
                "redistribution": False,
                "authentication": benchmark_id == "cifar10",
                "sample_availability": "local_reference" if benchmark_id == "cifar10" else "unverified",
                "blocker": "" if benchmark_id == "cifar10" else "exact source/license/split/protocol review required",
                "human_action": "none for local planning" if benchmark_id == "cifar10" else "review exact official source and license, then pin immutable artifacts",
                "gates": {gate: benchmark_id == "cifar10" for gate in (
                    "source_verified", "license_reviewed", "revision_pinned", "adapter_validated", "reference_protocol_frozen",
                    "feature_protocol_frozen", "compute_feasible", "released_sample_semantics_clear",
                )},
                **PLAN,
            }
        )
    write_yaml(REGISTRY / "benchmark_registry.yaml", {"schema_version": "certgen.icml2027.benchmark_registry.v1", "benchmarks": benchmark_rows, "claim_allowed": False})
    dino = DinoV2Contract()
    models = [
        {
            "model_id": "dinov2_base_robustness",
            "verification_status": "SOURCE_AND_LICENSE_IDENTIFIED_ASSET_NOT_LOCALLY_AUTHENTICATED",
            "source_url": dino.source_url,
            "revision": dino.revision,
            "license": dino.license,
            "redistribution": False,
            "authentication": False,
            "sample_availability": "not_applicable_feature_extractor",
            "blocker": "authenticated pinned model asset and human redistribution review required",
            "human_action": "accept/review Apache-2.0 obligations, acquire pinned safetensors snapshot, build private asset manifest, run Kaggle preflight",
            "contract": dino.__dict__,
            "gates": {
                "source_verified": True, "license_reviewed": False, "revision_pinned": True, "adapter_validated": False,
                "reference_protocol_frozen": True, "feature_protocol_frozen": True, "compute_feasible": False,
                "released_sample_semantics_clear": True,
            },
            "claim_allowed": False,
        },
        {
            "model_id": "cifar_flow_matching_candidate",
            "verification_status": "BLOCKED_REQUIRES_REAL_SOURCE_VERIFICATION",
            "source_url": "unresolved",
            "revision": "unresolved",
            "license": "unresolved",
            "redistribution": False,
            "authentication": False,
            "sample_availability": "unverified",
            "blocker": "adapter and sampler semantics cannot be established from repository context",
            "human_action": "provide official source, revision, license, checkpoint hashes, and sampling documentation",
            "gates": {gate: False for gate in (
                "source_verified", "license_reviewed", "revision_pinned", "adapter_validated", "reference_protocol_frozen",
                "feature_protocol_frozen", "compute_feasible", "released_sample_semantics_clear",
            )},
            "claim_allowed": False,
        },
    ]
    write_yaml(REGISTRY / "model_registry.yaml", {"schema_version": "certgen.icml2027.model_registry.v1", "models": models, "claim_allowed": False})
    write_yaml(
        REGISTRY / "feature_space_registry.yaml",
        {
            "schema_version": "certgen.icml2027.feature_space_registry.v1",
            "feature_spaces": [
                {"feature_space_id": "inception", "role": "confirmatory_cifar", "legacy_contract_reused": True, "claim_allowed": False},
                {"feature_space_id": "clip", "role": "confirmatory_cifar", "legacy_contract_reused": True, "claim_allowed": False},
                {"feature_space_id": "dinov2_base", "role": "robustness_only", "contract": dino.__dict__, "preprocessing_hash": dino.preprocessing_hash, "claim_allowed": False},
            ],
            "consensus_policies": ["unanimous_direction", "all_representations_equivalent", "any_conflict_blocks", "majority_direction_exploratory"],
            "claim_allowed": False,
        },
    )
    baseline_rows = []
    for baseline_id, contract in BASELINES.items():
        baseline_rows.append(
            {
                "baseline_id": baseline_id,
                "method_family": contract["method_family"],
                "implementation": "certgen.icml2027.baselines.runner",
                "package": "certgen/numpy/scipy",
                "version": "repository_pinned_environment",
                "hyperparameters": "study_config",
                "supports_cached_features": True,
                "supports_streaming": contract["supports_streaming"],
                "supports_multi_model": baseline_id in {"fixed_bonferroni", "certgen_anytime"},
                "requires_gpu": False,
                "claim_allowed": False,
            }
        )
    write_yaml(REGISTRY / "baseline_registry.yaml", {"schema_version": "certgen.icml2027.baseline_registry.v1", "baselines": baseline_rows, "claim_allowed": False})
    write_yaml(
        REGISTRY / "statistical_method_registry.yaml",
        {
            "schema_version": "certgen.icml2027.statistical_method_registry.v1",
            "methods": [
                {"method_id": "bounded_anytime_union_cs", "validity": "conservative_anytime_union_bound", "assumptions": ["bounded observations", "prospectively fixed stream", "declared multiplicity"], "claim_allowed": False},
                {"method_id": "bonferroni", "validity": "FWER_under_arbitrary_dependence", "claim_allowed": False},
                {"method_id": "holm", "validity": "FWER_under_arbitrary_dependence", "claim_allowed": False},
                {"method_id": "benjamini_hochberg", "validity": "exploratory_dependency_conditions_unverified", "claim_allowed": False},
                {"method_id": "equivalence_anytime", "validity": "EXPLORATORY_UNTIL_THEORY_VERIFIED", "claim_allowed": False},
                {"method_id": "adaptive_graph_frontier", "validity": "EXPLORATORY_NOT_PROVEN", "claim_allowed": False},
            ],
            "claim_allowed": False,
        },
    )
    run_registry_path = REGISTRY / "run_registry.yaml"
    preserve_completed_registry = False
    if run_registry_path.is_file():
        existing_registry = yaml.safe_load(run_registry_path.read_text(encoding="utf-8"))
        existing_runs = existing_registry.get("runs", []) if isinstance(existing_registry, dict) else []
        preserve_completed_registry = bool(existing_runs) and all(
            isinstance(run, dict) and run.get("status") == "COMPLETED" for run in existing_runs
        )
    if not preserve_completed_registry:
        write_yaml(
            run_registry_path,
            {
                "schema_version": "certgen.icml2027.run_registry.v1",
                "runs": [
                    {"run_id": "cpu_tier_a_quick", "command": "python3 -m certgen icml2027 synthetic run --config configs/icml2027/synthetic_validation_quick.yaml --out-dir artifacts/icml2027/synthetic_validation/quick", "status": "PLANNED", **TRUTH},
                    {"run_id": "cpu_tier_b_medium", "command": "python3 -m certgen icml2027 synthetic run --config configs/icml2027/synthetic_validation_medium.yaml --out-dir artifacts/icml2027/synthetic_validation/medium", "status": "PLANNED", **TRUTH},
                    {"run_id": "cpu_tier_c_overnight", "command": "python3 -m certgen icml2027 synthetic run --config configs/icml2027/synthetic_validation_overnight.yaml --out-dir artifacts/icml2027/synthetic_validation/overnight", "status": "PLANNED_LONG", **TRUTH},
                ],
                "claim_allowed": False,
            },
        )


def build_docs() -> None:
    documents = {
        "ICML2027_RESEARCH_MASTER_PLAN.md": """
# ICML 2027 research master plan

This layer is prospective, separate from the sealed CIFAR-10 1k pilot, and result-agnostic. It supports C0 engineering validation and C1 synthetic validation now. Real claims remain blocked until authenticated GPU artifacts pass source, license, identity, protocol, and evidence gates.

Execution order: preserve the legacy pilot; run deterministic synthetic calibration; validate baselines and reviewer attacks; freeze the CIFAR 10k contract; execute the existing Kaggle diagnostic/preflight; run 10k generation and features once prerequisites pass; add DINOv2 as robustness only; add cross-family and benchmark breadth only after source/license/adapter gates pass.

All planning and synthetic outputs set `claim_allowed=false`. No final paper prose or fake result rows belong here.
""",
        "ICML2027_STATISTICAL_ANALYSIS_PLAN.md": """
# Statistical analysis plan

Primary objects are prospectively ordered bounded block-level feature-distance differences. The core confidence sequence uses a conservative summable-alpha union construction. Familywise error is controlled prospectively with Bonferroni or Holm; fixed alpha splits are supported. Naive repeated testing is a negative control, not a valid sequential comparator.

Report Type-I error, FWER, simultaneous coverage, decision states, stopping distributions with censoring, power, unresolved fraction, sample-to-decision, and typed cost-to-decision. Reused references, finite populations, multiple representations, equivalence margins, and adaptive allocation are separately declared. Practical equivalence and data-dependent graph-frontier allocation remain exploratory until their theory contracts are verified.
""",
        "ICML2027_THEORY_ENGINEERING_CHECKLIST.md": """
# Theory engineering checklist

- Define the filtration, bounded observation, stream order, reference-sampling mechanism, and stopping time.
- Verify the confidence-sequence boundary and simultaneous family allocation.
- Separate finite-reference and reused-reference dependence from independent-stream assumptions.
- Define ranking edge orientation, transitivity assumptions, cycles, and unresolved edges.
- Prove or explicitly withhold validity for equivalence and adaptive allocation.
- Connect every code assumption to an executable check and counterexample fixture.
- Never treat Monte Carlo calibration as proof.
""",
        "ICML2027_REVIEWER_ATTACK_MATRIX.md": """
# Reviewer attack matrix

The executable suite covers optional stopping, bandwidth/alpha/reference/budget/stream/seed sensitivity, preprocessing and normalization changes, exact and near duplicates, compression/corruption, reference reuse, finite populations, near ties, mode/rare-mode changes, dimension, heavy tails, multi-model scaling, representation conflicts, precision, and zero variance. Every row records the question, setup, invariant, rule, artifacts, and `claim_allowed=false`.
""",
        "ICML2027_BENCHMARK_EXPANSION_PLAN.md": """
# Benchmark expansion plan

CIFAR-10 remains the first executable lane. FFHQ, ImageNet class-conditional, and public text-to-image lanes have complete prospective contract skeletons but are NO-GO until exact source, license/access, split, reference, model, preprocessing, released-sample semantics, and compute gates pass. LSUN is optional. Video remains planning-only.
""",
        "ICML2027_MODEL_EXPANSION_PLAN.md": """
# Model expansion plan

Preserve the two registered CIFAR DDPM candidates for the prospective 10k extension. Add DINOv2 only as a robustness representation. A flow-matching/cross-family generator is blocked because its exact source, revision, license, checkpoint and sampler semantics are not established. Never infer `DDPMPipeline` compatibility.
""",
        "ICML2027_COMPUTE_BUDGET_PLAN.md": """
# Compute budget plan

All numbers generated before authenticated throughput exists are labeled `PLANNING_ESTIMATE_NOT_MEASURED`. Generation, feature extraction, dependency installation, model loading, disk, ZIP size, and copyback are accounted separately. CPU quick, medium, and overnight suites are resumable and deterministic. GPU stages use T4 x2 with no one-GPU fallback.
""",
        "ICML2027_EXECUTION_ORDER.md": """
# Execution order

1. Run and import the existing Kaggle environment diagnostic.
2. Run and import the existing two-checkpoint preflight.
3. Complete the immutable legacy 1k pilot path.
4. Build and run the prospectively frozen CIFAR 10k maximum stream once gates pass.
5. Extract Inception and CLIP features; run local replay, baselines, prefix and cost analyses.
6. Authenticate the pinned DINOv2 asset, run DINO preflight/features, and analyze representation agreement outside the confirmatory family.
7. Resolve cross-family and multibench source/license/adapter gates before scheduling those GPU lanes.
""",
        "RELEASED_SAMPLE_IMPORT_GUIDE.md": """
# Released-sample import guide

Prepare source metadata without asserting undocumented sampling semantics. Run `released-samples validate`, build a hash-bound manifest, then import into a new empty directory. Validation rejects traversal, absolute paths, symlinks/special members, duplicate/case-colliding members, non-images, decode failures, membership/count/hash mismatches, and duplicate image content. Sample IDs derive from source/revision/archive/image hashes and ordinal, never from trusted filenames.

Official released samples and locally generated samples require an explicit prospective compatibility judgment before sharing a confirmatory family.
""",
        "DINOV2_KAGGLE_RUNBOOK.md": """
# DINOv2 Kaggle runbook

The robustness lane pins `facebook/dinov2-base` at revision `f9e44c814b77203eaa57a6bdbbd535f21ede1415`, uses `AutoImageProcessor` plus `Dinov2Model`, extracts the CLS token (768 dimensions), and freezes the pinned processor's 256-short-edge resize, 224 center crop, bicubic resampling, RGB conversion, rescaling and ImageNet normalization. The official model card and Hugging Face repository identify Apache-2.0; redistribution remains disabled until human review.

Acquire the exact pinned snapshot into a private Kaggle asset, inventory every file and SHA-256, record license approval, build the preflight input, run the T4 x2 preflight, import its authenticated ZIP, then build/run feature extraction. DINOv2 is robustness-only and not part of the frozen pilot or CIFAR 10k confirmatory family.
""",
        "CIFAR_CROSS_FAMILY_RUNBOOK.md": """
# CIFAR cross-family runbook

Status: `BLOCKED_REQUIRES_REAL_SOURCE_VERIFICATION`. Provide the official repository, immutable revision, license, checkpoint hashes, model construction, scheduler/sampler algorithm and parameters, conditioning, seed semantics, and expected 32x32 RGB output. Implement the `CrossFamilyGenerator` protocol and run two-seed deterministic conformance on T4 x2. Do not assume Diffusers `DDPMPipeline` compatibility. Only then can a generation input package exist.
""",
    }
    for name, content in documents.items():
        write_text(DOCS / name, content + "\n`claim_allowed=false`.\n")
    theory = {
        "ANYTIME_VALID_ASSUMPTIONS.md": ("T-AV-1", "bounded adapted observations; prospectively fixed stream; valid confidence sequence", "adaptive allocation beyond inherited fixed schedules"),
        "MULTIPLICITY_ASSUMPTIONS.md": ("T-MULT-1", "family frozen before inspection; Bonferroni/Holm arbitrary-dependence control", "graph-aware and FDR dependency conditions"),
        "PARTIAL_ORDER_ASSUMPTIONS.md": ("T-PO-1", "edge direction is antisymmetric; cycles are invalid rather than silently removed", "population-level transitivity across representations"),
        "FINITE_REFERENCE_ASSUMPTIONS.md": ("T-FR-1", "sampling design and reuse declared; without-replacement dependence retained", "tight finite-population anytime boundary"),
        "EQUIVALENCE_ASSUMPTIONS.md": ("T-EQ-1", "margin frozen before data; CS contained within margin for equivalence", "full dual-error proof under sequential multiplicity"),
        "ADAPTIVE_ALLOCATION_VALIDITY.md": ("T-AA-1", "uniform/round-robin inherit fixed-edge validity; stopped edges receive no more budget", "uncertainty, width and graph-frontier allocation validity"),
    }
    for name, (statement, assumptions, unresolved) in theory.items():
        write_text(
            DOCS / "theory" / name,
            f"""# {name.removesuffix('.md').replace('_', ' ').title()}

- `statement_id`: `{statement}`
- `formal_objects`: filtered bounded streams, stopping times, family allocations, and directed comparison graphs
- `assumptions`: {assumptions}
- `dependencies`: frozen study, sample identities, feature/preprocessing hashes, multiplicity registry
- `what_code_assumes`: fail-closed bounded values and prospective configuration
- `what_simulations_validate`: implementation behavior and finite-grid calibration only
- `what_remains_unproven`: {unresolved}
- `counterexamples`: naive repeated testing, outcome-adaptive prefixes, undeclared reuse, cyclic directions
- `proof_status`: `NOT_MARKED_COMPLETE`
- `claim_allowed`: `false`
""",
        )


RUNBOOK_FIELDS = (
    "purpose", "prerequisite_state", "input_builder", "input_ZIP", "input_SHA256", "package_type", "notebook",
    "accelerator", "GPU_count", "internet_mode", "dependency_profile", "private_assets", "disk_expectation",
    "RAM_VRAM_expectation", "planning_runtime", "restart_behavior", "expected_output", "copyback", "local_resume",
    "failure_recovery", "immutable_fields", "claim_allowed",
)


def build_runbooks() -> None:
    existing = {
        "current_diagnostic": ("environment diagnostic", "READY", "python3 -m certgen kaggle build-input --stage diagnostic --json", "artifacts/cvpr/kaggle_inputs/diagnostic/certgen_kaggle_environment_diagnostic_input.zip", "d9b056f220fdd3ef87d5a0c2b41df0d8012452f0f912cb2e378bbc8f764e718d", "notebooks/kaggle/certgen_kaggle_environment_diagnostic_t4x2.ipynb"),
        "current_preflight": ("legacy two-model preflight", "READY_AFTER_DIAGNOSTIC", "python3 -m certgen kaggle build-input --stage preflight --json", "artifacts/cvpr/kaggle_inputs/preflight/certgen_cvpr_preflight_input.zip", "d3a5b585383e12cfad82d94694fa1d8e2701de399617e8e515bafae57f33e93f", "notebooks/kaggle/certgen_cvpr_checkpoint_preflight_t4x2.ipynb"),
        "current_1k_generation": ("immutable pilot generation", "BLOCKED_PENDING_PREFLIGHT_IMPORT", "python3 -m certgen kaggle build-input --stage generation --scale 1k --json", "BLOCKED_NOT_BUILT", "", "notebooks/kaggle/certgen_cvpr_generation_1k_t4x2.ipynb"),
        "current_1k_features": ("immutable pilot features", "BLOCKED_PENDING_GENERATION_IMPORT", "python3 -m certgen kaggle build-input --stage features --scale 1k --json", "BLOCKED_NOT_BUILT", "", "notebooks/kaggle/certgen_cvpr_feature_extraction_t4x2.ipynb"),
    }
    prospective = {
        "dinov2_preflight": ("DINOv2 robustness preflight", "BLOCKED_PINNED_PRIVATE_ASSET_AND_LICENSE_REVIEW", "python3 scripts/icml2027/build_kaggle_input.py --lane dinov2_preflight", "BLOCKED_NOT_BUILT", "", "notebooks/kaggle/icml2027/certgen_icml2027_dinov2_preflight_t4x2.ipynb"),
        "dinov2_features": ("DINOv2 robustness features", "BLOCKED_PREFLIGHT_AND_IMAGE_INPUT", "python3 scripts/icml2027/build_kaggle_input.py --lane dinov2_features", "BLOCKED_NOT_BUILT", "", "notebooks/kaggle/icml2027/certgen_icml2027_dinov2_features_t4x2.ipynb"),
        "cross_family_preflight": ("cross-family adapter conformance", "BLOCKED_REQUIRES_REAL_SOURCE_VERIFICATION", "python3 scripts/icml2027/build_kaggle_input.py --lane cifar_cross_family_preflight", "BLOCKED_NOT_BUILT", "", "notebooks/kaggle/icml2027/certgen_icml2027_cifar_cross_family_preflight_t4x2.ipynb"),
        "cifar_10k_generation": ("prospective CIFAR 10k maximum-stream generation", "BLOCKED_LEGACY_PREFLIGHT_AND_10K_BUILD_GATE", "python3 scripts/icml2027/build_kaggle_input.py --lane cifar_10k_generation", "BLOCKED_NOT_BUILT", "", "notebooks/kaggle/icml2027/certgen_icml2027_cifar_10k_generation_t4x2.ipynb"),
        "cifar_10k_features": ("prospective CIFAR 10k Inception/CLIP features", "BLOCKED_10K_GENERATION_IMPORT", "python3 scripts/icml2027/build_kaggle_input.py --lane cifar_10k_features", "BLOCKED_NOT_BUILT", "", "notebooks/kaggle/icml2027/certgen_icml2027_cifar_10k_features_t4x2.ipynb"),
        "released_sample_features": ("authenticated released-sample features", "BLOCKED_RELEASED_SAMPLE_IMPORT", "python3 scripts/icml2027/build_kaggle_input.py --lane released_sample_features", "BLOCKED_NOT_BUILT", "", "notebooks/kaggle/icml2027/certgen_icml2027_released_sample_features_t4x2.ipynb"),
        "ffhq": ("FFHQ prospective lane", "BLOCKED_SOURCE_LICENSE_PROTOCOL", "python3 scripts/icml2027/build_kaggle_input.py --lane ffhq", "BLOCKED_NOT_BUILT", "", "notebooks/kaggle/icml2027/ffhq/certgen_icml2027_ffhq_t4x2.ipynb"),
        "imagenet": ("ImageNet class-conditional prospective lane", "BLOCKED_ACCESS_LICENSE_PROTOCOL", "python3 scripts/icml2027/build_kaggle_input.py --lane imagenet", "BLOCKED_NOT_BUILT", "", "notebooks/kaggle/icml2027/imagenet/certgen_icml2027_imagenet_t4x2.ipynb"),
        "text_to_image": ("public text-to-image prospective lane", "BLOCKED_PROMPT_SOURCE_LICENSE_MODEL_PROTOCOL", "python3 scripts/icml2027/build_kaggle_input.py --lane text_to_image", "BLOCKED_NOT_BUILT", "", "notebooks/kaggle/icml2027/text_to_image/certgen_icml2027_text_to_image_t4x2.ipynb"),
    }
    rows = []
    for lane, values in {**existing, **prospective}.items():
        purpose, prerequisites, builder, input_zip, sha, notebook = values
        row = {
            "purpose": purpose,
            "prerequisite_state": prerequisites,
            "input_builder": builder,
            "input_ZIP": input_zip,
            "input_SHA256": sha or "NOT_AVAILABLE_BLOCKED",
            "package_type": "authenticated_stage_input_or_blocked_plan",
            "notebook": notebook,
            "accelerator": "Kaggle T4 x2",
            "GPU_count": 2,
            "internet_mode": "internet_on_for_dependencies; model/data assets authenticated separately",
            "dependency_profile": "exact stage lock plus restart marker",
            "private_assets": "required only where source/license/asset registry says so",
            "disk_expectation": "planner estimate; verify preflight before launch",
            "RAM_VRAM_expectation": "planner estimate; fail closed on preflight",
            "planning_runtime": "PLANNING_ESTIMATE_NOT_MEASURED",
            "restart_behavior": "resume deterministic completed shards; never mutate configuration",
            "expected_output": f"certgen_icml2027_{lane}_output.zip",
            "copyback": "download ZIP, retain SHA-256, validate and import locally",
            "local_resume": "python3 scripts/run_all_available_cpu_stages.py --resume --explain plus ICML replay",
            "failure_recovery": "preserve input/config/logs; repair only failed stage; rerun exact immutable identity",
            "immutable_fields": "study/model/revision/seed/preprocessing/shards/output schema",
            "claim_allowed": False,
        }
        rows.append({"lane": lane, **row})
        table = "\n".join(f"| `{field}` | {row[field]} |" for field in RUNBOOK_FIELDS)
        write_text(DOCS / "runbooks" / lane / "RUNBOOK.md", f"# {purpose}\n\n| Field | Value |\n|---|---|\n{table}")
    launch_lines = [
        "# CertGen ICML 2027 Kaggle launchboard",
        "",
        "All runtimes are planning estimates until authenticated measurements exist. `claim_allowed=false`.",
        "",
        "| Order | Study | Stage | Status | Prerequisites | Notebook | Input builder | Input ZIP | SHA | GPU | Internet | Private assets | Runtime | Output | Copyback | Local resume |",
        "|---:|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for order, row in enumerate(rows, start=1):
        launch_lines.append(
            f"| {order} | `{row['lane']}` | {row['purpose']} | `{row['prerequisite_state']}` | {row['prerequisite_state']} | `{row['notebook']}` | `{row['input_builder']}` | `{row['input_ZIP']}` | `{row['input_SHA256']}` | T4 | 2 | {row['internet_mode']} | {row['private_assets']} | {row['planning_runtime']} | `{row['expected_output']}` | {row['copyback']} | {row['local_resume']} |"
        )
    write_text(ROOT / "CERTGEN_ICML2027_KAGGLE_LAUNCHBOARD.md", "\n".join(launch_lines))


def build_result_schemas() -> None:
    schemas = {
        "main_result_rows.csv": ["study_id", "comparison", "feature_space", "decision", "evidence_hash", "claim_allowed"],
        "baseline_rows.csv": ["study_id", "baseline_id", "comparison", "estimate", "decision", "evidence_hash", "claim_allowed"],
        "representation_rows.csv": ["study_id", "comparison", "feature_space", "decision", "classification", "claim_allowed"],
        "cost_rows.csv": ["study_id", "stage", "measurement_status", "GPU_seconds", "CPU_seconds", "samples_to_decision", "claim_allowed"],
        "ablation_rows.csv": ["study_id", "ablation_id", "frozen_before_run", "decision", "evidence_hash", "claim_allowed"],
        "benchmark_rows.csv": ["study_id", "benchmark_id", "status", "evidence_hash", "claim_allowed"],
        "model_rows.csv": ["study_id", "model_id", "revision", "status", "evidence_hash", "claim_allowed"],
    }
    for name, fields in schemas.items():
        write_csv(ARTIFACTS / "result_schemas" / name, [], fields)


def build_source_queue() -> None:
    models = yaml.safe_load((REGISTRY / "model_registry.yaml").read_text())["models"]
    benchmarks = yaml.safe_load((REGISTRY / "benchmark_registry.yaml").read_text())["benchmarks"]
    rows = []
    for record in [*models, *benchmarks]:
        rows.append(
            {
                "record_id": record.get("model_id") or record.get("benchmark_id"),
                "verification_status": record["verification_status"],
                "source_url": record.get("source_url", ""),
                "revision": record.get("revision", ""),
                "license": record.get("license", ""),
                "redistribution": record.get("redistribution", False),
                "authentication": record.get("authentication", False),
                "sample_availability": record.get("sample_availability", ""),
                "blocker": record.get("blocker", ""),
                "human_action": record.get("human_action", ""),
                "planning_only": True,
                "claim_allowed": False,
            }
        )
    write_csv(REPORTS / "SOURCE_LICENSE_VERIFICATION_QUEUE.csv", rows)


def build_baseline_capture() -> None:
    baseline_start = "2026-08-09T13:37:22.325990Z"
    report = f"""# CertGen ICML 2027 sealed baseline

- Capture start (UTC): `{baseline_start}`
- Branch: `main`
- HEAD: `64175fc355175ff316d0213c811d543865d119d2`
- Commit subject: `Seal CertGen Kaggle execution path and asset loading`
- Remote: `origin https://github.com/Saket-Maganti/certgen.git`
- Initial worktree: three untracked prompt-pack Markdown files only; preserved and excluded from implementation scope
- Python: `{sys.version.replace(chr(10), ' ')}`
- Platform: `{platform.platform()}` / `{platform.machine()}`
- Default pytest: `309 passed, 4 deselected`
- Explicit integration audits: `4 passed, 309 deselected`
- Execution-path/security tests: `18 passed`
- Historical full mypy debt: `99 errors in 33 files` (comparison ceiling)
- Changed-code baseline mypy: pass
- Ruff: pass
- Frozen pilot study file SHA-256: `346f0bea70d94803bd9da2793153496a6b0c1fe839174e8d2049773f5bfcc5ae`
- Frozen pilot semantic study hash: `b6882b9e1be0b9f12868c47be44c0f41a522ed45c7a4529ceabd08f38cc991aa`
- Diagnostic bundle SHA-256: `d9b056f220fdd3ef87d5a0c2b41df0d8012452f0f912cb2e378bbc8f764e718d`
- Preflight bundle SHA-256: `d3a5b585383e12cfad82d94694fa1d8e2701de399617e8e515bafae57f33e93f`

Compile/import, full one-process pytest, explicit integration wrappers, trusted bootstrap, exact identity, asset resolution, wheelhouse compatibility, deterministic notebooks, package security, provenance, replay, privacy, secrets, restricted assets, release safety, final-pre-run, maximum-ceiling, CPU-execution, Kaggle-launch, universal-Kaggle, Ruff, changed-code mypy, historical mypy debt capture, and `git diff --check` all completed. The detailed commands and runtimes are in the ICML-specific CSV/JSONL ledger.

`claim_allowed=false`.
"""
    write_text(REPORTS / "CERTGEN_ICML2027_BASELINE.md", report)
    lines = _git("ls-tree", "-rl", "HEAD").splitlines()
    rows = []
    for line in lines:
        metadata, path = line.split("\t", 1)
        mode, kind, object_hash, size = metadata.split()
        rows.append(
            {
                "path": path,
                "git_mode": mode,
                "object_type": kind,
                "git_object_hash": object_hash,
                "size_bytes": int(size),
                "baseline_commit": "64175fc355175ff316d0213c811d543865d119d2",
                "immutable_legacy": path.startswith(("artifacts/cvpr/", "registry/cvpr/", "configs/cvpr/", "data/results/")),
                "claim_allowed": False,
            }
        )
    write_csv(REPORTS / "CERTGEN_ICML2027_ARTIFACT_INVENTORY.csv", rows)


def build_planning_reports() -> None:
    current_state_path = REPORTS / "CERTGEN_ICML2027_CURRENT_STATE.json"
    if current_state_path.is_file():
        existing_state = json.loads(current_state_path.read_text(encoding="utf-8"))
        if isinstance(existing_state, dict) and existing_state.get("final_status"):
            return
    report_names = (
        "CERTGEN_ICML2027_MAXIMIZATION_AUDIT.md",
        "CERTGEN_ICML2027_CPU_EXECUTION_REPORT.md",
        "CERTGEN_ICML2027_GPU_RUNBOOK_READINESS.md",
        "CERTGEN_ICML2027_SYNTHETIC_VALIDITY_REPORT.md",
        "CERTGEN_ICML2027_BASELINE_COVERAGE.md",
        "CERTGEN_ICML2027_REVIEWER_ATTACK_REPORT.md",
        "CERTGEN_ICML2027_MULTI_MODEL_REPORT.md",
        "CERTGEN_ICML2027_ADAPTIVE_REPORT.md",
        "CERTGEN_ICML2027_REPRESENTATION_REPORT.md",
        "CERTGEN_ICML2027_RELEASED_SAMPLE_REPORT.md",
        "CERTGEN_ICML2027_BENCHMARK_READINESS.md",
        "CERTGEN_ICML2027_MODEL_READINESS.md",
        "CERTGEN_ICML2027_COMPUTE_PLAN.md",
        "CERTGEN_ICML2027_BLOCKERS.md",
    )
    for name in report_names:
        title = name.removesuffix(".md").replace("CERTGEN_ICML2027_", "").replace("_", " ").title()
        write_text(
            REPORTS / name,
            f"# CertGen ICML 2027 — {title}\n\nThis report is generated prospectively and is refreshed after actual CPU execution. It contains no real generator evidence. `claim_allowed=false`.\n",
        )
    current = {
        "schema_version": "certgen.icml2027.current_state.v1",
        "legacy_pilot_preserved": True,
        "synthetic_engine_ready": True,
        "synthetic_cpu_runs_completed": [],
        "null_calibration_completed": False,
        "optional_stopping_completed": False,
        "power_curves_completed": False,
        "multi_model_scaling_completed": False,
        "baseline_suite_ready": True,
        "baseline_cpu_runs_completed": False,
        "equivalence_infrastructure_ready": True,
        "multiplicity_suite_ready": True,
        "representation_analysis_ready": True,
        "adaptive_scheduler_ready": True,
        "released_sample_import_ready": True,
        "dinov2_infrastructure_ready": True,
        "cross_family_cifar_infrastructure_ready": True,
        "cifar_10k_study_frozen": True,
        "multibench_infrastructure_ready": True,
        "reviewer_attack_suite_completed": False,
        "cpu_runs_remaining": ["quick", "medium", "overnight"],
        "gpu_runs_required": True,
        "claim_allowed": False,
        "next_real_action": "run existing authenticated Kaggle diagnostic T4x2",
    }
    write_json(REPORTS / "CERTGEN_ICML2027_CURRENT_STATE.json", current)


def main() -> int:
    for directory in (CONFIG, REGISTRY, REPORTS, ARTIFACTS, NOTEBOOKS, TESTS, DOCS, ROOT / "scripts/icml2027"):
        directory.mkdir(parents=True, exist_ok=True)
    build_configs()
    build_registries()
    build_docs()
    build_runbooks()
    build_result_schemas()
    build_source_queue()
    build_baseline_capture()
    build_planning_reports()
    generate_notebooks(NOTEBOOKS)
    payload = {
        "schema_version": "certgen.icml2027.research_layer_build.v1",
        "directories": [str(path.relative_to(ROOT)) for path in (CONFIG, REGISTRY, REPORTS, ARTIFACTS, NOTEBOOKS, TESTS, DOCS)],
        "planning_only": True,
        "claim_allowed": False,
    }
    write_json(ARTIFACTS / "research_layer_build.json", payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
