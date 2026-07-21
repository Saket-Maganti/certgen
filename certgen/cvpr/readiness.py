"""Live-artifact run readiness with separate capability and execution state."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from certgen.cvpr.profiles import load_profile
from certgen.cvpr.registries import validate_preregistration
from certgen.pipeline.v9_next_action import determine_next_action


def _passed(path: str | Path) -> bool:
    candidate = Path(path)
    if not candidate.is_file():
        return False
    try:
        payload = json.loads(candidate.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return bool(
        payload.get("passed") is True
        or payload.get("status_code", "").endswith(("PASS", "COMPLETE"))
    )


def _exists(path: str | Path) -> bool:
    return Path(path).is_file()


def readiness_report() -> dict[str, Any]:
    action = determine_next_action()
    replacement_path = Path("reports/CERTGEN_REPLACEMENT_AUDIT.json")
    try:
        replacement = json.loads(replacement_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        replacement = {}
    reference_ready = _exists("registry/manifests/cvpr/cifar10_reference.jsonl")
    reference_candidate = next(
        (
            path
            for path in (
                Path("data/sources/cifar-10-python.tar.gz"),
                Path("cifar-10-python.tar.gz"),
            )
            if path.is_file()
        ),
        None,
    )
    try:
        profile = load_profile("cifar_integrity_minimal")
    except (OSError, KeyError, ValueError):
        profile = None
    study_path = Path("artifacts/cvpr/study/cifar_integrity_minimal.yaml")
    study_ready = study_path.is_file() and validate_preregistration(
        study_path, require_frozen=True
    )["passed"]
    preflight_imported = _passed("data/results/cvpr/preflight_import_status.json")
    generation_package = _exists("artifacts/cvpr/generation/generation_input_manifest.json")
    feature_package = _exists("artifacts/cvpr/features/feature_input_manifest.json")
    feature_config = Path("artifacts/cvpr/features/feature_config.yaml")
    components = {
        "reference": (
            "READY"
            if reference_ready
            else (
                "CANDIDATE_ARCHIVE_PRESENT_VALIDATION_REQUIRED"
                if reference_candidate is not None
                else "WAITING_FOR_OFFICIAL_CIFAR_ARCHIVE"
            )
        ),
        "selected_profile": "READY_FROZEN_PROFILE" if profile else "BLOCKED_PROFILE_INVALID",
        "study_freeze": "READY" if study_ready else "COMMAND_READY_NOT_YET_FROZEN",
        "model_preflight_package": "READY" if _exists("artifacts/cvpr/preflight/preflight_input_manifest.json") else "BUILDER_VERIFIED_NOT_PREPARED",
        "extractor_preflight_package": "READY" if _exists("artifacts/cvpr/preflight/preflight_input_manifest.json") else "BUILDER_VERIFIED_NOT_PREPARED",
        "model_adapter_readiness": "SELECTED_DDPM_ADAPTERS_IMPLEMENTED_REAL_PREFLIGHT_REQUIRED",
        "extractor_adapter_readiness": "INCEPTION_AND_CLIP_IMPLEMENTED_REAL_PREFLIGHT_REQUIRED",
        "generation_package": "READY" if generation_package else ("REAL_PREFLIGHT_IMPORT_REQUIRED" if not preflight_imported else "READY_TO_PREPARE"),
        "feature_package": "READY" if feature_package else "GENERATION_IMPORT_REQUIRED",
        "image_path_resolvability": "EMBEDDED_IMAGE_CONTRACT_LOCAL_VALIDATED" if feature_package and feature_config.is_file() else "BUILDER_AND_FIXTURE_VALIDATED",
        "output_schema_compatibility": "LOCAL_CONTRACT_VERIFIED",
        "feature_merge": "REAL_FEATURE_IMPORT_REQUIRED" if not any(Path("data/features/cvpr").glob("*/status.json")) else "READY",
        "cache_v2": "MERGE_VALIDATOR_VERIFIED_REAL_CACHE_REQUIRED",
        "family_freeze": "READY" if _exists("artifacts/cvpr/family/family.json") else "COMMAND_READY_AFTER_SANITY_GATES",
        "exact_next_action": "VALIDATE_REFERENCE" if not reference_ready else action.get("action"),
    }
    maximum_ceiling_components = {
        "replacement_status": "VERIFIED_FIXED_ZIP_REPLACEMENT" if replacement.get("replacement_verified") is True else "REPLACEMENT_AUDIT_REQUIRED",
        "reference": components["reference"],
        "profile": components["selected_profile"],
        "study_freeze": components["study_freeze"],
        "reference_draw": "REAL_REFERENCE_AND_FROZEN_STUDY_REQUIRED",
        "preflight": "REAL_KAGGLE_PREFLIGHT_REQUIRED",
        "generation": "REAL_PREFLIGHT_IMPORT_REQUIRED",
        "controls": "REAL_REFERENCE_DRAW_REQUIRED",
        "features": "REAL_GENERATION_IMPORT_REQUIRED",
        "cache_v2": components["cache_v2"],
        "metric_gates": "REAL_VALIDATED_CACHE_REQUIRED",
        "sanity_gates": "REAL_VALIDATED_CACHE_REQUIRED",
        "family": "READY" if _exists("artifacts/cvpr/family/family.json") else "REAL_GATES_REQUIRED",
        "certificate_inputs": "REAL_FAMILY_AND_CACHES_REQUIRED",
        "family_certificates": "REAL_GATE_PASS_AND_COMPLETE_INPUT_COVERAGE_REQUIRED",
        "ranking": "COMPLETE_FROZEN_FAMILY_CERTIFICATE_COVERAGE_REQUIRED",
        "cross_feature_analysis": "COMPLETE_REGISTERED_CERTIFICATE_LANES_REQUIRED",
        "pilot_decision": "REAL_1K_PILOT_REQUIRED",
        "provenance_integrity": "LOCAL_CONTRACT_VERIFIED_REAL_ARTIFACT_DAG_PENDING",
        "public_release_safety": "LOCAL_EXCLUSION_POLICY_VERIFIED_REAL_RESULTS_EXCLUDED",
        "exact_next_action": components["exact_next_action"],
    }
    if not reference_ready:
        top_level = (
            "RUN_READY_WAITING_FOR_REFERENCE_VALIDATION"
            if reference_candidate is not None
            else "RUN_READY_WAITING_FOR_REFERENCE"
        )
    elif action.get("action") == "RUN_KAGGLE_ENVIRONMENT_DIAGNOSTIC":
        top_level = "WAITING_FOR_KAGGLE_DIAGNOSTIC"
    elif action.get("action") == "RUN_KAGGLE_CHECKPOINT_PREFLIGHT":
        top_level = "WAITING_FOR_KAGGLE_PREFLIGHT"
    else:
        top_level = "READY_TO_PREPARE_PREFLIGHT"
    exact_command = str(action["exact_command"])
    return {
        "top_level_status": top_level,
        "components": components,
        "maximum_ceiling_components": maximum_ceiling_components,
        "selected_profile": profile,
        "next_action": action,
        "exact_next_command": exact_command,
        "known_local_defect": None,
        "evidence_status": "no_real_execution_evidence",
        "blocked_only_by_real_inputs_and_real_execution": True,
        "claim_allowed": False,
    }
