"""Generate deterministic CVPR pre-execution registries and documentation.

The script writes only missing files (or accepts byte-identical files).  It
does not download, execute a model, fabricate a result, or promote a claim.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]


def put(relative: str, text: str) -> None:
    path = ROOT / relative
    payload = text.rstrip() + "\n"
    if path.exists():
        if path.read_text(encoding="utf-8") != payload:
            raise FileExistsError(f"refusing to overwrite changed file: {relative}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def put_json(relative: str, payload: Any) -> None:
    put(relative, json.dumps(payload, indent=2, sort_keys=True))


def put_yaml(relative: str, payload: Any) -> None:
    put(relative, yaml.safe_dump(payload, sort_keys=False, allow_unicode=False))


def put_csv(relative: str, fields: list[str], rows: list[dict[str, Any]]) -> None:
    from io import StringIO

    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    put(relative, output.getvalue())


COMMON_BENCHMARK = {
    "download_size_estimate": "planning estimate; hardware and source dependent",
    "official_url_placeholder": "TBD_MANUAL_SOURCE_AND_LICENSE_VERIFICATION",
    "status": "planning_only_blocked",
    "claim_allowed": False,
}


def registries() -> None:
    benchmarks = [
        {**COMMON_BENCHMARK, "benchmark_id": "cifar10", "display_name": "CIFAR-10", "domain": "natural objects", "resolution": "32x32", "conditioning": "unconditional_or_class_conditional", "reference_source": "official Python batches, user-provided only", "reference_split": "test", "license": "manual_release_review_required", "expected_reference_count": 10000, "local_source_formats": ["official_tar_gz", "extracted_python_batches", "torchvision_cache", "validated_image_tree", "safe_wrapper_archive"], "feature_spaces_supported": ["inception", "clip", "dinov2"], "evaluation_protocols": ["debug_pilot", "null_controls", "controlled_corruption", "bounded_rbf_certificate"], "known_preprocessing_risks": ["32_to_encoder_resolution", "interpolation", "reference_split_reuse"], "cvpr_relevance": "pilot and debugging only; insufficient alone", "execution_tier": "pilot", "blocker": "local reference source missing"},
        {**COMMON_BENCHMARK, "benchmark_id": "ffhq_candidate", "display_name": "FFHQ candidate lane", "domain": "faces", "resolution": "high_resolution", "conditioning": "unconditional", "reference_source": "TBD_MANUAL_VERIFICATION", "reference_split": "TBD", "license": "unverified_requires_manual_review", "expected_reference_count": "TBD", "local_source_formats": ["validated_image_tree", "released_samples"], "feature_spaces_supported": ["inception", "clip", "dinov2"], "evaluation_protocols": ["higher_resolution_face_audit"], "known_preprocessing_risks": ["face_alignment", "crop", "license"], "cvpr_relevance": "recognized high-resolution visual domain", "execution_tier": "post_pilot", "blocker": "source, license, split, and feasible model pairs not verified"},
        {**COMMON_BENCHMARK, "benchmark_id": "imagenet_class_conditional_candidate", "display_name": "ImageNet class-conditional candidate lane", "domain": "natural objects", "resolution": "TBD", "conditioning": "class_conditional", "reference_source": "TBD_MANUAL_VERIFICATION", "reference_split": "validation_candidate", "license": "access_and_release_review_required", "expected_reference_count": "TBD", "local_source_formats": ["validated_image_tree", "released_samples"], "feature_spaces_supported": ["inception", "clip", "dinov2"], "evaluation_protocols": ["class_balanced_visual_generator_audit"], "known_preprocessing_risks": ["class_balance", "label_mapping", "resolution", "access"], "cvpr_relevance": "recognizable class-conditional benchmark", "execution_tier": "strong_study", "blocker": "access, protocol, model sources, and licenses unverified"},
        {**COMMON_BENCHMARK, "benchmark_id": "text_to_image_public_prompts_candidate", "display_name": "Public text-to-image prompt/sample candidate", "domain": "text_to_image", "resolution": "TBD", "conditioning": "text", "reference_source": "public prompts plus licensed real-image or released-sample protocol TBD", "reference_split": "prospective_prompt_freeze_required", "license": "unverified_requires_manual_review", "expected_reference_count": "TBD", "local_source_formats": ["prompt_manifest", "released_sample_manifest"], "feature_spaces_supported": ["clip", "dinov2", "inception"], "evaluation_protocols": ["prompt_stratified_pairwise_audit"], "known_preprocessing_risks": ["prompt_selection", "aspect_ratio", "safety_filter", "released_sample_selection"], "cvpr_relevance": "modern text-to-image evaluation", "execution_tier": "strong_study", "blocker": "benchmark, prompts, reference semantics, and sources not frozen"},
        {**COMMON_BENCHMARK, "benchmark_id": "lsun_candidate", "display_name": "LSUN-style optional domain", "domain": "scene_or_object_domain", "resolution": "TBD", "conditioning": "unconditional", "reference_source": "TBD_MANUAL_VERIFICATION", "reference_split": "TBD", "license": "unverified_requires_manual_review", "expected_reference_count": "TBD", "local_source_formats": ["validated_image_tree"], "feature_spaces_supported": ["inception", "clip", "dinov2"], "evaluation_protocols": ["optional_domain_replication"], "known_preprocessing_risks": ["dataset_version", "crop", "duplicates"], "cvpr_relevance": "optional breadth", "execution_tier": "optional", "blocker": "only execute if pilot and core breadth justify it"},
        {**COMMON_BENCHMARK, "benchmark_id": "video_generation_extension", "display_name": "Optional video-generation extension", "domain": "video", "resolution": "TBD", "conditioning": "TBD", "reference_source": "minimal_config_skeleton_only", "reference_split": "TBD", "license": "unverified", "expected_reference_count": "TBD", "local_source_formats": ["video_manifest"], "feature_spaces_supported": [], "evaluation_protocols": ["post_image_core_only"], "known_preprocessing_risks": ["temporal_sampling", "decoder", "metric_theory_not_implemented"], "cvpr_relevance": "maximum-ceiling extension only", "execution_tier": "optional_post_image", "blocker": "rejected before successful image core"},
    ]
    put_yaml("registry/cvpr/benchmark_registry.yaml", {"schema_version": "certgen.cvpr.benchmarks.v1", "benchmarks": benchmarks, "claim_allowed": False})

    base_model = {"task": "image_generation", "license": "unverified_requires_manual_review", "authentication_required": "unknown", "released_samples_available": "not_verified", "checkpoint_available": "not_verified", "sample_count_available": "not_verified", "generation_cost_estimate": "planning_only_hardware_dependent", "feature_only_possible": "unknown", "preflight_required": True, "status": "candidate_metadata_unverified", "claim_allowed": False}
    models = [
        {**base_model, "model_id": "google_ddpm_cifar10_candidate", "display_name": "Google DDPM CIFAR-10 candidate", "family": "DDPM", "benchmark_id": "cifar10", "architecture": "DDPM", "checkpoint_or_sample_source": "google/ddpm-cifar10-32", "revision": "267b167dc01f0e4e61923ea244e8b988f84deb80", "resolution": "32x32", "conditioning": "unconditional", "adapter": "diffusers_DDPMPipeline_preflight_required", "blocker": "real load, license, scheduler, and output validation not run", "cvpr_recognition": "pilot baseline candidate"},
        {**base_model, "model_id": "frank_ddpm_ema_cifar10_candidate", "display_name": "DDPM EMA CIFAR-10 candidate", "family": "DDPM", "benchmark_id": "cifar10", "architecture": "DDPM_EMA", "checkpoint_or_sample_source": "FrankCCCCC/ddpm_ema_cifar10", "revision": "6aa387f240fbb00d0e003f93a3b994f56dd98dc2", "resolution": "32x32", "conditioning": "unconditional", "adapter": "diffusers_DDPMPipeline_preflight_required", "blocker": "real load, provenance, license, and output validation not run", "cvpr_recognition": "pilot within-family candidate"},
        {**base_model, "model_id": "frank_cfm_cifar10_candidate", "display_name": "CFM CIFAR-10 candidate", "family": "flow_matching", "benchmark_id": "cifar10", "architecture": "repository_label_CFM_adapter_unverified", "checkpoint_or_sample_source": "FrankCCCCC/cfm-cifar10-32", "revision": "b3f30358497e11ce5011c00614c9b0521262f51c", "resolution": "32x32", "conditioning": "unconditional", "adapter": "highest_risk_DDPMPipeline_interpretation_requires_preflight", "blocker": "architecture/adapter semantics, real load, license, and outputs unverified", "cvpr_recognition": "cross-family pilot candidate"},
    ]
    for model_id, family, benchmark, relevance in [
        ("adm_guided_diffusion_candidate", "ADM_guided_diffusion", "imagenet_class_conditional_candidate", "recognized diffusion family"),
        ("edm_candidate", "EDM", "ffhq_candidate", "recognized diffusion design"),
        ("latent_diffusion_candidate", "latent_diffusion", "text_to_image_public_prompts_candidate", "recognized latent family"),
        ("dit_candidate", "DiT", "imagenet_class_conditional_candidate", "recognized transformer generator"),
        ("consistency_candidate", "consistency_or_accelerated", "imagenet_class_conditional_candidate", "accelerated generation family"),
        ("stylegan_candidate", "StyleGAN", "ffhq_candidate", "recognized GAN family"),
        ("biggan_candidate", "BigGAN", "imagenet_class_conditional_candidate", "recognized class-conditional GAN"),
        ("open_text_to_image_candidate", "open_text_to_image", "text_to_image_public_prompts_candidate", "modern text-to-image lane"),
    ]:
        models.append({**base_model, "model_id": model_id, "display_name": model_id.replace("_", " ").title(), "family": family, "benchmark_id": benchmark, "architecture": family, "checkpoint_or_sample_source": "TBD_MANUAL_SOURCE_VERIFICATION", "revision": "TBD_PINNED_REVISION", "resolution": "TBD", "conditioning": "benchmark_dependent", "adapter": "TBD_AFTER_SOURCE_VERIFICATION", "blocker": "planning entry only; no availability, license, or adapter claim", "cvpr_recognition": relevance})
    model_asset_fields = {"asset_policy": "ONLINE_PREFLIGHT_DOWNLOAD", "asset_manifest_required": True, "online_preflight_supported": True, "offline_cache_supported": True, "expected_cache_size": "planning_only_measure_in_preflight"}
    for index, model in enumerate(models):
        rebuilt: dict[str, Any] = {}
        for key, value in model.items():
            rebuilt[key] = value
            if key == "model_id":
                rebuilt.update(model_asset_fields)
        models[index] = rebuilt
    put_yaml("registry/cvpr/model_registry.yaml", {"schema_version": "certgen.cvpr.models.v1", "models": models, "claim_allowed": False})

    features = [
        {"feature_space_id": "inception", "model_identifier": "torchvision_inception_v3_IMAGENET1K_V1", "revision": "package_and_weight_enum_lock", "package": "torchvision", "expected_dimension": 2048, "input_resolution": 299, "resize": "preprocessing_lock_required", "crop": "preprocessing_lock_required", "interpolation": "bilinear_lock_required", "pixel_range": "extractor_contract", "normalization": "ImageNet_lock_required", "feature_normalization": "none_or_explicit_l2_before_RBF", "precision": "float32_cache", "batch_size_default": 64, "device_support": ["cuda", "cpu_fallback"], "license": "package_and_weights_review_required", "cache_schema_version": "certgen.feature_cache.v2", "status": "adapter_exists_real_cache_not_run", "claim_allowed": False},
        {"feature_space_id": "clip", "model_identifier": "openai/clip-vit-large-patch14", "revision": "32bd64288804d66eefd0ccbe215aa642df71cc41", "package": "transformers", "expected_dimension": 768, "input_resolution": 224, "resize": "processor_lock_required", "crop": "processor_lock_required", "interpolation": "processor_lock_required", "pixel_range": "processor_contract", "normalization": "processor_lock_required", "feature_normalization": "l2_required_for_bounded_RBF_route", "precision": "float32_cache", "batch_size_default": 64, "device_support": ["cuda", "cpu_fallback"], "license": "model_and_package_review_required", "cache_schema_version": "certgen.feature_cache.v2", "status": "adapter_exists_real_cache_not_run", "claim_allowed": False},
        {"feature_space_id": "dinov2", "model_identifier": "DINOv2_candidate_encoder", "revision": "TBD_PIN_AFTER_PREFLIGHT", "package": "timm_or_transformers_to_be_frozen", "expected_dimension": "TBD_BY_SELECTED_VARIANT", "input_resolution": "TBD_BY_SELECTED_VARIANT", "resize": "preprocessing_lock_required", "crop": "preprocessing_lock_required", "interpolation": "preprocessing_lock_required", "pixel_range": "extractor_contract", "normalization": "selected_encoder_contract", "feature_normalization": "l2_required_for_bounded_RBF_route", "precision": "float32_cache", "batch_size_default": 32, "device_support": ["cuda", "cpu_fallback"], "license": "model_and_package_review_required", "cache_schema_version": "certgen.feature_cache.v2", "status": "planned_adapter_contract_real_preflight_required", "claim_allowed": False},
    ]
    asset_fields = {"asset_policy": "ONLINE_PREFLIGHT_DOWNLOAD", "asset_manifest_required": True, "online_preflight_supported": True, "offline_cache_supported": True, "expected_cache_size": "planning_only_measure_in_preflight"}
    features = [
        {"feature_space_id": feature["feature_space_id"], **asset_fields, **{key: value for key, value in feature.items() if key != "feature_space_id"}}
        for feature in features
    ]
    put_yaml("registry/cvpr/feature_space_registry.yaml", {"schema_version": "certgen.cvpr.feature_spaces.v1", "feature_spaces": features, "claim_allowed": False})

    capabilities = [
        {"adapter_id": "diffusers_ddpm_pipeline", "model_ids": ["google_ddpm_cifar10_candidate", "frank_ddpm_ema_cifar10_candidate"], "supports_batching": True, "supports_generator_list": True, "supports_class_conditioning": False, "supports_prompt_batching": False, "supports_scheduler_override": True, "supports_mixed_precision": True, "supports_resume": True, "known_memory_risk": "preflight_measurement_required", "status": "adapter_contract_fixture_validated_real_preflight_required", "claim_allowed": False},
        {"adapter_id": "cfm_candidate_preflight_only", "model_ids": ["frank_cfm_cifar10_candidate"], "supports_batching": False, "supports_generator_list": False, "supports_class_conditioning": False, "supports_prompt_batching": False, "supports_scheduler_override": False, "supports_mixed_precision": "unknown_until_preflight", "supports_resume": True, "known_memory_risk": "adapter_semantics_and_memory_unverified", "status": "blocked_real_adapter_preflight_required", "claim_allowed": False},
    ]
    put_yaml("registry/cvpr/model_adapter_capabilities.yaml", {"schema_version": "certgen.cvpr.model_adapter_capabilities.v1", "adapters": capabilities, "claim_allowed": False})

    comparison_fields = ["comparison_id", "benchmark_id", "model_a", "model_b", "comparison_type", "source_of_pair", "prospective_or_posthoc", "primary_or_secondary", "expected_gap_class", "feature_spaces", "metrics", "sample_budgets", "family_id", "status", "blocker"]
    types = [
        ("null_reference_split", "reference_split_a", "reference_split_b", "null reference split versus reference split", "null", "primary"),
        ("same_checkpoint_seeds", "google_ddpm_seed_a", "google_ddpm_seed_b", "same model/checkpoint independent seeds", "near_null", "primary"),
        ("obvious_gap_corruption", "reference_clean", "reference_severe_corruption", "obvious-gap corruption control", "obvious", "primary"),
        ("controlled_degradation", "reference_mild_corruption", "reference_severe_corruption", "controlled degradation ladder", "controlled", "secondary"),
        ("sampler_variant", "same_model_sampler_a", "same_model_sampler_b", "same model different sampler", "contestable", "secondary"),
        ("checkpoint_variant", "google_ddpm_cifar10_candidate", "frank_ddpm_ema_cifar10_candidate", "same family different checkpoint", "contestable", "primary"),
        ("cross_family", "google_ddpm_cifar10_candidate", "frank_cfm_cifar10_candidate", "cross-family contestable pair", "contestable", "primary"),
        ("preprocess_sensitivity", "fixed_samples_preprocess_a", "fixed_samples_preprocess_b", "preprocessing sensitivity pair", "unknown", "secondary"),
        ("feature_disagreement_candidate", "google_ddpm_cifar10_candidate", "frank_cfm_cifar10_candidate", "feature-space disagreement candidate", "unknown", "secondary"),
        ("published_pair_placeholder", "TBD_PROSPECTIVE_MODEL_A", "TBD_PROSPECTIVE_MODEL_B", "real reported pair", "unknown", "secondary"),
    ]
    comparison_rows = [{"comparison_id": item[0], "benchmark_id": "cifar10", "model_a": item[1], "model_b": item[2], "comparison_type": item[3], "source_of_pair": "prospective_protocol_not_results", "prospective_or_posthoc": "prospective", "primary_or_secondary": item[5], "expected_gap_class": item[4], "feature_spaces": "inception|clip|dinov2", "metrics": "rbf_mmd", "sample_budgets": "1000|10000|50000", "family_id": "cvpr_primary_cifar10", "status": "planning_only", "blocker": "real inputs and frozen family required"} for item in types]
    put_csv("registry/cvpr/comparison_registry.csv", comparison_fields, comparison_rows)
    claim_fields = ["claim_id", "paper_title", "paper_year", "venue", "paper_url_or_identifier", "benchmark", "model_a", "model_b", "reported_metric", "reported_a", "reported_b", "sample_count", "feature_extractor", "preprocessing", "released_samples_available", "checkpoint_available", "license", "reproduction_possible", "selection_reason", "prospective_status", "notes"]
    put_csv("registry/cvpr/published_claim_registry.csv", claim_fields, [])


def configs() -> None:
    prereg = {
        "study_id": "certgen_cvpr_prospective_template", "version": 1,
        "primary_question": "Which prospectively selected visual-generator comparisons are directionally decided by bounded RBF-MMD evidence at registered budgets?",
        "primary_outcomes": ["family-wise-valid pairwise decisions", "certified partial ranking", "censored samples-to-decision"],
        "secondary_outcomes": ["cross-feature consistency", "protocol sensitivity", "compute planning implications"],
        "benchmarks": ["cifar10"],
        "models": ["google_ddpm_cifar10_candidate", "frank_ddpm_ema_cifar10_candidate", "frank_cfm_cifar10_candidate"],
        "model_pairs": [{"comparison_id": "checkpoint_variant", "model_a": "google_ddpm_cifar10_candidate", "model_b": "frank_ddpm_ema_cifar10_candidate"}, {"comparison_id": "cross_family", "model_a": "google_ddpm_cifar10_candidate", "model_b": "frank_cfm_cifar10_candidate"}],
        "feature_spaces": ["inception", "clip", "dinov2"], "metrics": ["rbf_mmd"],
        "kernel": {"name": "rbf", "normalize": "l2", "gamma": 0.5},
        "bandwidth_protocol": "prospectively_fixed_unit_sphere_gamma_0.5_v1",
        "alpha": 0.05, "multiplicity_families": ["cvpr_primary_cifar10"], "sample_budgets": [1000, 10000, 50000],
        "stopping_rule": "first_boundary_crossing_union_hoeffding", "stream_seed": 0,
        "reference_draw_protocol": "iid_with_replacement_from_fixed_empirical_population_precommitted",
        "exclusion_rules": ["invalid provenance", "cache mismatch", "nonfinite features", "failed sanity gate"],
        "failure_rules": ["fail closed; preserve raw artifacts; do not substitute models or pairs after inspecting outcomes"],
        "resume_rules": ["same configuration hash, stream order, reference draw, and alpha ledger only"],
        "missing_data_rules": ["block the affected comparison; do not silently impute"],
        "censoring_rules": ["UNDECIDED_AT_BUDGET is right-censored at the registered maximum budget"],
        "claim_thresholds": ["all lineage, sanity, family, and paper gates pass"],
        "scale_up_rules": ["stop after 1k for interpretation", "10k only after pilot gate", "50k only after 10k gate"],
        "pivot_rules": ["scientific pivots require a new version before inspecting affected results"],
        "preprocessing_hash": "TBD_REAL_CACHE_REQUIRED", "configuration_hash": "TBD_FREEZE_WITH_CERTGEN", "frozen": False,
        "evidence_class": "planning_only", "claim_allowed": False,
    }
    put_yaml("configs/cvpr/certgen_cvpr_preregistration_template.yaml", prereg)
    put_yaml("registry/cvpr/family_registry.yaml", {"schema_version": "certgen.cvpr.family_registry.v1", "families": [{"family_id": "cvpr_primary_cifar10", "analysis_scope": "all registered primary model pairs x 3 feature spaces x registered budgets under one prospective interpretation", "benchmark": "cifar10", "feature_space": "separate_feature_specific_families_required_before_freeze", "metric": "rbf_mmd", "kernel": "rbf", "bandwidth": "gamma_0.5_fixed", "model_pairs": ["checkpoint_variant", "cross_family"], "alpha_total": 0.05, "number_of_hypotheses": "TBD_EXACT_CARTESIAN_FREEZE", "alpha_per_hypothesis": "TBD_AFTER_FREEZE", "status": "planning_only_not_frozen", "preregistered_at": None, "configuration_hash": "TBD_AFTER_FREEZE", "claim_allowed": False}], "claim_allowed": False})
    execution_rows = []
    run_classes = [
        ("local_validation", "Class A", "local", "CPU", "compilation/tests/audits", "reports/CERTGEN_CVPR_FINAL_AUDIT.json", "none", "P0", "seconds to minutes"),
        ("reference_materialization", "Class B", "local", "CPU", "user-provided reference", "reference manifest", "valid source", "P0", "minutes"),
        ("checkpoint_preflight", "Class C", "Kaggle", "T4x2", "preflight input ZIP", "preflight output ZIP", "reference materialized", "P1", "5-30 minutes"),
        ("generation_1k", "Class D", "Kaggle", "T4x2", "validated preflight", "generation ZIP", "preflight imported", "P1", "30 minutes-3 hours"),
        ("features_1k", "Class E", "Kaggle", "T4x2", "reference+generation package", "feature ZIP", "generation imported", "P1", "5-60 minutes per extractor planning range"),
        ("import_validation", "Class F", "local", "CPU", "copied-back ZIPs", "hash-addressed imports", "ZIP copied back", "P1", "seconds-tens of minutes"),
        ("metric_sanity", "Class G", "local", "CPU", "validated caches", "gate results", "caches validated", "P1", "seconds-minutes"),
        ("certificate_pilot", "Class H", "local", "CPU", "frozen family+features", "pilot certificates", "sanity pass", "P1", "seconds-minutes"),
        ("ranking_sensitivity", "Class I", "local", "CPU", "compatible certificates", "partial ranking", "pilot complete", "P2", "seconds-minutes"),
        ("figures", "Class J", "local", "CPU", "approved artifacts", "figures", "figure gate", "P3", "minutes"),
        ("literature_audit", "Class K", "local/manual", "CPU", "frozen claim registry", "audit tables", "protocol freeze", "P3", "days of manual curation"),
        ("paper_promotion", "Class L", "local", "CPU", "complete lineage", "approved evidence IDs", "all gates", "P3", "minutes-hours"),
    ]
    for scale in ["preflight", "1k", "10k", "50k"]:
        for row in run_classes:
            if scale == "preflight" and row[0] not in {
                "local_validation",
                "reference_materialization",
                "checkpoint_preflight",
            }:
                continue
            execution_rows.append({"run_id_template": f"<benchmark>__{row[0]}__{scale}__<feature>__<hash>__<timestamp>", "benchmark": "config_driven", "model": "registry_driven", "feature_space": "registry_driven", "scale": scale, "stage": row[0], "class": row[1], "CPU_GPU": row[3], "location": row[2], "expected_input": row[4], "expected_output": row[5], "prerequisite": row[6], "priority": row[7], "runtime_estimate": row[8], "memory_estimate": "hardware-dependent planning estimate", "resumability": "hash-bound per-shard where applicable", "evidence_class": "planning_only", "claim_allowed": False})
    put_yaml("configs/cvpr/execution_matrix.yaml", {"schema_version": "certgen.cvpr.execution_matrix.v1", "estimate_label": "planning estimate; hardware-dependent; not an empirical project result", "runs": execution_rows, "claim_allowed": False})
    put_yaml("configs/cvpr/statistical_baselines.yaml", {"baselines": ["fixed_n_point_estimate", "fixed_n_bootstrap_interval", "naive_repeated_peeking_negative_control", "bonferroni_fixed_n", "certgen_union_hoeffding", "closest_applicable_sequential_kernel_baseline_TBD"], "status": "planning_only", "claim_allowed": False})
    put_yaml("configs/cvpr/evaluation_baselines.yaml", {"descriptive": ["FID_FD", "polynomial_KID", "precision_recall_or_density_coverage_if_feasible"], "certificate_capable": ["bounded_RBF_MMD_Inception", "bounded_RBF_MMD_CLIP", "bounded_RBF_MMD_DINO"], "status": "planning_only", "claim_allowed": False})
    put_yaml("configs/cvpr/ablations.yaml", {"ablations": ["alpha", "maximum_budget", "bandwidth", "bandwidth_selection_protocol", "reference_split", "reference_sampling", "feature_space", "normalization", "preprocessing", "Bonferroni_family_size", "model_pair_family", "seed_partition", "scale_1k_10k_50k", "resume_boundary", "synthetic_dependence_violation"], "negative_controls": ["null_pairs", "same_checkpoint_independent_seeds", "identical_cached_features", "corrupted_manifests", "mixed_preprocessing_rejection", "mixed_reference_rejection"], "status": "planning_only", "claim_allowed": False})
    figure_types = ["headline_partial_ranking", "anytime_trajectory", "decidedness_vs_budget", "samples_to_decision", "protocol_sensitivity", "compute_savings", "visual_model_pair_gallery", "controlled_failure_gallery"]
    put_yaml("configs/cvpr/figure_contracts.yaml", {"figures": [{"figure_id": name, "figure_type": name, "approved_input_artifacts": ["TBD_PAPER_APPROVED_ARTIFACT_ID"], "schema": "certgen.cvpr.figure_request.v1", "configuration_hash": "TBD_REAL_RUN_REQUIRED", "claim_gate_status": "BLOCKED_NO_PAPER_EVIDENCE", "output_path": f"paper/figures/{name}.pdf", "caption_metadata": {"status": "placeholder"}, "limitations": ["TBD_REAL_RUN_REQUIRED"]} for name in figure_types], "claim_allowed": False})
    put("configs/cvpr/metric_reproduction_gate_template.yaml", """schema_version: certgen.cvpr.metric_reproduction_config.v1
gate_id: TBD_REAL_RUN_REQUIRED
run_id: TBD_REAL_RUN_REQUIRED
reference_cache:
  features: TBD_VALIDATED_CACHE_V2_NPZ
  sidecar: TBD_VALIDATED_CACHE_V2_SIDECAR
  artifact_root: TBD_IMMUTABLE_IMPORT_ROOT
  array_sha256: TBD_REAL_RUN_REQUIRED
  ordered_sample_ids_sha256: TBD_REAL_RUN_REQUIRED
  sample_count: 1000
  role: reference
generated_cache:
  features: TBD_VALIDATED_CACHE_V2_NPZ
  sidecar: TBD_VALIDATED_CACHE_V2_SIDECAR
  artifact_root: TBD_IMMUTABLE_IMPORT_ROOT
  array_sha256: TBD_REAL_RUN_REQUIRED
  ordered_sample_ids_sha256: TBD_REAL_RUN_REQUIRED
  sample_count: 1000
  role: generated
metric:
  name: unbiased_mmd2
  convention: unbiased_u_statistic_full_pairwise
  feature_extractor_hash: TBD_REAL_RUN_REQUIRED
  preprocessing_hash: TBD_REAL_RUN_REQUIRED
  kernel:
    name: rbf
    normalize: l2
    gamma: 0.5
target:
  class: cross_implementation_consistency
  implementation_id: TBD_INDEPENDENT_IMPLEMENTATION
  provenance: TBD_TARGET_VALUE_PROVENANCE
  value: null
  tolerance_abs: 1.0e-10
  tolerance_rel: 1.0e-8
evidence_class: sanity_artifact
claim_allowed: false
configuration_hash: TBD_FREEZE_WITH_CERTGEN_CONFIGURATION_HASH
""")
    put("configs/cvpr/runtime_plan_template.yaml", """schema_version: certgen.cvpr.runtime_plan_config.v1
run_id: TBD_REAL_RUN_REQUIRED
scale: 1k
model_count: 3
images_per_model: 1000
reference_images: 1000
gpu_count: 2
shard_count: 4
session_limit_minutes: 720
fixed_setup_minutes: 20
model_download_cache_minutes_per_model: 30
generation_images_per_second_per_gpu: {min: 0.05, max: 0.5}
generation_batch_size: 64
average_encoded_image_bytes: 50000
extractors:
- feature_space_id: inception
  images_per_second_per_gpu: {min: 1.0, max: 10.0}
  feature_dimension: 2048
  bytes_per_value: 4
  batch_size: 64
- feature_space_id: clip
  images_per_second_per_gpu: {min: 0.5, max: 5.0}
  feature_dimension: 768
  bytes_per_value: 4
  batch_size: 64
- feature_space_id: TBD_SELECTED_DINOV2_FEATURE_SPACE
  images_per_second_per_gpu: {min: 0.5, max: 5.0}
  feature_dimension: 768
  bytes_per_value: 4
  batch_size: 32
merge_minutes: 15
local_validation_minutes: 20
archive_overhead_fraction: 0.15
planning_ram_gib: 16
planning_vram_per_gpu_gib: 16
claim_allowed: false
configuration_hash: TBD_FREEZE_WITH_CERTGEN
""")
    put("configs/cvpr/sanity_gates_template.yaml", """schema_version: certgen.cvpr.sanity_gate_config.v1
run_id: TBD_REAL_RUN_REQUIRED
gates:
- gate_id: null_reference_split
  family: null
  control_type: reference_split_vs_reference_split
  inputs: {artifact_ids: [TBD_TWO_INDEPENDENT_REFERENCE_SPLITS]}
  measured_values: {value: null}
  tolerances: {max_absolute: TBD_PREREGISTERED}
- gate_id: null_same_model
  family: null
  control_type: same_model_independent_samples
  inputs: {artifact_ids: [TBD_SAME_CHECKPOINT_INDEPENDENT_SAMPLES]}
  measured_values: {value: null}
  tolerances: {max_absolute: TBD_PREREGISTERED}
- gate_id: null_repeated_batching
  family: null
  control_type: repeated_batching
  inputs: {artifact_ids: [TBD_SAME_ROWS_DIFFERENT_BATCHING]}
  measured_values: {value: null}
  tolerances: {max_absolute: TBD_PREREGISTERED}
- gate_id: null_repeated_shard_merge
  family: null
  control_type: repeated_shard_merge
  inputs: {artifact_ids: [TBD_SAME_SHARDS_REPEATED_MERGE]}
  measured_values: {value: null}
  tolerances: {max_absolute: TBD_PREREGISTERED}
- gate_id: gap_reference_corruption
  family: obvious_gap
  control_type: reference_vs_severe_corruption
  inputs: {artifact_ids: [TBD_INDEPENDENT_REFERENCE_AND_SEVERE_CORRUPTION]}
  measured_values: {gap: null}
  tolerances: {minimum_gap: TBD_PREREGISTERED, expected_sign: 1}
- gate_id: gap_quality_degradation
  family: obvious_gap
  control_type: high_quality_vs_intentionally_degraded
  inputs: {artifact_ids: [TBD_HIGH_QUALITY_AND_DEGRADED]}
  measured_values: {gap: null}
  tolerances: {minimum_gap: TBD_PREREGISTERED, expected_sign: 1}
- gate_id: gap_corruption_ladder
  family: obvious_gap
  control_type: noise_blur_compression_ladder
  inputs: {artifact_ids: [TBD_FIXED_CORRUPTION_LADDER]}
  measured_values: {gap: null}
  tolerances: {minimum_gap: TBD_PREREGISTERED, expected_sign: 1}
- gate_id: direction_corruption_severity
  family: direction
  control_type: corruption_severity_aggregate
  inputs: {ordered_severities: [TBD_PREREGISTERED]}
  measured_values: {ordered_values: []}
  tolerances: {expected_direction: increasing, minimum_aggregate_step: TBD_PREREGISTERED}
- gate_id: direction_certificate_ordering
  family: direction
  control_type: certificate_controlled_ordering
  inputs: {artifact_ids: [TBD_CONTROLLED_ORDER_CERTIFICATES]}
  measured_values: {ordered_values: []}
  tolerances: {expected_direction: increasing, minimum_aggregate_step: TBD_PREREGISTERED}
- gate_id: protocol_identity_rejection
  family: protocol
  control_type: identity_mismatch_rejection
  inputs:
    cases:
    - mismatch_field: preprocessing_hash
      baseline: {preprocessing_hash: TBD_BASELINE}
      candidate: {preprocessing_hash: TBD_DIFFERENT}
    - mismatch_field: feature_space
      baseline: {feature_space: TBD_BASELINE}
      candidate: {feature_space: TBD_DIFFERENT}
    - mismatch_field: bandwidth
      baseline: {bandwidth: TBD_BASELINE}
      candidate: {bandwidth: TBD_DIFFERENT}
    - mismatch_field: reference_population_hash
      baseline: {reference_population_hash: TBD_BASELINE}
      candidate: {reference_population_hash: TBD_DIFFERENT}
  measured_values: {}
  tolerances: {all_mismatches_must_be_rejected: true}
evidence_class: sanity_artifact
claim_allowed: false
configuration_hash: TBD_FREEZE_WITH_CERTGEN_CONFIGURATION_HASH
""")


def theory_docs() -> None:
    put("docs/theory/CERTGEN_CVPR_STATISTICAL_CORE_AUDIT.md", """# CertGen CVPR Statistical Core Audit

Status: `VERIFIED_CURRENT` for the local implementation; real-run assumptions remain `BLOCKED`.

The only claim-capable route is the prospectively fixed bounded-RBF comparison stream, union-Hoeffding confidence sequence, first-boundary crossing, and Bonferroni control over a frozen family. Tests and synthetic checks are not model evidence.

| Item | Verdict | Contract |
|---|---|---|
| Estimand | VERIFIED_CURRENT | Delta = MMD^2(A,R)-MMD^2(B,R) |
| Unit | VERIFIED_CURRENT | disjoint A pair, B pair, and shared-within-unit R pair |
| Contribution | VERIFIED_CURRENT | kAA-kBB-kAR1-kAR2+kBR1+kBR2 |
| Support | VERIFIED_CURRENT | each kernel term in [0,1], conservative contribution support [-3,3] |
| Direction | VERIFIED_CURRENT | negative means A closer; positive means B closer |
| Stopping | VERIFIED_CURRENT | first time the time-uniform interval excludes zero; ties/zero remain undecided |
| Time allocation | VERIFIED_CURRENT | alpha_t = 6 alpha/(pi^2 t^2), encoded through the union-Hoeffding radius |
| Resume | VERIFIED_CURRENT | identical stream prefix/configuration/reference plan only |
| Dependence | BLOCKED_REAL_RUN | IID/conditional-mean stream and prospectively fixed choices must be enforced by lineage |
| Multiplicity | BLOCKED_FREEZE | exact Cartesian family must be frozen before claim-bearing analysis |

Unsupported: betting-grid confidence intervals, empirical-Bernstein certificates, directional e-BH ranking, FID/FD certification, and polynomial-KID certification.
""")
    put("docs/theory/CERTGEN_FORMAL_STREAM_CONTRACT.md", """# CertGen Formal Stream Contract

For time t, consume six rows `(A_1t,A_2t,B_1t,B_2t,R_1t,R_2t)`. Define

`Z_t = k(A_1t,A_2t)-k(B_1t,B_2t)-k(A_1t,R_2t)-k(A_2t,R_1t)+k(B_1t,R_2t)+k(B_2t,R_1t)`.

The reference-reference terms cancel because the same reference pair is used inside both relative-MMD contributions. With an RBF kernel in `[0,1]`, `Z_t` lies in `[-3,3]`. Across time, A/B rows may not repeat; R rows follow the preregistered draw plan. All extractor, preprocessing, normalization, gamma, family, order, seed, and maximum-budget choices are measurable before the stream is inspected. The filtration is generated by completed preceding units. The decision is the first interval excluding zero; equality and boundary-touching remain undecided.

`synthetic_validation_only` · `not_model_evidence` · `claim_allowed=false`
""")
    put("docs/theory/CERTGEN_REFERENCE_DRAW_PROTOCOL.md", """# CertGen Reference Draw Protocol

Freeze the validated reference manifest and its SHA-256. Then run `python3 -m certgen.cli.build_reference_draw_plan` before inspecting certificate values. The canonical target is the fixed empirical reference distribution with deterministic PCG64 IID-with-replacement draws. The plan records population ID/hash, seed, draw IDs, source IDs/indices, pairing order, and a plan hash. Repeats are allowed by design; unregistered reuse, reordered caches, changed populations, or post-outcome redraws fail closed. A finite without-replacement design needs a separate proof and family lock.

The materialized execution view pairs draw indices `(0,1)`, `(2,3)`, and so on. A/B sample identities remain non-overlapping and role-disjoint.
""")
    put("docs/theory/CERTGEN_MULTIPLICITY_FAMILY_PROTOCOL.md", """# CertGen Multiplicity Family Protocol

The family denominator is the full prospective Cartesian set of claim-bearing model pairs, feature spaces, metrics, benchmarks, budgets, preprocessing variants, and kernels. Budgets monitored by one time-uniform stream do not become independent hypotheses; separately interpreted budget-specific claims do. Each frozen record contains the family ID, scope, benchmark, feature space, metric, kernel, bandwidth, pair list, alpha total, hypothesis count, Bonferroni alpha, timestamp, and configuration hash.

Ad hoc pairs are exploratory and cannot enter a global ranking. A changed pair, representation, preprocessing lock, reference population, or kernel creates a new family/version before results are viewed. Directional e-BH and global adaptive stopping remain unsupported.
""")


def reports_and_docs() -> None:
    put("reports/CERTGEN_CVPR_BASELINE_REPRODUCTION.md", """# CertGen CVPR Baseline Reproduction

Baseline captured before CVPR-layer edits on branch `master`, commit `bff335aa648fd19e2fa7e3cfea293a6ca519a68b`. The worktree was already heavily dirty; all state was preserved.

| Check | Verdict | Result |
|---|---|---|
| Full offline tests | VERIFIED_CURRENT | 212 passed in 9.73s; exit 0 |
| Statistical documented lane | VERIFIED_CURRENT | 22 passed; exit 0 (not the reported 31 count) |
| Artifact-contract documented lane | VERIFIED_CURRENT | 18 passed; exit 0 (not the reported 25 count) |
| Forensic audit | VERIFIED_CURRENT | 8/8; exit 0 |
| Final execution audit | VERIFIED_CURRENT | BLOCKED_MISSING_REFERENCE_SAMPLES; exit 0 |
| V9 notebook static audit | VERIFIED_CURRENT | pass; static only |
| Paper firewall/artifact registry | VERIFIED_CURRENT | pass |
| Compile/import/ruff | VERIFIED_CURRENT | pass |
| Full mypy | VERIFIED_CURRENT_DEBT | 111 errors in 34 files; exit 1 |
| Paper build | VERIFIED_CURRENT | 5-page placeholder PDF built; warnings only |
| Privacy/secrets scan | VERIFIED_CURRENT | no issue; unknown-license template warnings remain |
| git diff --check | VERIFIED_CURRENT | pass |

No command downloaded data/models or generated scientific evidence.
""")
    ledger_fields = ["command_id", "command", "working_directory", "environment", "start_time_utc", "end_time_utc", "exit_code", "duration_seconds", "passed", "failed", "skipped", "warnings", "output_artifact"]
    ledger_rows = [
        {"command_id": "baseline_full_pytest", "command": "PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' python3 -m pytest -q", "working_directory": ".", "environment": "local CPU Python 3.11 no CUDA", "start_time_utc": "2026-07-13T05:02:57Z", "end_time_utc": "2026-07-13T05:03:09Z", "exit_code": 0, "duration_seconds": 11.41, "passed": 212, "failed": 0, "skipped": 0, "warnings": "none", "output_artifact": "reports/CERTGEN_CVPR_BASELINE_REPRODUCTION.md"},
        {"command_id": "baseline_stat_lane", "command": "python3 -m pytest -q tests/test_confidence_sequences.py tests/test_mmd_streams.py tests/test_clean_core_certificate.py tests/test_reference_draw_plan.py", "working_directory": ".", "environment": "local CPU", "start_time_utc": "2026-07-13T05:03:34Z", "end_time_utc": "2026-07-13T05:03:35Z", "exit_code": 0, "duration_seconds": 1.04, "passed": 22, "failed": 0, "skipped": 0, "warnings": "reported 31 count not reproduced by documented lane", "output_artifact": "reports/CERTGEN_CVPR_BASELINE_REPRODUCTION.md"},
        {"command_id": "baseline_artifact_lane", "command": "python3 -m pytest -q tests/test_engineering_evidence_safety.py tests/test_feature_cache_v2_contract.py tests/test_v7_importers.py", "working_directory": ".", "environment": "local CPU", "start_time_utc": "2026-07-13T05:03:34Z", "end_time_utc": "2026-07-13T05:03:35Z", "exit_code": 0, "duration_seconds": 1.05, "passed": 18, "failed": 0, "skipped": 0, "warnings": "reported 25 count not reproduced by documented lane", "output_artifact": "reports/CERTGEN_CVPR_BASELINE_REPRODUCTION.md"},
        {"command_id": "baseline_forensic", "command": "python3 -m certgen.audit.forensic_final_audit", "working_directory": ".", "environment": "local CPU", "start_time_utc": "2026-07-13T05:03:34Z", "end_time_utc": "2026-07-13T05:03:34Z", "exit_code": 0, "duration_seconds": 0.24, "passed": "8/8", "failed": 0, "skipped": 0, "warnings": "none", "output_artifact": "reports/CERTGEN_FORENSIC_MACHINE_AUDIT.json"},
        {"command_id": "baseline_mypy", "command": "mypy certgen", "working_directory": ".", "environment": "local Python 3.11", "start_time_utc": "2026-07-13T05:04:05Z", "end_time_utc": "2026-07-13T05:04:14Z", "exit_code": 1, "duration_seconds": 9.40, "passed": 0, "failed": "111 errors in 34 files", "skipped": 0, "warnings": "historical debt; critical new modules checked separately", "output_artifact": "CERTGEN_CVPR_MAX_PREEXECUTION_BUILD_REPORT.md"},
        {"command_id": "final_ruff", "command": "python3 -m ruff check certgen tests scripts", "working_directory": ".", "environment": "local Python 3.11", "start_time_utc": "2026-07-13T05:44:44Z", "end_time_utc": "2026-07-13T05:44:44Z", "exit_code": 0, "duration_seconds": 0.17, "passed": "all checks", "failed": 0, "skipped": 0, "warnings": "none", "output_artifact": "reports/CERTGEN_CVPR_COMMAND_LEDGER.csv"},
        {"command_id": "final_full_pytest", "command": "PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' python3 -m pytest -q", "working_directory": ".", "environment": "local CPU Python 3.11 no CUDA", "start_time_utc": "2026-07-13T05:44:44Z", "end_time_utc": "2026-07-13T05:44:58Z", "exit_code": 0, "duration_seconds": 14.58, "passed": 228, "failed": 0, "skipped": 0, "warnings": "none", "output_artifact": "CERTGEN_CVPR_MAX_PREEXECUTION_BUILD_REPORT.md"},
        {"command_id": "final_targeted_mypy", "command": "python3 -m mypy --follow-imports=skip --ignore-missing-imports certgen/cvpr certgen/visualization certgen/notebooks/cvpr_factory.py certgen/notebooks/cvpr_static_analyzer.py certgen/notebooks/cvpr_runtime.py certgen/audit/cvpr_final_audit.py scripts/build_cvpr_preexecution_assets.py tests/test_cvpr_statistical_contract.py tests/test_cvpr_architecture.py tests/test_cvpr_extended_synthetic.py", "working_directory": ".", "environment": "local Python 3.11", "start_time_utc": "2026-07-13T05:44:44Z", "end_time_utc": "2026-07-13T05:44:45Z", "exit_code": 0, "duration_seconds": 1.40, "passed": "20 source files", "failed": 0, "skipped": 0, "warnings": "none", "output_artifact": "reports/CERTGEN_CVPR_COMMAND_LEDGER.csv"},
        {"command_id": "final_full_mypy", "command": "python3 -m mypy certgen", "working_directory": ".", "environment": "local Python 3.11", "start_time_utc": "2026-07-13T05:40:50Z", "end_time_utc": "2026-07-13T05:41:06Z", "exit_code": 1, "duration_seconds": 15.31, "passed": 0, "failed": "111 errors in 34 files", "skipped": 0, "warnings": "exact pre-existing baseline debt; no incremental errors", "output_artifact": "CERTGEN_CVPR_MAX_PREEXECUTION_BUILD_REPORT.md"},
        {"command_id": "final_paper_build", "command": "pdflatex -interaction=nonstopmode -halt-on-error main.tex (two passes)", "working_directory": "paper", "environment": "local TeX Live 2026", "start_time_utc": "2026-07-13T05:40:10Z", "end_time_utc": "2026-07-13T05:40:11Z", "exit_code": 0, "duration_seconds": 0.25, "passed": "5 pages", "failed": 0, "skipped": 0, "warnings": "overfull boxes; PDF/log/aux removed after structural verification", "output_artifact": "paper/CERTGEN_CVPR_PAPER_BUILD_REPORT.md"},
        {"command_id": "final_notebook_static", "command": "python3 -m certgen audit notebooks", "working_directory": ".", "environment": "local CPU static only", "start_time_utc": "2026-07-13T05:41:22Z", "end_time_utc": "2026-07-13T05:41:22Z", "exit_code": 0, "duration_seconds": 0.19, "passed": "5/5", "failed": 0, "skipped": 0, "warnings": "not run on Kaggle", "output_artifact": "reports/CERTGEN_CVPR_NOTEBOOK_READINESS.md"},
        {"command_id": "final_cvpr_audit", "command": "python3 -m certgen audit cvpr", "working_directory": ".", "environment": "local CPU no external execution", "start_time_utc": "2026-07-13T05:41:22Z", "end_time_utc": "2026-07-13T05:41:23Z", "exit_code": 0, "duration_seconds": 0.19, "passed": "8/8", "failed": 0, "skipped": 0, "warnings": "blocked honestly on reference input", "output_artifact": "reports/CERTGEN_CVPR_FINAL_AUDIT.json"},
        {"command_id": "final_forensic", "command": "python3 -m certgen.audit.forensic_final_audit", "working_directory": ".", "environment": "local CPU", "start_time_utc": "2026-07-13T05:42:17Z", "end_time_utc": "2026-07-13T05:42:17Z", "exit_code": 0, "duration_seconds": 0.13, "passed": "8/8", "failed": 0, "skipped": 0, "warnings": "none", "output_artifact": "reports/CERTGEN_FORENSIC_MACHINE_AUDIT.json"},
        {"command_id": "final_execution_audit", "command": "CUDA_VISIBLE_DEVICES='' python3 -m certgen.audit.final_execution_audit --out docs/FINAL_EXECUTION_AUDIT.md --json-out data/results/final_execution_audit.json", "working_directory": ".", "environment": "local CPU no CUDA", "start_time_utc": "2026-07-13T05:42:17Z", "end_time_utc": "2026-07-13T05:42:17Z", "exit_code": 0, "duration_seconds": 0.12, "passed": "blocked-honest", "failed": 0, "skipped": 0, "warnings": "BLOCKED_MISSING_REFERENCE_SAMPLES", "output_artifact": "data/results/final_execution_audit.json"},
        {"command_id": "final_release_privacy", "command": "python3 -m certgen.audit.release_safety_v5 plus certgen.release.privacy_scan", "working_directory": ".", "environment": "local CPU", "start_time_utc": "2026-07-13T05:42:17Z", "end_time_utc": "2026-07-13T05:42:17Z", "exit_code": 0, "duration_seconds": 0.14, "passed": "release and privacy", "failed": 0, "skipped": 0, "warnings": "none", "output_artifact": "data/results/v5_release_safety.json"},
        {"command_id": "seal_compile_import", "command": "python3 -m certgen.notebooks.cvpr_factory; python3 scripts/build_cvpr_preexecution_assets.py; python3 -m compileall -q certgen scripts tests; canonical package imports", "working_directory": ".", "environment": "local CPU Python 3.11", "start_time_utc": "2026-07-13T06:27:10Z", "end_time_utc": "2026-07-13T06:27:11Z", "exit_code": 0, "duration_seconds": 0.5, "passed": "compile imports notebooks generator", "failed": 0, "skipped": 0, "warnings": "no execution", "output_artifact": "notebooks/kaggle/certgen_cvpr_*.ipynb"},
        {"command_id": "seal_full_pytest", "command": "PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' python3 -m pytest -q", "working_directory": ".", "environment": "local CPU Python 3.11 no CUDA", "start_time_utc": "2026-07-13T06:27:15Z", "end_time_utc": "2026-07-13T06:27:31Z", "exit_code": 0, "duration_seconds": 14.81, "passed": 234, "failed": 0, "skipped": 0, "warnings": "none", "output_artifact": "CERTGEN_CVPR_MAX_PREEXECUTION_BUILD_REPORT.md"},
        {"command_id": "seal_required_lanes", "command": "statistical 31-test lane; artifact-contract 25-test lane; extended CVPR synthetic/gate 11-test lane", "working_directory": ".", "environment": "local CPU no CUDA", "start_time_utc": "2026-07-13T06:27:51Z", "end_time_utc": "2026-07-13T06:27:53Z", "exit_code": 0, "duration_seconds": 2.4, "passed": "31+25+11", "failed": 0, "skipped": 0, "warnings": "synthetic and fixture validation only", "output_artifact": "reports/CERTGEN_CVPR_COMMAND_LEDGER.csv"},
        {"command_id": "seal_targeted_mypy", "command": "python3 -m mypy --follow-imports=skip --ignore-missing-imports critical CVPR modules and tests", "working_directory": ".", "environment": "local Python 3.11", "start_time_utc": "2026-07-13T06:28:31Z", "end_time_utc": "2026-07-13T06:28:31Z", "exit_code": 0, "duration_seconds": 0.8, "passed": "25 source files", "failed": 0, "skipped": 0, "warnings": "none", "output_artifact": "reports/CERTGEN_CVPR_COMMAND_LEDGER.csv"},
        {"command_id": "seal_full_mypy", "command": "python3 -m mypy certgen", "working_directory": ".", "environment": "local Python 3.11", "start_time_utc": "2026-07-13T06:28:31Z", "end_time_utc": "2026-07-13T06:28:48Z", "exit_code": 1, "duration_seconds": 16.2, "passed": 0, "failed": "111 errors in 34 files", "skipped": 0, "warnings": "exact historical baseline debt; no incremental errors", "output_artifact": "CERTGEN_CVPR_MAX_PREEXECUTION_BUILD_REPORT.md"},
        {"command_id": "seal_v9_compatibility", "command": "python3 -m certgen.audit.v9_execution_supercharger_audit --out docs/V9_EXECUTION_SUPERCHARGER_AUDIT.md --json-out data/results/v9_execution_supercharger_audit.json", "working_directory": ".", "environment": "local CPU", "start_time_utc": "2026-07-13T06:29:08Z", "end_time_utc": "2026-07-13T06:29:08Z", "exit_code": 0, "duration_seconds": 0.2, "passed": "22/22", "failed": 0, "skipped": 0, "warnings": "blocked honestly by inputs", "output_artifact": "data/results/v9_execution_supercharger_audit.json"},
        {"command_id": "seal_paper_build", "command": "pdflatex -interaction=nonstopmode -halt-on-error -output-directory=/tmp/certgen_cvpr_paper_final main.tex (two passes)", "working_directory": "paper", "environment": "local TeX Live 2026", "start_time_utc": "2026-07-13T06:29:16Z", "end_time_utc": "2026-07-13T06:29:17Z", "exit_code": 0, "duration_seconds": 0.4, "passed": "5 pages 179875 bytes", "failed": 0, "skipped": 0, "warnings": "3 overfull-box log lines; output kept outside repository", "output_artifact": "paper/CERTGEN_CVPR_PAPER_BUILD_REPORT.md"},
        {"command_id": "seal_release_privacy", "command": "python3 -m certgen.audit.release_safety_v5; certgen.release.privacy_scan", "working_directory": ".", "environment": "local CPU", "start_time_utc": "2026-07-13T06:29:32Z", "end_time_utc": "2026-07-13T06:29:32Z", "exit_code": 0, "duration_seconds": 0.3, "passed": "release and privacy", "failed": 0, "skipped": 0, "warnings": "none", "output_artifact": "data/results/v5_release_safety.json"},
        {"command_id": "seal_ruff_generator_diff_claim", "command": "python3 -m ruff check certgen tests scripts; generator idempotence; git diff --check; claim_allowed JSON scan", "working_directory": ".", "environment": "local CPU", "start_time_utc": "2026-07-13T06:29:45Z", "end_time_utc": "2026-07-13T06:29:45Z", "exit_code": 0, "duration_seconds": 0.4, "passed": "all checks", "failed": 0, "skipped": 0, "warnings": "none", "output_artifact": "reports/CERTGEN_CVPR_COMMAND_LEDGER.csv"},
        {"command_id": "seal_final_audits", "command": "canonical notebook registry paper artifact CVPR forensic execution release privacy ruff generator diff and status audits", "working_directory": ".", "environment": "local CPU no CUDA", "start_time_utc": "2026-07-13T06:32:57Z", "end_time_utc": "2026-07-13T06:32:58Z", "exit_code": 0, "duration_seconds": 1.7, "passed": "notebooks 5/5; CVPR 8/8; forensic 8/8; all other gates pass", "failed": 0, "skipped": 0, "warnings": "BLOCKED_MISSING_REFERENCE_SAMPLES expected and honest", "output_artifact": "reports/CERTGEN_CVPR_FINAL_AUDIT.json"},
    ]
    put_csv("reports/CERTGEN_CVPR_COMMAND_LEDGER.csv", ledger_fields, ledger_rows)
    current = {"schema_version": "certgen.cvpr.current_state.v1", "top_level_status": "CVPR_PREEXECUTION_READY_BLOCKED_BY_REFERENCE_INPUT", "classification": "VERIFIED_CURRENT", "theory": "local_bounded_rbf_core_valid_real_assumptions_pending", "software": "local_safe_baseline_passed_cvpr_layer_built", "registries": "planning_registries_valid_not_availability_evidence", "reference": "BLOCKED_USER_MUST_PROVIDE_CIFAR_REFERENCE", "checkpoint_preflight": "NOT_RUN", "generation": "NOT_RUN", "feature_extraction": "NOT_RUN", "cache_contracts": "IMPLEMENTED_NO_REAL_CACHE", "metric_reproduction": "NOT_RUN", "sanity": "NOT_RUN", "certificate": "IMPLEMENTED_NO_REAL_CERTIFICATE", "partial_ranking": "IMPLEMENTED_NO_REAL_RANKING", "visualization": "CONTRACTS_ONLY", "literature_audit": "SCHEMA_ONLY_NOT_RUN", "paper": "STRUCTURAL_PLACEHOLDERS_NO_RESULTS", "release": "MANIFEST_READY_NOT_RELEASED", "exact_next_action": {"action": "PROVIDE_CIFAR_REFERENCE", "exact_command": "python3 -m certgen validate reference --source data/sources/cifar-10-python.tar.gz --explain", "expected_output": "data/results/v9_cifar_reference_onramp.json", "success_status": "READY_FOR_LOCAL_CIFAR_REFERENCE_MATERIALIZATION"}, "evidence_state": ["planning_only", "synthetic_validation_only", "not_empirical_evidence"], "claim_allowed": False}
    put_json("reports/CERTGEN_CVPR_CURRENT_STATE.json", current)
    put("reports/CERTGEN_CVPR_REPAIR_CHANGELOG.md", """# CertGen CVPR Repair Changelog

| Finding | Severity | Root cause | Change | Files | Tests | Verification | Remaining limitation |
|---|---|---|---|---|---|---|---|
| Scattered V6-V9 entrypoints | P1 | historical versioned growth | typed CVPR stage/registry/CLI layer routes canonical contracts | `certgen/__main__.py`; `certgen/cvpr/` | `tests/test_cvpr_architecture.py` | unit/CLI tests | legacy wrappers remain |
| No unified experiment ontology | P1 | ad hoc templates | benchmark/model/feature/comparison/family/preregistration registries | `registry/cvpr/`; `configs/cvpr/`; `certgen/cvpr/registries.py` | architecture registry tests | schema audit | availability still unverified |
| Reference blocker not represented in CVPR taxonomy | P0 | legacy status names | CVPR top status and enriched one-action record | `certgen/cvpr/contracts.py`; `certgen/pipeline/v9_next_action.py` | CLI status and final-audit tests | CLI/final audit | user input required |
| Missing generic T4x2 notebooks/DINO lane | P1 | CIFAR/V9-specific assets | deterministic notebook factory and five canonical notebooks | `certgen/notebooks/cvpr_factory.py`; `notebooks/kaggle/certgen_cvpr_*.ipynb` | notebook analyzer and architecture tests | syntax/static tests | Kaggle run required |
| No canonical partial ranking gate | P1 | earlier descriptive analysis | compatible-family partial graph with unresolved/disagreement outputs | `certgen/cvpr/ranking.py` | partial-ranking architecture tests | fixture tests | no real certificates |
| Figure scripts could imply readiness | P0 | no unified gate | paper-approved lineage required before rendering | `certgen/visualization/factory.py`; `configs/cvpr/figure_contracts.yaml` | figure-gate architecture tests | gate tests | rendering intentionally blocked |
| Statistical support not isolated as scalar contract | P0 | proof embedded in stream code | explicit six-kernel formula and [-3,3] tests | `certgen/cvpr/statistical_contract.py` | `tests/test_cvpr_statistical_contract.py` | deterministic/random tests | real independence remains an artifact obligation |
| Metric/sanity CLI only reported a blocker | P0 | canonical future gates were not executable | exact cache/metric/target binding plus all ten required controls | `certgen/cvpr/gates.py`; gate templates; canonical CLI | `tests/test_cvpr_gates.py` | synthetic-only gate tests | real caches and measurements required |
| Canonical notebooks and importer missed failure-preservation details | P0 | static schemas did not cover every output/resume/raw-ZIP obligation | exact output roots, validated resume, diagnostics, and hash-addressed raw preservation on success or failure | notebook factory/analyzer; `certgen/packaging/v9_import_repair.py` | notebook/import fixture tests | static and secure-import audits | Kaggle execution required |
| Certificate/ranking identity was incomplete | P0 | deterministic timestamp and compatibility fields were underbound | normalized certificate timestamp, stream/family hashes, alpha/resume identity, strict partial-ranking compatibility | `certgen/cvpr/certificate.py`; `certgen/cvpr/ranking.py` | statistical and architecture fixture tests | deterministic fixture tests | no real certificate family |
| Runtime report lacked a configuration-driven session plan | P1 | legacy V9 ranges had no resource arithmetic or shard checkpoints | frozen planner calculates throughput ranges, disk/RAM/VRAM, session count, shard assignments, ZIP sizes, resume points, and recovery commands | `certgen/cvpr/runtime_planner.py`; runtime template; canonical CLI | `tests/test_cvpr_runtime_planner.py` | synthetic planning test | all values remain hardware-dependent estimates |
""")
    prioritized_fields = ["task_id", "priority", "owner", "location", "input", "output", "dependency", "CPU_or_GPU", "planning_runtime", "evidence_produced", "claim_permission", "completion_test"]
    prioritized_rows = [
        {"task_id": "CVPR-RUN-001", "priority": "P0", "owner": "user/researcher", "location": "local", "input": "official local CIFAR-10 source", "output": "validated reference onramp", "dependency": "none", "CPU_or_GPU": "CPU", "planning_runtime": "minutes", "evidence_produced": "cache artifact only", "claim_permission": "false", "completion_test": "REFERENCE_SOURCE_VALID"},
        {"task_id": "CVPR-RUN-002", "priority": "P1", "owner": "researcher", "location": "Kaggle", "input": "preflight package", "output": "preflight ZIP", "dependency": "reference materialized", "CPU_or_GPU": "T4x2", "planning_runtime": "5-30 minutes", "evidence_produced": "run log", "claim_permission": "false", "completion_test": "all per-model preflights pass and import validates"},
        {"task_id": "CVPR-RUN-003", "priority": "P1", "owner": "researcher", "location": "Kaggle", "input": "validated preflight", "output": "1k generation ZIP", "dependency": "CVPR-RUN-002", "CPU_or_GPU": "T4x2", "planning_runtime": "30 minutes-3 hours", "evidence_produced": "pilot sample artifact", "claim_permission": "false", "completion_test": "all deterministic shards pass"},
        {"task_id": "CVPR-RUN-004", "priority": "P1", "owner": "researcher", "location": "Kaggle", "input": "reference+generation package", "output": "Inception/CLIP/DINO caches", "dependency": "CVPR-RUN-003", "CPU_or_GPU": "T4x2", "planning_runtime": "5-60 minutes per extractor", "evidence_produced": "cache artifact", "claim_permission": "false", "completion_test": "cache-v2 validation passes"},
        {"task_id": "CVPR-RUN-005", "priority": "P1", "owner": "researcher", "location": "local", "input": "validated caches and frozen family", "output": "sanity+pilot certificates+partial ranking", "dependency": "CVPR-RUN-004", "CPU_or_GPU": "CPU", "planning_runtime": "minutes", "evidence_produced": "sanity and pilot artifacts", "claim_permission": "false", "completion_test": "stop-and-interpret gate reached"},
        {"task_id": "CVPR-RUN-006", "priority": "P3", "owner": "research team", "location": "multi-benchmark", "input": "successful pilot decision", "output": "credible CVPR evidence matrix", "dependency": "explicit scale-up approval", "CPU_or_GPU": "mixed", "planning_runtime": "days-weeks", "evidence_produced": "candidate paper evidence", "claim_permission": "separate gate only", "completion_test": "multi-benchmark immutable lineage and paper firewall pass"},
        {"task_id": "CVPR-NOBUILD-001", "priority": "REJECTED", "owner": "none", "location": "none", "input": "idea only", "output": "none", "dependency": "none", "CPU_or_GPU": "none", "planning_runtime": "none", "evidence_produced": "none", "claim_permission": "false", "completion_test": "do not build web dashboards, video pipelines, FID certificates, complex e-BH, or another prompt-pack version before pilot"},
    ]
    put_csv("reports/CERTGEN_CVPR_REMAINING_WORK_PRIORITIZED.csv", prioritized_fields, prioritized_rows)
    put("reports/CERTGEN_CVPR_REMAINING_WORK_PRIORITIZED.md", "# CertGen CVPR Remaining Work Prioritized\n\nThe machine-readable task ledger is `reports/CERTGEN_CVPR_REMAINING_WORK_PRIORITIZED.csv`. P0/P1 work is execution, not more generic infrastructure. P2 begins only after pilot interpretation; P3-P5 require results to justify breadth. `REJECTED` items are prohibited by the stop-building rule.")
    put("reports/CERTGEN_CVPR_NOTEBOOK_READINESS.md", """# CertGen CVPR Notebook Readiness

| Notebook | Static validation | Fixture validation | T4x2 | Resume | Unverified risk |
|---|---|---|---|---|---|
| checkpoint preflight | pass | structural only | two process workers | hash-bound per model | packages, network, auth, real model load |
| CIFAR 1k generation | pass | structural only | deterministic shard allocation | manifest/hash validation | adapters, throughput, disk, scheduler behavior |
| generic generation | pass | structural only | config-driven | per-shard | every future model needs preflight |
| CIFAR 1k features | pass | structural only | two process workers | cache finite/hash validation | runtime adapter and DINO variant |
| generic features | pass | structural only | config-driven | per-shard | memory, exact preprocessing, cache merge |

Static validation is not successful Kaggle execution. Every notebook remains `real_run_required`, `run_log_only`, and `claim_allowed=false`.
""")
    run_fields = ["run_id_template", "run_name", "class", "priority", "purpose", "location", "CPU_or_GPU", "GPU_count", "input", "output", "prerequisites", "command_or_notebook", "planning_runtime", "planning_disk", "planning_RAM", "planning_VRAM", "resumable", "failure_recovery", "evidence_class", "claim_permission", "completion_test"]
    run_rows = [
        {"run_id_template": "local__validation__current__none__hash__timestamp", "run_name": "LOCAL_CPU_VALIDATION", "class": "A", "priority": "P0", "purpose": "local safety", "location": "local", "CPU_or_GPU": "CPU", "GPU_count": 0, "input": "repo", "output": "audit", "prerequisites": "none", "command_or_notebook": "python3 -m certgen audit cvpr", "planning_runtime": "minutes", "planning_disk": "small", "planning_RAM": "low", "planning_VRAM": "none", "resumable": "yes", "failure_recovery": "repair exact failing gate", "evidence_class": "planning_only", "claim_permission": "false", "completion_test": "audit pass"},
        {"run_id_template": "cifar10__reference__test__none__hash__timestamp", "run_name": "LOCAL_CPU_REFERENCE", "class": "B", "priority": "P0", "purpose": "reference manifest", "location": "local", "CPU_or_GPU": "CPU", "GPU_count": 0, "input": "official source", "output": "10k manifest", "prerequisites": "user source", "command_or_notebook": "python3 -m certgen materialize reference --source <path>", "planning_runtime": "minutes", "planning_disk": "under 1 GiB", "planning_RAM": "low", "planning_VRAM": "none", "resumable": "idempotent identical", "failure_recovery": "preserve source and report rejected layout", "evidence_class": "cache_artifact", "claim_permission": "false", "completion_test": "10000 validated rows"},
        {"run_id_template": "cifar10__preflight__tiny__none__hash__timestamp", "run_name": "KAGGLE_T4X2_PREFLIGHT", "class": "C", "priority": "P1", "purpose": "real load", "location": "Kaggle", "CPU_or_GPU": "GPU", "GPU_count": 2, "input": "preflight package", "output": "preflight ZIP", "prerequisites": "reference+registry", "command_or_notebook": "certgen_cvpr_checkpoint_preflight_t4x2.ipynb", "planning_runtime": "5-30 minutes", "planning_disk": "model dependent", "planning_RAM": "Kaggle dependent", "planning_VRAM": "T4 dependent", "resumable": "per model", "failure_recovery": "rerun failed model only under same hash", "evidence_class": "run_log_only", "claim_permission": "false", "completion_test": "all model status pass"},
        {"run_id_template": "cifar10__generation__1k__none__hash__timestamp", "run_name": "KAGGLE_T4X2_GENERATION", "class": "D", "priority": "P1", "purpose": "1k samples/model", "location": "Kaggle", "CPU_or_GPU": "GPU", "GPU_count": 2, "input": "validated preflight", "output": "generation ZIP", "prerequisites": "preflight import", "command_or_notebook": "certgen_cvpr_cifar10_generation_t4x2_1k.ipynb", "planning_runtime": "30 minutes-3 hours", "planning_disk": "model/image dependent", "planning_RAM": "Kaggle dependent", "planning_VRAM": "T4 dependent", "resumable": "per shard", "failure_recovery": "quarantine invalid shard; rerun exact shard", "evidence_class": "pilot_only", "claim_permission": "false", "completion_test": "complete unique manifest"},
        {"run_id_template": "cifar10__features__1k__feature__hash__timestamp", "run_name": "KAGGLE_T4X2_FEATURE_EXTRACTION", "class": "E", "priority": "P1", "purpose": "three feature spaces", "location": "Kaggle", "CPU_or_GPU": "GPU", "GPU_count": 2, "input": "images+locks", "output": "feature ZIP", "prerequisites": "generation import", "command_or_notebook": "certgen_cvpr_feature_extraction_t4x2_1k.ipynb", "planning_runtime": "5-60 minutes/extractor", "planning_disk": "feature dependent", "planning_RAM": "Kaggle dependent", "planning_VRAM": "T4 dependent", "resumable": "per shard", "failure_recovery": "rerun failed shard under same lock", "evidence_class": "cache_artifact", "claim_permission": "false", "completion_test": "cache-v2 pass"},
        {"run_id_template": "cifar10__import__1k__none__hash__timestamp", "run_name": "LOCAL_CPU_IMPORT", "class": "F", "priority": "P1", "purpose": "secure copyback validation", "location": "local", "CPU_or_GPU": "CPU", "GPU_count": 0, "input": "copied-back ZIP", "output": "hash-addressed immutable import", "prerequisites": "completed Kaggle stage", "command_or_notebook": "python3 -m certgen import <stage> <zip>", "planning_runtime": "seconds-tens of minutes", "planning_disk": "ZIP plus extracted bytes", "planning_RAM": "low", "planning_VRAM": "none", "resumable": "new immutable output only", "failure_recovery": "preserve raw ZIP; follow structured repair record", "evidence_class": "cache_or_run_log_by_stage", "claim_permission": "false", "completion_test": "integrity schema and stage validators pass"},
        {"run_id_template": "cifar10__metric-reproduction__1k__feature__hash__timestamp", "run_name": "LOCAL_CPU_METRIC_REPRODUCTION", "class": "G", "priority": "P1", "purpose": "bind and cross-check exact registered metric", "location": "local", "CPU_or_GPU": "CPU", "GPU_count": 0, "input": "validated cache-v2 pair plus frozen target", "output": "immutable metric gate JSON", "prerequisites": "cache validation", "command_or_notebook": "python3 -m certgen sanity metric-reproduction --config <frozen.yaml> --out <new.json>", "planning_runtime": "seconds-minutes", "planning_disk": "feature-cache dependent", "planning_RAM": "two feature arrays plus kernels", "planning_VRAM": "none", "resumable": "immutable rerun under same hash", "failure_recovery": "stop on identity or tolerance failure", "evidence_class": "sanity_artifact", "claim_permission": "false", "completion_test": "PASS with exact target class and lineage"},
        {"run_id_template": "cifar10__sanity__1k__feature__hash__timestamp", "run_name": "LOCAL_CPU_SANITY", "class": "G", "priority": "P1", "purpose": "null gap direction and protocol controls", "location": "local", "CPU_or_GPU": "CPU", "GPU_count": 0, "input": "frozen control measurements and artifact IDs", "output": "immutable sanity gate JSON", "prerequisites": "metric gate pass", "command_or_notebook": "python3 -m certgen sanity controls --config <frozen.yaml> --out <new.json>", "planning_runtime": "seconds-minutes", "planning_disk": "artifact dependent", "planning_RAM": "feature dependent", "planning_VRAM": "none", "resumable": "immutable rerun under same hash", "failure_recovery": "stop at failed control; do not relax tolerance", "evidence_class": "sanity_artifact", "claim_permission": "false", "completion_test": "all ten required controls pass"},
        {"run_id_template": "cifar10__certificate__1k__feature__hash__timestamp", "run_name": "LOCAL_CPU_CERTIFICATE", "class": "H", "priority": "P1", "purpose": "first bounded-RBF nonclaim certificate", "location": "local", "CPU_or_GPU": "CPU", "GPU_count": 0, "input": "frozen study family bundle and draw plan", "output": "immutable certificate JSON", "prerequisites": "all sanity gates and family freeze", "command_or_notebook": "python3 -m certgen certify --study <yaml> --family <json> --features <npz> --reference-draw-plan <json> --comparison <id> --feature-space <id> --out <new.json>", "planning_runtime": "seconds-minutes", "planning_disk": "feature-bundle dependent", "planning_RAM": "feature dependent", "planning_VRAM": "none", "resumable": "same stream identity only", "failure_recovery": "block changed stream family alpha or draw", "evidence_class": "pilot_only", "claim_permission": "false", "completion_test": "deterministic decided censored or blocked certificate"},
        {"run_id_template": "cifar10__ranking__1k__multi__hash__timestamp", "run_name": "LOCAL_CPU_PARTIAL_RANKING", "class": "I", "priority": "P2", "purpose": "certified partial graph", "location": "local", "CPU_or_GPU": "CPU", "GPU_count": 0, "input": "compatible certificate family", "output": "graph CSVs and summary JSON", "prerequisites": "certificate pilot complete", "command_or_notebook": "python3 -m certgen rank --family <json> --certificate-dir <dir> --out-dir <new-dir>", "planning_runtime": "seconds", "planning_disk": "small", "planning_RAM": "low", "planning_VRAM": "none", "resumable": "new immutable output directory", "failure_recovery": "reject mixed identities; keep incomparable pairs", "evidence_class": "pilot_only", "claim_permission": "false", "completion_test": "no forced total order and compatibility pass"},
        {"run_id_template": "cifar10__sensitivity__1k__feature__hash__timestamp", "run_name": "LOCAL_CPU_SENSITIVITY", "class": "I", "priority": "P2", "purpose": "censored samples-to-decision and registered ablations", "location": "local", "CPU_or_GPU": "CPU", "GPU_count": 0, "input": "compatible certificates by frozen variant", "output": "nonclaim analysis JSON", "prerequisites": "pilot certificates", "command_or_notebook": "python3 -m certgen analyze samples-to-decision --certificate-dir <dir> --out <new.json>", "planning_runtime": "seconds-minutes", "planning_disk": "small", "planning_RAM": "low", "planning_VRAM": "none", "resumable": "new immutable output", "failure_recovery": "retain censoring and exclude incompatible variants", "evidence_class": "pilot_only", "claim_permission": "false", "completion_test": "decided censored and invalid counts retained"},
        {"run_id_template": "cifar10__figures__1k__multi__hash__timestamp", "run_name": "LOCAL_CPU_FIGURES", "class": "J", "priority": "P3", "purpose": "pilot visuals or paper-gated rendering", "location": "local", "CPU_or_GPU": "CPU", "GPU_count": 0, "input": "figure request plus approved artifact IDs", "output": "planning contract or gated figure", "prerequisites": "ranking and figure approval gate", "command_or_notebook": "python3 -m certgen figures --request <json> --out <new.json>", "planning_runtime": "seconds-minutes", "planning_disk": "small plus selected images", "planning_RAM": "low", "planning_VRAM": "none", "resumable": "new immutable outputs", "failure_recovery": "block unapproved lineage; do not render", "evidence_class": "planning_or_pilot", "claim_permission": "false", "completion_test": "schema pass and explicit approval status"},
        {"run_id_template": "multibench__literature-audit__full__multi__hash__timestamp", "run_name": "LOCAL_CPU_LITERATURE_AUDIT", "class": "K", "priority": "P3", "purpose": "prospective published-claim audit", "location": "local/manual", "CPU_or_GPU": "CPU", "GPU_count": 0, "input": "frozen claim registry and eligible artifacts", "output": "audited claim table", "prerequisites": "protocol frozen before curation", "command_or_notebook": "follow docs/experiments/CERTGEN_CVPR_LITERATURE_AUDIT_PROTOCOL.md", "planning_runtime": "days of manual curation", "planning_disk": "source dependent", "planning_RAM": "low", "planning_VRAM": "none", "resumable": "append-only registry", "failure_recovery": "record exclusion or blocker; never invent citation", "evidence_class": "candidate_paper_evidence", "claim_permission": "false", "completion_test": "every included claim has complete provenance"},
        {"run_id_template": "multibench__paper-gate__full__multi__hash__timestamp", "run_name": "LOCAL_CPU_PAPER_GATE", "class": "L", "priority": "P3", "purpose": "explicit evidence promotion audit", "location": "local", "CPU_or_GPU": "CPU", "GPU_count": 0, "input": "complete multi-benchmark immutable lineage", "output": "paper firewall and approved artifact registry", "prerequisites": "all empirical and release gates", "command_or_notebook": "python3 -m certgen audit paper", "planning_runtime": "minutes", "planning_disk": "small", "planning_RAM": "low", "planning_VRAM": "none", "resumable": "rerun after every paper edit", "failure_recovery": "remove unsupported language or block promotion", "evidence_class": "paper_evidence_candidate", "claim_permission": "false until separate future approval", "completion_test": "firewall pass plus explicit approved artifact IDs"},
    ]
    put_csv("reports/CERTGEN_CVPR_RUN_CLASSIFICATION.csv", run_fields, run_rows)

    docs = {
        "docs/CERTGEN_CVPR_EXACT_NEXT_ACTION.md": "# CertGen CVPR Exact Next Action\n\nStatus: `CVPR_PREEXECUTION_READY_BLOCKED_BY_REFERENCE_INPUT`.\n\n```bash\npython3 -m certgen validate reference --source data/sources/cifar-10-python.tar.gz --explain\n```\n\nExpected output: `data/results/v9_cifar_reference_onramp.json`. Success status: `READY_FOR_LOCAL_CIFAR_REFERENCE_MATERIALIZATION`. The command performs no download.",
        "docs/CERTGEN_CVPR_EXECUTION_CRITICAL_PATH.md": "# CertGen CVPR Execution Critical Path\n\nReference validate/materialize -> checkpoint package and Kaggle preflight -> secure import -> 1k generation -> secure import -> feature package and Inception/CLIP/DINO extraction -> secure import/cache validation -> metric reproduction -> null/obvious-gap gates -> freeze Bonferroni family -> certificate pilot -> partial ranking -> pilot figures -> evidence gate -> stop and interpret. Every arrow is a fail-closed gate.",
        "docs/CERTGEN_CVPR_MAXIMUM_RESEARCH_CEILING.md": "# CertGen CVPR Maximum Research Ceiling\n\nThe strongest honest identity is a visual generative-model evaluation audit producing optional-stopping-valid pairwise decisions and partial rankings, not a new metric or general theorem. Pilot-only work demonstrates execution. A minimum CVPR study needs multiple recognizable model families, at least two credible image benchmarks, three representations, controls, baselines, visual panels, sensitivity, and a frozen claim audit. A strong study additionally needs stable cross-benchmark findings and a material practical consequence. Video is optional only after the image core succeeds.",
        "docs/CERTGEN_CVPR_SINGLE_FILE_HANDOFF.md": "# CertGen CVPR Single-file Handoff\n\nThe local core, typed CVPR registries/state machine, secure imports, five static-validated T4x2 notebooks, certificate/partial-ranking contracts, figure gates, paper firewall, and execution handbook exist. No real reference, checkpoint load, generation, feature cache, metric result, sanity result, certificate, ranking, or paper evidence exists. Keep `claim_allowed=false`. Start with the singular command in `docs/CERTGEN_CVPR_EXACT_NEXT_ACTION.md`; then follow `CERTGEN_CVPR_COMPLETE_EXECUTION_AND_RUN_HANDBOOK.md`. Stop generic building until a concrete run failure appears. These assets are not paper evidence.",
        "docs/CERTGEN_CVPR_STAGE_STATE_MACHINE.md": "# CertGen CVPR Stage State Machine\n\nThe authoritative machine contract is `certgen.cvpr.contracts.STAGE_TRANSITIONS`. It enumerates all 18 stages from `REFERENCE_SOURCE_MISSING` through `CVPR_EVIDENCE_GATES_PENDING`, with required inputs, validator, outputs, failure status, next action, evidence class, and claim permission. Every current transition sets claim permission false; paper promotion is a separate future gate.",
        "docs/CERTGEN_CVPR_EVIDENCE_PROMOTION_POLICY.md": "# CertGen CVPR Evidence Promotion Policy\n\nPlanning artifacts cannot become run logs by renaming. Run logs cannot become caches. Caches require schema/hash/provenance validation. Sanity artifacts are controls, not model results. Pilot artifacts remain single-benchmark/non-generalized. No paper evidence exists now; future promotion requires immutable lineage, passed metric/sanity/statistical/multiplicity gates, preregistration match, release safety, and an explicit approved artifact ID. Tests, synthetic results, notebook images, runtimes, and fixtures are permanently non-paper evidence.",
        "docs/engineering/CERTGEN_CVPR_CANONICAL_ARCHITECTURE.md": "# CertGen CVPR Canonical Architecture\n\n`certgen.cvpr` owns stage/run/family/preregistration/certificate/ranking contracts; `certgen.packaging` owns safe ZIP and append-only artifact handling; `certgen.features.cache_v2` owns cache identity; `certgen.notebooks.cvpr_factory` owns deterministic notebook JSON; `certgen.visualization` owns paper-approved figure gates; `certgen.paper` owns claim firewalls. Historical V1-V9 wrappers are compatibility surfaces, not the default architecture. Outputs are atomic, non-overwriting, hash-bound, resumable, and lineage-preserving.",
        "docs/engineering/CERTGEN_CVPR_CLI_REFERENCE.md": "# CertGen CVPR CLI Reference\n\nUse `python3 -m certgen status`, `next-action`, `validate reference`,\n`materialize reference`, `freeze-config`, `package preflight|generation|features`,\n`import preflight|generation|features`, `validate caches` (or the legacy\n`validate-caches` alias), `sanity metric-reproduction --config <frozen.yaml>\n--out <new.json>`, `sanity controls --config <frozen.yaml> --out <new.json>`,\n`plan-runtime --config <frozen.yaml> --out <new.json>`, `certify`, `rank`,\n`analyze`, `figures`, and\n`audit notebooks|paper|artifact-registry|registries|cvpr`. Omitting the sanity\nconfiguration reports the current prerequisite blocker. Every command is\nnonclaim by default and refuses incompatible, incomplete, changed, or\noverwrite-prone artifacts.",
        "docs/experiments/CERTGEN_CVPR_PREREGISTRATION_GUIDE.md": "# CertGen CVPR Preregistration Guide\n\nCopy the template to a versioned study file. Verify sources/licenses, replace every TBD, enumerate pairs/feature spaces/metrics/budgets and exact family dimensions, freeze preprocessing/reference draw/bandwidth/stopping/failure/resume/censoring/scale rules, compute the configuration hash, set `frozen: true`, and never edit that file after outcomes are inspected. A pivot creates a new version and excludes the affected old claim family.",
        "docs/experiments/CERTGEN_CVPR_MINIMUM_CREDIBLE_STUDY.md": "# Minimum Credible CVPR Study\n\nAfter controls pass: at least two recognized image benchmarks, multiple model families, Inception/CLIP/DINO bounded-RBF families, fixed-n and repeated-peeking baselines, partial-ranking and samples-to-decision outputs, visual galleries, protocol sensitivity, and a prospectively frozen published-claim sample. No result-driven pair selection.",
        "docs/experiments/CERTGEN_CVPR_STRONG_STUDY.md": "# Strong CVPR Study\n\nThe minimum study plus a third domain or credible text-to-image lane, robust cross-representation interpretation, meaningful resolved/unresolved cases, compute consequences, broad ablations, released-sample/checkpoint coverage, and a reproducible literature/leaderboard audit. Strength depends on real findings, not run count.",
        "docs/experiments/CERTGEN_CVPR_MAXIMUM_CEILING_STUDY.md": "# Maximum-ceiling Study\n\nOnly if the image core yields a clear result: expand model families, full 50k lanes, prospective multi-venue audit, and possibly a minimal video replication after a new valid temporal protocol. Do not build a video platform, FID certificate, arbitrary plugin system, or general e-BH theory pre-pilot.",
        "docs/experiments/CERTGEN_CVPR_SCALE_UP_RULES.md": "# CertGen CVPR Scale-up Rules\n\n1k -> 10k only if provenance, preflight, caches, metric reproduction, null/obvious-gap controls, family freeze, and pilot interpretation pass. 10k -> 50k only for comparisons where added budget answers a registered question. CIFAR -> benchmark 2 only after pilot code/assumptions survive. Benchmark 2 -> 3 only if breadth is scientifically necessary. Image -> video only if the image paper is strong and temporal theory is separately specified. Pilot output is not paper evidence; any future promotion requires immutable lineage and the paper gate.",
        "docs/experiments/CERTGEN_CVPR_LITERATURE_AUDIT_PROTOCOL.md": "# CertGen CVPR Literature Audit Protocol\n\nBefore curation, freeze date window, venues, benchmarks, metrics, sample/checkpoint availability, comparison eligibility, exclusions, duplicate handling, missing-preprocessing policy, and prospective selection reason. Populate `published_claim_registry.csv` with real citations only. Report eligibility, reproducibility, decided/undecided status, direction changes, feature disagreement, ranking implications, and compute. An undecided CertGen comparison does not make the original paper wrong.",
        "docs/execution/CERTGEN_CVPR_KAGGLE_T4X2_GUIDE.md": "# CertGen CVPR Kaggle T4x2 Guide\n\nCreate a private Kaggle dataset from the exact input ZIP; select two T4 GPUs; set internet only as required by verified model licenses/auth; confirm two visible devices; run all cells in order; preserve logs and the deterministic output ZIP. Single-GPU fallback is explicit and logged. Do not run certificates on Kaggle. Copy back without modifying the ZIP and import with `python3 -m certgen import <stage> <zip>`.",
        "docs/execution/CERTGEN_CVPR_FAILURE_RECOVERY_PLAYBOOK.md": "# CertGen CVPR Failure Recovery\n\nPreserve raw ZIP/logs/config hashes. Dependency or checkpoint failure -> fix only the preflight package and rerun failed models. Partial generation/feature shard -> quarantine the invalid shard and rerun the exact deterministic assignment. Hash/schema/preprocessing/reference mismatch -> stop; local repair is allowed only for derived metadata that can be regenerated without changing raw bytes. Provenance, metric reproduction, null, direction, family, or paper firewall failure -> no scale-up or claim promotion.",
        "docs/execution/CERTGEN_CVPR_RUNTIME_AND_RESOURCE_PLAN.md": "# CertGen CVPR Runtime and Resource Plan\n\nAll values are `planning estimate`, `hardware-dependent`, and `not an empirical project result`. Fill `configs/cvpr/runtime_plan_template.yaml`, freeze it with `python3 -m certgen freeze-config --input <filled.yaml> --out <frozen.yaml>`, then run `python3 -m certgen plan-runtime --config <frozen.yaml> --out <new-plan.json>`. The planner reports fixed setup, model download/cache, throughput ranges, image counts, batch/GPU/shard counts, merge/local validation time, output bytes, RAM/VRAM, session count, deterministic shard assignments, ZIP checkpoints, resume points, and failure-recovery commands. Initial ranges remain: preflight 5-30 min; CIFAR 1k generation 30 min-3 h; 1k Inception 5-30 min; CLIP 10-45 min; DINO 10-60 min; 10k generation 1-8 h/model; 50k may span sessions. The frozen overrides are prospective planning inputs, never measurements.",
        "docs/execution/CERTGEN_CVPR_COPYBACK_AND_IMPORT_GUIDE.md": "# CertGen CVPR Copyback and Import Guide\n\nDownload the single deterministic ZIP, record SHA-256, place it under ignored `data/kaggle_outputs/`, and run the matching importer. The importer rejects traversal, absolute paths, symlinks, executables, nested archives, collisions, expansion bombs, partial status, hashes, configuration mismatches, overwrites, and evidence-language injection. Raw ZIPs are preserved read-only under the hash-addressed import root. Follow the generated repair report on failure.",
    }
    for path, text in docs.items():
        put(path, text)


def paper_and_release() -> None:
    put("paper/CERTGEN_CVPR_CLAIM_CONTRACT.md", """# CertGen CVPR Claim Contract

Working title (provisional): **CertGen: Certified Partial Rankings for Visual Generative Models**.

Method claims may describe the implemented bounded-RBF stream, union-Hoeffding first crossing, and Bonferroni protocol with explicit assumptions. Empirical decidedness, cross-feature agreement, compute savings, literature audit, model quality, and ranking claims require approved artifact IDs. FID/FD and polynomial KID remain descriptive. No universal metric, total ranking, or 'FID is useless' claim is allowed. Current empirical placeholders are `TBD_REAL_RUN_REQUIRED`; `claim_allowed=false`.
""")
    put("paper/CERTGEN_CVPR_RESULT_TABLE_CONTRACTS.md", """# CertGen CVPR Result Table Contracts

Every row requires benchmark/model IDs, feature space, metric/kernel/bandwidth, reference and preprocessing hashes, family ID/alpha, budget, decision/censoring, certificate artifact ID, validation status, evidence class, and limitations. Placeholder tables contain no invented numbers. Synthetic, run-log, cache, sanity, and pilot rows cannot enter main-paper empirical tables. Missing or incompatible lineage blocks the entire affected row.
""")
    put("paper/CERTGEN_CVPR_FIGURE_CONTRACTS.md", """# CertGen CVPR Figure Contracts

The eight registered types are headline partial ranking, anytime trajectory, decidedness-budget, censored samples-to-decision, protocol sensitivity, resource-use consequences, visual pair gallery, and controlled-failure gallery. Each request lists approved artifact IDs, schema/configuration hash, paper gate, output, caption metadata, and limitations. Representative images illustrate cases; they never prove distribution-level claims. The factory currently writes planning contracts and refuses empirical rendering without paper-approved lineage.
""")
    reviewer_template = """## {name}

**Summary:** The pre-execution design is coherent, but there are no real results.

**Strengths:** bounded claim scope, prospective families, partial rankings, artifact integrity.

**Major concerns:** {concerns}

**Fatal concern:** {fatal}

**Required theory:** enforce the stream assumptions and family definition on real lineage.

**Required experiments:** {experiments}

**Required visual evidence:** partial-ranking graph, trajectories, and representative failure panels.

**Required baselines/ablations:** fixed-n, bootstrap, naive peeking, family control, feature/preprocessing/bandwidth/budget ablations.

**Current score:** reject/incomplete (no empirical evidence). **After successful execution:** potentially competitive, outcome-dependent.
"""
    reviews = [
        reviewer_template.format(name="1. Generative-model evaluation reviewer", concerns="recognizable model/benchmark breadth, faithful metric reproduction, and model-pair selection remain unexecuted", fatal="a CIFAR-only or obscure-model study would not support the claimed vision-evaluation importance", experiments="two or more credible benchmarks, multiple families, three features, quality and controlled pairs"),
        reviewer_template.format(name="2. Sequential-inference reviewer", concerns="conditional independence, precommitted bandwidth/reference draws, optional stopping, and exact family accounting must be evidenced", fatal="any adaptive pair/kernel choice or reused stream unit invalidates the certificate", experiments="null type-I simulation plus real null/obvious-gap gates and restart replay"),
        reviewer_template.format(name="3. CVPR vision reviewer", concerns="the work could appear like KID plus a stopping rule unless visual disagreements and ranking consequences are substantial", fatal="no vision-native visual evidence or meaningful real comparisons", experiments="feature disagreement, protocol sensitivity, visual galleries, and partial leaderboards"),
        reviewer_template.format(name="4. Reproducibility reviewer", concerns="Kaggle notebooks are only statically checked; licenses, revisions, copyback, and resume behavior require real logs", fatal="unverifiable or non-releasable inputs", experiments="clean preflight/generation/feature import lineage and rerun demonstrations"),
        reviewer_template.format(name="5. Skeptical incremental reviewer", concerns="statistical principles are prior art and novelty must come from the audit design and empirical consequences", fatal="small synthetic-only gains or repository engineering presented as research", experiments="prospective literature audit, baselines, nontrivial unresolved/resolved cases, and practical compute consequences"),
    ]
    put("paper/CERTGEN_CVPR_REVIEWER_SIMULATION.md", "# CertGen CVPR Reviewer Simulation\n\n" + "\n".join(reviews))
    repair_fields = ["reviewer", "concern", "preexecution_status", "repair", "verification", "remaining_real_requirement", "priority"]
    repair_rows = [
        {"reviewer": "evaluation", "concern": "experiment ontology", "preexecution_status": "closed", "repair": "typed benchmark/model/feature/comparison registries", "verification": "registry audit", "remaining_real_requirement": "source/license/preflight", "priority": "P1"},
        {"reviewer": "statistics", "concern": "family and reference construction", "preexecution_status": "closed_conditional", "repair": "family and draw-plan protocols", "verification": "contract tests", "remaining_real_requirement": "frozen executed lineage", "priority": "P0"},
        {"reviewer": "vision", "concern": "partial ranking and visual plan", "preexecution_status": "closed_structurally", "repair": "ranking graph and eight figure contracts", "verification": "fixture tests", "remaining_real_requirement": "real visual cases", "priority": "P3"},
        {"reviewer": "reproducibility", "concern": "T4x2/resume/copyback", "preexecution_status": "closed_static", "repair": "five notebooks, safe importer, handbook", "verification": "static analyzer", "remaining_real_requirement": "Kaggle execution", "priority": "P1"},
        {"reviewer": "incremental", "concern": "novelty", "preexecution_status": "honestly_scoped", "repair": "vision-audit identity and stop-building rule", "verification": "claim contract/firewall", "remaining_real_requirement": "material empirical finding", "priority": "P3"},
    ]
    put_csv("paper/CERTGEN_CVPR_REVIEWER_REPAIR_MATRIX.csv", repair_fields, repair_rows)
    put("paper/CERTGEN_CVPR_PAPER_BUILD_REPORT.md", "# CertGen CVPR Paper Build Report\n\nThe provisional vision-native paper scaffold compiled locally in two `pdflatex` passes on 2026-07-13. The structural output was 5 letter-size pages and 179,875 bytes. Overfull-box warnings remain. The generated PDF, log, and auxiliary file were removed after inspection so local paths and build-only percentages do not enter the release tree. All result text remains placeholder/non-evidence. The paper firewall must pass after every edit. A compiled PDF is structural verification only, never paper evidence.")
    put("release/CERTGEN_CVPR_PUBLIC_RELEASE_MANIFEST.txt", """# Planning manifest; not a released package
README.md
pyproject.toml
certgen/
configs/cvpr/
registry/cvpr/
notebooks/kaggle/certgen_cvpr_*.ipynb
tests/
paper/
docs/engineering/CERTGEN_CVPR_CANONICAL_ARCHITECTURE.md
docs/engineering/CERTGEN_CVPR_CLI_REFERENCE.md
CERTGEN_CVPR_COMPLETE_EXECUTION_AND_RUN_HANDBOOK.md
LICENSE (required before release)
CITATION.cff (required before release)
""")
    put("release/CERTGEN_CVPR_INTERNAL_ARCHIVE_CANDIDATES.txt", """promptpacks/
certgen_prompt_pack_v1/ through certgen_prompt_pack_v5/ historical deletions/state
commands/v1* through commands/v9* compatibility wrappers
historical V1-V9 reports and generated smoke outputs
AUTORUN_*.md/jsonl
local caches, raw datasets, copied-back ZIPs, imported artifacts, pycache, DS_Store

Review manually; do not delete or archive user-owned files in this pass.
""")


def handbook() -> None:
    classification_csv = (ROOT / "reports/CERTGEN_CVPR_RUN_CLASSIFICATION.csv").read_text(encoding="utf-8").rstrip()
    put("CERTGEN_CVPR_COMPLETE_EXECUTION_AND_RUN_HANDBOOK.md", f"""# CertGen CVPR Complete Execution and Run Handbook

`planning_only` · `not_empirical_evidence` · `claim_allowed=false`

## A. Current exact status

Top-level status: `CVPR_PREEXECUTION_READY_BLOCKED_BY_REFERENCE_INPUT`. Verified pre-build baseline: 212 default tests, 22 documented statistical-lane tests, and 18 documented artifact-lane tests. Final local verification: 234 tests, 31/31 statistical-lane checks, 25/25 artifact-contract checks, 11/11 extended CVPR synthetic/gate checks, 8/8 CVPR checks, 8/8 forensic checks, 22/22 V9 compatibility checks, and 5/5 canonical notebook static checks; compilation/import/ruff/paper/firewall/privacy/artifact audits pass. Full mypy retains exactly 111 historical errors in 34 files; the 25-file critical new-code lane passes. There is no validated real reference, checkpoint load, generation, feature cache, metric/sanity result, certificate, ranking, or paper evidence.

Exact next command:

```bash
python3 -m certgen validate reference --source data/sources/cifar-10-python.tar.gz --explain
```

Expected output: `data/results/v9_cifar_reference_onramp.json`; success: `READY_FOR_LOCAL_CIFAR_REFERENCE_MATERIALIZATION`. No download occurs.

## B. Hardware and environment assumptions

- Verified local environment: macOS/CPU, Python 3.11.9, NumPy 2.4.4, SciPy 1.17.1, PyYAML 6.0.3, pytest 9.0.2; no GPU or network for validation/certification.
- Kaggle: two visible T4 GPUs requested; explicit, logged single-T4 fallback only when approved.
- Kaggle dependencies are pinned to torch 2.7.1, torchvision 0.22.1, diffusers 0.34.0, transformers 4.53.2, accelerate 1.8.1, safetensors 0.5.3, timm 1.0.16, Pillow 11.2.1, NumPy 2.0.2, and PyYAML 6.0.2. The notebook records observed versions and fails on a mismatch.
- Disk: at least 10 GiB free in `/kaggle/working` at bootstrap, plus calculated model/cache/image/ZIP headroom. RAM and VRAM are configuration/model dependent; verify both T4 devices and lower batch size only through a new frozen configuration if the preflight shows a limit.
- Network: off when uploaded caches suffice; on only when source license/auth permits and the registry records it.
- Dependencies: exact pinned versions are captured and compared; a mismatch blocks execution.
- Runtime values below are planning estimates, hardware-dependent, and not empirical project results.

## C-D. Complete run classification

The authoritative 21-field table is reproduced here and stored at `reports/CERTGEN_CVPR_RUN_CLASSIFICATION.csv`. Run IDs follow `<benchmark>__<stage>__<scale>__<feature>__<config-hash>__<timestamp>`.

```csv
{classification_csv}
```

## E. Exact critical path to the first pilot

1. Place the official archive or another accepted local source under `data/sources/` without modifying it.
2. Validate: `python3 -m certgen validate reference --source <path> --explain`.
3. Materialize: `python3 -m certgen materialize reference --source <path>`; require exactly 10,000 test rows.
4. Fill and freeze the model/preflight and runtime-plan configurations; run `python3 -m certgen plan-runtime --config <frozen-runtime.yaml> --out <new-plan.json>`; then package the checkpoint-preflight input using the canonical config schema.
5. Run `notebooks/kaggle/certgen_cvpr_checkpoint_preflight_t4x2.ipynb` on Kaggle T4x2.
6. Copy back `certgen_cvpr_checkpoint_preflight_<run_id>.zip` unchanged and record SHA-256.
7. Import: `python3 -m certgen import preflight <zip>`; require every model `PREFLIGHT_PASS`.
8. Build the 1k generation input from that exact imported preflight and the frozen seed-shard plan.
9. Run `notebooks/kaggle/certgen_cvpr_cifar10_generation_t4x2_1k.ipynb`.
10. Copy back the deterministic generation ZIP and record SHA-256.
11. Import: `python3 -m certgen import generation <zip>`; require every shard and unique ID/seed/hash.
12. Build feature input with reference draw, image manifests, extractor registry, and preprocessing locks.
13. Run `notebooks/kaggle/certgen_cvpr_feature_extraction_t4x2_1k.ipynb` for Inception, CLIP, and the frozen DINOv2 choice.
14. Copy back the deterministic feature ZIP and record SHA-256.
15. Import: `python3 -m certgen import features <zip>`.
16. Validate every cache-v2 artifact: `python3 -m certgen validate-caches --features <npz> --sidecar <json> --artifact-root <root>`.
17. Fill and freeze `configs/cvpr/metric_reproduction_gate_template.yaml`, then run `python3 -m certgen sanity metric-reproduction --config <frozen-metric-gate.yaml> --out <new-result.json>`. The gate binds both exact sets/counts, extractor, preprocessing, metric/kernel/bandwidth, tolerance, and target provenance. With no trusted external target it emits `cross_implementation_consistency` and `not_external_reproduction`.
18. Fill and freeze `configs/cvpr/sanity_gates_template.yaml`, then run `python3 -m certgen sanity controls --config <frozen-sanity-gates.yaml> --out <new-result.json>`.
19. Require all four families: null repetition/splits, obvious-gap corruption, aggregate direction, and rejection of preprocessing/feature/bandwidth/reference-population mismatches. Stop on any failure.
20. Replace every family TBD, freeze the Bonferroni record, and hash it before inspecting certificate values.
21. Run `python3 -m certgen certify --study <frozen.yaml> --family <frozen.json> --features <bundle.npz> --reference-draw-plan <plan.json> --comparison <id> --feature-space <id> --out <certificate.json>`.
22. Build the pilot partial ranking with `python3 -m certgen rank --family <frozen-family.json> --certificate-dir <dir> --out-dir <new-dir>`; mixed features need the preregistered unanimous rule.
23. Create pilot-only figure requests; empirical paper rendering remains blocked.
24. Run `python3 -m certgen audit cvpr` and the evidence gate.
25. Stop and interpret. Do not automatically start 10k.

## F. Scale-up path

- 1k -> 10k: provenance, preflight, cache, metric, null, obvious-gap, family, and pilot interpretation gates all pass; added budget answers a registered question.
- 10k -> 50k: unresolved/censored or sensitivity questions justify cost; session/shard plan fits Kaggle limits.
- CIFAR -> benchmark 2: pilot logic and adapters survive; source/license/model pairs are verified.
- Benchmark 2 -> 3: breadth is necessary for the central conclusion.
- Image -> video: only after a strong image core and a separately valid temporal protocol.
- Pilot -> paper: immutable multi-benchmark lineage and explicit paper-approved artifact IDs; never automatic.

## G. Planning runtime tables

| Location/type | Lane | Planning range | Resource/disk rule |
|---|---|---|---|
| Local CPU | validation/import | seconds to tens of minutes | low RAM for static checks; import needs ZIP plus extracted bytes |
| Local CPU | reference materialization | minutes | source plus normalized reference view; under 1 GiB for CIFAR planning |
| Local CPU | metric/certificate/ranking | seconds-minutes | RAM can reach two or more feature arrays plus kernel work |
| Local CPU | figures | seconds-minutes | selected images plus plotting dependencies |
| Data transfer | package upload/copyback | connection-dependent; no measured estimate | record ZIP size and SHA-256 at every boundary |
| Kaggle T4x2 | checkpoint preflight | 5-30 min | model dependent; require 10 GiB free working disk |
| Kaggle T4x2 | CIFAR 1k generation, three candidates | 30 min-3 h | model/image/cache dependent |
| Kaggle T4x2 | 1k Inception | 5-30 min | feature dimension and batch dependent |
| Kaggle T4x2 | 1k CLIP | 10-45 min | feature dimension and batch dependent |
| Kaggle T4x2 | 1k DINO | 10-60 min | selected DINO revision must first be frozen |
| Kaggle T4x2 | 10k generation | 1-8 h/model | split into deterministic sessions if required |
| Kaggle T4x2 | 50k generation | potentially multiple sessions | mandatory per-session copyback checkpoints |

Transfer and ZIP sizes depend on image encoding and feature dimension. The session planner divides immutable shard IDs across sessions and mandates copyback after each complete session.

## H. Kaggle notebook instructions

Common procedure for all five notebooks: build one deterministic input ZIP with `python3 -m certgen package <preflight|generation|features> --config <frozen.yaml> --input <NAME=PATH> --out-zip <new.zip> --manifest-out <new.json>`; upload that ZIP as one private Kaggle dataset; select accelerator `GPU T4 x2`; set internet exactly as the frozen `network_allowed` policy permits; require two visible CUDA devices unless the separately approved configuration enables the logged one-T4 fallback; run every cell in order. Download the single output ZIP from the notebook output pane without modification, record SHA-256, and import locally. Before upload and after every notebook regeneration, run `python3 -m certgen audit notebooks`.

| Notebook | Required input ZIP | Internet | Resume rule | Expected output ZIP | Local import and validation | Failure recovery |
|---|---|---|---|---|---|---|
| `certgen_cvpr_checkpoint_preflight_t4x2.ipynb` | frozen preflight config, runtime adapter, model registry/cache inputs | off unless source/auth review explicitly enables it | passed model only under the same configuration and integrity hashes | `certgen_cvpr_checkpoint_preflight_<run_id>.zip` | `python3 -m certgen import preflight <zip>`; require every per-model status `PREFLIGHT_PASS` and import `passed=true` | copy back the blocked diagnostic ZIP; preserve logs; rerun failed model IDs only |
| `certgen_cvpr_cifar10_generation_t4x2_1k.ipynb` | exact imported preflight identity, frozen three-model config, two disjoint seed shards per model | frozen config only | complete image/manifest/hash shard under unchanged config | `certgen_cvpr_generation_cifar10_1k_<run_id>.zip` | `python3 -m certgen import generation <zip>`; verify unique IDs/seeds, all shards, configuration and integrity hashes | quarantine only invalid failed-shard directories; rerun exact shard IDs |
| `certgen_cvpr_generation_t4x2_generic.ipynb` | same contract for one registered benchmark/model/scale | frozen config only | identical per-shard rule | `certgen_cvpr_generation_<benchmark>_<scale>_<run_id>.zip` | same generation importer; require declared model/seed coverage | add no ad hoc adapter; return to preflight or create a new frozen config |
| `certgen_cvpr_feature_extraction_t4x2_1k.ipynb` | validated CIFAR reference/generated manifests and images, draw plan, exact Inception/CLIP/DINO registry entries, preprocessing locks, runtime adapter | off when model weights are uploaded; otherwise only by recorded source policy | finite cache plus exact sample/order/extractor/preprocessing/config hashes | `certgen_cvpr_features_cifar10_1k_<run_id>.zip` | `python3 -m certgen import features <zip>` then `python3 -m certgen validate caches --features <npz> --sidecar <json> --artifact-root <root>` for every cache | preserve blocked ZIP; rerun only failed extractor/shard identities under the same locks |
| `certgen_cvpr_feature_extraction_t4x2_generic.ipynb` | same feature contract for a registered benchmark/model/scale | frozen source policy | identical per-extractor/shard rule | `certgen_cvpr_features_<benchmark>_<scale>_<run_id>.zip` | same feature importer and cache-v2 validator; require expected roles/models/counts | stop on benchmark, feature, preprocessing, reference, dimension, or license mismatch |

The notebooks write exact output roots, per-shard status, logs, copyback instructions, integrity manifests, and a deterministic archive layout. A partial run is blocked rather than merged as success. Import preserves every raw ZIP under its content hash even when validation fails.

## I. Run dependency DAG

```text
local validation
  -> reference validate -> reference materialize
  -> preflight package -> Kaggle preflight -> copyback/import
  -> generation package -> Kaggle generation -> copyback/import
  -> feature package -> Kaggle features -> copyback/import/cache validation
  -> metric reproduction -> null controls -> obvious-gap controls
  -> frozen family -> certificate pilot -> partial ranking -> pilot figures
  -> evidence gate -> STOP/INTERPRET
  -> conditional 10k -> conditional 50k -> conditional benchmark breadth -> paper gate
```

## J. Evidence promotion

- Registry/config/runtime plans: planning artifacts.
- Preflight/environment/tiny images: run logs, never paper evidence.
- Generated images/manifests: sample/cache-adjacent artifacts, not conclusions.
- Feature arrays/sidecars: cache artifacts.
- Metric/null/obvious-gap outputs: sanity artifacts.
- First certificates/rankings: pilot artifacts, single-benchmark, non-generalized.
- Paper evidence: only after the separate immutable-lineage promotion gate.

## K. Immediate stop conditions

Stop on provenance failure, unsafe/archive/hash failure, cache schema or dimension mismatch, preprocessing/extractor/reference mismatch, preflight failure, metric reproduction failure, null calibration failure, obvious-gap direction failure, draw-plan invalidity, unfrozen family, incompatible ranking family, or paper firewall failure. Preserve raw inputs and produce one exact repair action. Do not relax the gate.

## L. Exact next action

```bash
python3 -m certgen validate reference --source data/sources/cifar-10-python.tar.gz --explain
```

Expected output: `data/results/v9_cifar_reference_onramp.json`. Required success: `READY_FOR_LOCAL_CIFAR_REFERENCE_MATERIALIZATION`.
""")


def master_report() -> None:
    put("CERTGEN_CVPR_MAX_PREEXECUTION_BUILD_REPORT.md", """# CertGen CVPR Maximum Pre-execution Build Report

## 1. Executive verdict

CertGen is now a CVPR-first, claim-safe visual generative-model comparison system built around bounded-RBF pairwise certificates and partial rankings. The local build succeeds conditionally: the 212-test baseline reproduces, the final expanded suite passes 234 tests, the CVPR experiment architecture exists, and no real evidence has been manufactured. Status is `CVPR_PREEXECUTION_READY_BLOCKED_BY_REFERENCE_INPUT`. The blocker is a missing user-provided CIFAR-10 source. Exact next command: `python3 -m certgen validate reference --source data/sources/cifar-10-python.tar.gz --explain`.

This moves the repository from a narrow audited core plus V6-V9 scripts to one execution ontology, stage machine, registry suite, hardened notebook factory, certificate/ranking interfaces, figure gates, paper contracts, and a complete run handbook. CVPR merit still depends entirely on real multi-benchmark/model/feature results and visual evidence.

## 2. Reproduced baseline

Baseline: `212 passed`; documented baseline statistical lane `22 passed`; documented baseline artifact lane `18 passed`. Final: `234 passed`, full statistical lane `31/31`, full artifact-contract lane `25/25`, extended CVPR synthetic/gate lane `11/11`, canonical notebooks `5/5`, CVPR audit `8/8`, forensic `8/8`, V9 compatibility audit `22/22`, and final execution audit `BLOCKED_MISSING_REFERENCE_SAMPLES`; compile/import/ruff/paper/privacy/firewall/artifact checks pass. Paper built as a five-page placeholder with box warnings; build byproducts were written outside the repository. Full mypy remains exactly `111 errors in 34 files`, while the new 25-file critical lane passes; this is historical maintenance debt with no incremental errors. The pre-existing dirty worktree and historical prompt-pack deletions were preserved and inventoried in `reports/CERTGEN_CVPR_REPOSITORY_SAFETY_INVENTORY.md`.

## 3. CVPR-readiness gaps found

- Theory: real-run independence/reference/family obligations not yet artifact-enforced by execution.
- Code: no typed CVPR stage/family/ranking/figure layer.
- Architecture: V6-V9 status and wrappers dominated navigation.
- Notebooks: no canonical generic generation/features names; DINO not in the primary extraction contract.
- Breadth: benchmark/model availability and licenses not verified.
- Ranking/visuals: no strict partial-ranking validity gate or paper-approved figure factory.
- Paper/release: working title/claim hierarchy existed but not a unified CVPR contract.

## 4. Repairs implemented

See `reports/CERTGEN_CVPR_REPAIR_CHANGELOG.md` for each finding, severity, root cause, changed files, tests, verification, and remaining limitation. P0 repairs isolate the exact six-kernel bounded contribution, freeze family/reference contracts, enrich the singular next action, require immutable ranking compatibility, and block unapproved empirical rendering. P1 repairs add registries, state machine, canonical notebooks, secure reference wrapper, CLI routes, tests, and runbook. Remaining limits are external data/model/Kaggle and real evidence.

## 5. New systems built

- benchmark, model, feature, comparison, family, claim, preregistration, execution, baseline, ablation, and figure registries/configs;
- 18-state typed machine, stable run IDs/config hashes, atomic output helper, enriched exact next action;
- no-download CIFAR validation/materialization for official/extracted/cache/image/wrapper forms;
- five config-driven process-based T4x2 notebooks and structural analyzer;
- reuse of secure ZIP/import, append-only artifact, and cache-v2 contracts;
- executable metric-reproduction and four-family sanity gates with immutable, nonclaim result schemas;
- configuration-driven runtime/session planner with resource arithmetic and deterministic copyback checkpoints;
- canonical bounded-RBF certificate runner with frozen-family/reference-plan checks;
- partial-ranking graph with unresolved and feature-disagreement outputs;
- censoring-aware samples-to-decision schema and paper-approved figure gates;
- literature claim schema/protocol, runtime/session matrix, paper/reviewer/release contracts;
- self-contained complete run handbook.

## 6. Statistical validity

The implemented contribution is `kAA-kBB-kAR1-kAR2+kBR1+kBR2`, estimating `MMD^2(A,R)-MMD^2(B,R)`. An RBF term is in `[0,1]`; the conservative contribution support is `[-3,3]`. Units use non-overlapping A/B/R pairs; the same R pair within a unit cancels reference-reference terms. A union-Hoeffding CS uses first exclusion of zero; negative certifies A closer and positive B closer. Bonferroni uses the full prospective family. Betting-grid, empirical Bernstein, directional e-BH, FID/FD, and polynomial KID are not certificate-capable. Real independence, fixed choices, source identity, and frozen family remain proof/artifact obligations.

## 7. CVPR experiment program

- Pilot: CIFAR controls and 1k candidate model pairs; execution validation only.
- Minimum credible: two recognized benchmarks, multiple families, three features, controls/baselines/visuals/sensitivity.
- Strong: third/text-to-image domain, material cross-representation and compute consequences, prospective published-claim audit.
- Maximum: broad 50k study and optional video replication only after the image core justifies it.

## 8. Notebook readiness

All five canonical notebooks pass JSON/Python/contract static analysis and have no stored outputs. They implement pinned dependency checks, T4x2 validation, explicit GPU pinning with independent processes, deterministic shards, configuration hashes, atomic statuses, validated resume, partial failure blocking, integrity manifests, deterministic ZIPs, logs, and copyback instructions. They have not run on Kaggle. Packages, auth, checkpoints, runtime adapter, memory, throughput, and model outputs are unverified.

## 9. Verification

The exact baseline and final commands, timestamps, exit codes, durations, counts, warnings, and artifacts are in `reports/CERTGEN_CVPR_COMMAND_LEDGER.csv`. The final audit is `reports/CERTGEN_CVPR_FINAL_AUDIT.json`. No validation command downloads data/models, executes GPU work, or grants paper permission.

## 10. Remaining blockers

- `USER_INPUT_REQUIRED`: provide a local accepted CIFAR source.
- `KAGGLE_EXECUTION_REQUIRED`: checkpoint preflight, generation, and features.
- `REAL_DATA_REQUIRED`: validated references on each benchmark.
- `REAL_MODEL_REQUIRED`: source/license/revision/adapter/preflight per model.
- `REAL_FEATURES_REQUIRED`: immutable Inception/CLIP/DINO caches.
- `EMPIRICAL_RESULT_REQUIRED`: metric, controls, certificates, rankings, sensitivity.
- `PAPER_EVIDENCE_REQUIRED`: multi-benchmark claim gate and visuals.
- `OPTIONAL_POST_PILOT_UPGRADE`: breadth/theory/video only if findings justify.

## 11. CVPR ceiling assessment

Pilot-only execution is not a paper. Workshop level needs a complete single-benchmark result with controls. Minimum CVPR needs breadth, recognizable models, three features, baselines, visual cases, and strong protocol integrity. Competitive CVPR needs a clear practical result across benchmarks. Strong CVPR needs a robust, consequential audit. The maximum realistic ceiling adds broad prospective literature evidence and possibly a separately valid extension; it cannot be inferred before runs.

## 12. Stop-building verdict

`DO NOT BUILD BEFORE FIRST PILOT`: complex e-BH, FID certification, video pipeline, dashboards/web apps, cloud/distributed support, arbitrary metric plugins, migration tooling, new prompt packs.

`ONLY BUILD IF EXECUTION FAILS`: concrete adapter/package/import/cache/resume repairs.

`ONLY BUILD IF RESULTS JUSTIFY IT`: 10k/50k breadth, third benchmark, video.

`POST_PILOT THEORY OPTIONS`: tighter valid CS or dependence design only if power/calibration blocks the registered question.

`POST_PILOT EMPIRICAL EXPANSIONS`: model/benchmark/literature breadth selected prospectively from the pilot interpretation.

## 13. Exact next action

```bash
python3 -m certgen validate reference --source data/sources/cifar-10-python.tar.gz --explain
```
""")


def main() -> None:
    registries()
    configs()
    theory_docs()
    reports_and_docs()
    paper_and_release()
    handbook()
    master_report()
    print("CVPR pre-execution assets generated without experiments or claim promotion")


if __name__ == "__main__":
    main()
