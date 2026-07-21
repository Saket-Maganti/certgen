"""Typed stage, run-identity, and evidence contracts for the CVPR workflow."""

from __future__ import annotations

import os
import re
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from certgen.core.hashing import stable_hash_json
from certgen.core.io import write_json


class EvidenceClass(str, Enum):
    PLANNING_ONLY = "planning_only"
    SYNTHETIC_VALIDATION_ONLY = "synthetic_validation_only"
    RUN_LOG_ONLY = "run_log_only"
    CACHE_ARTIFACT = "cache_artifact"
    SANITY_ARTIFACT = "sanity_artifact"
    PILOT_ARTIFACT = "pilot_only"
    PAPER_EVIDENCE = "paper_evidence"


class CVPRStage(str, Enum):
    REFERENCE_SOURCE_MISSING = "REFERENCE_SOURCE_MISSING"
    REFERENCE_SOURCE_VALID = "REFERENCE_SOURCE_VALID"
    REFERENCE_MATERIALIZED = "REFERENCE_MATERIALIZED"
    CHECKPOINT_PREFLIGHT_REQUIRED = "CHECKPOINT_PREFLIGHT_REQUIRED"
    CHECKPOINT_PREFLIGHT_IMPORTED = "CHECKPOINT_PREFLIGHT_IMPORTED"
    GENERATION_INPUT_READY = "GENERATION_INPUT_READY"
    GENERATION_OUTPUT_REQUIRED = "GENERATION_OUTPUT_REQUIRED"
    GENERATION_IMPORTED = "GENERATION_IMPORTED"
    FEATURE_INPUT_READY = "FEATURE_INPUT_READY"
    FEATURE_OUTPUT_REQUIRED = "FEATURE_OUTPUT_REQUIRED"
    FEATURES_IMPORTED = "FEATURES_IMPORTED"
    CACHE_VALIDATION_REQUIRED = "CACHE_VALIDATION_REQUIRED"
    METRIC_REPRODUCTION_REQUIRED = "METRIC_REPRODUCTION_REQUIRED"
    SANITY_GATES_REQUIRED = "SANITY_GATES_REQUIRED"
    FIRST_PILOT_READY = "FIRST_PILOT_READY"
    FIRST_PILOT_COMPLETE_NONCLAIM = "FIRST_PILOT_COMPLETE_NONCLAIM"
    MULTIBENCHMARK_EXPANSION_READY = "MULTIBENCHMARK_EXPANSION_READY"
    CVPR_EVIDENCE_GATES_PENDING = "CVPR_EVIDENCE_GATES_PENDING"


@dataclass(frozen=True)
class StageTransition:
    stage: CVPRStage
    required_inputs: tuple[str, ...]
    validator: str
    output_artifacts: tuple[str, ...]
    failure_status: str
    next_action: str
    evidence_class: EvidenceClass
    claim_permission: bool = False


STAGE_TRANSITIONS: tuple[StageTransition, ...] = (
    StageTransition(CVPRStage.REFERENCE_SOURCE_MISSING, ("user-provided CIFAR-10 source",), "certgen validate reference", ("data/results/cvpr_reference_validation.json",), "BLOCKED_USER_MUST_PROVIDE_CIFAR_REFERENCE", "validate the user-provided reference source", EvidenceClass.PLANNING_ONLY),
    StageTransition(CVPRStage.REFERENCE_SOURCE_VALID, ("validated reference source",), "certgen materialize reference", ("registry/manifests/cvpr/cifar10_reference.jsonl", "data/results/cvpr_reference_materialization.json"), "BLOCKED_REFERENCE_MATERIALIZATION", "materialize the immutable reference manifest", EvidenceClass.CACHE_ARTIFACT),
    StageTransition(CVPRStage.REFERENCE_MATERIALIZED, ("reference manifest", "model registry"), "certgen package preflight", ("data/kaggle_inputs/certgen_cvpr_checkpoint_preflight_input.zip",), "BLOCKED_PREFLIGHT_PACKAGE", "package checkpoint preflight", EvidenceClass.PLANNING_ONLY),
    StageTransition(CVPRStage.CHECKPOINT_PREFLIGHT_REQUIRED, ("preflight input ZIP",), "certgen import preflight", ("data/imported/<preflight-run>",), "BLOCKED_CHECKPOINT_PREFLIGHT", "run and import checkpoint preflight", EvidenceClass.RUN_LOG_ONLY),
    StageTransition(CVPRStage.CHECKPOINT_PREFLIGHT_IMPORTED, ("validated preflight import",), "certgen package generation", ("data/kaggle_inputs/certgen_cvpr_generation_1k_input.zip",), "BLOCKED_GENERATION_PACKAGE", "package 1k generation", EvidenceClass.PLANNING_ONLY),
    StageTransition(CVPRStage.GENERATION_INPUT_READY, ("generation package",), "Kaggle generation notebook", ("certgen_cvpr_generation_<benchmark>_<scale>_<run_id>.zip",), "BLOCKED_GENERATION_RUN", "run generation on Kaggle T4x2", EvidenceClass.RUN_LOG_ONLY),
    StageTransition(CVPRStage.GENERATION_OUTPUT_REQUIRED, ("copied-back generation ZIP",), "certgen import generation", ("data/imported/<generation-run>",), "BLOCKED_GENERATION_IMPORT", "securely import generated samples", EvidenceClass.PILOT_ARTIFACT),
    StageTransition(CVPRStage.GENERATION_IMPORTED, ("validated generation manifest", "reference manifest"), "certgen package features", ("data/kaggle_inputs/certgen_cvpr_features_1k_input.zip",), "BLOCKED_FEATURE_PACKAGE", "package feature extraction", EvidenceClass.PLANNING_ONLY),
    StageTransition(CVPRStage.FEATURE_INPUT_READY, ("feature input package",), "Kaggle feature notebook", ("certgen_cvpr_features_<benchmark>_<scale>_<run_id>.zip",), "BLOCKED_FEATURE_RUN", "run feature extraction on Kaggle T4x2", EvidenceClass.RUN_LOG_ONLY),
    StageTransition(CVPRStage.FEATURE_OUTPUT_REQUIRED, ("copied-back feature ZIP",), "certgen import features", ("data/imported/<feature-run>",), "BLOCKED_FEATURE_IMPORT", "securely import feature caches", EvidenceClass.CACHE_ARTIFACT),
    StageTransition(CVPRStage.FEATURES_IMPORTED, ("imported feature caches",), "certgen validate caches", ("data/results/cvpr_cache_validation.json",), "BLOCKED_CACHE_VALIDATION", "validate cache identities and locks", EvidenceClass.CACHE_ARTIFACT),
    StageTransition(CVPRStage.CACHE_VALIDATION_REQUIRED, ("validated cache-v2 artifacts",), "certgen sanity metric-reproduction", ("data/results/cvpr_metric_reproduction.json",), "BLOCKED_METRIC_REPRODUCTION", "reproduce or cross-check metrics", EvidenceClass.SANITY_ARTIFACT),
    StageTransition(CVPRStage.METRIC_REPRODUCTION_REQUIRED, ("metric reproduction pass",), "certgen sanity controls", ("data/results/cvpr_sanity_gates.json",), "BLOCKED_SANITY_GATES", "run null and obvious-gap gates", EvidenceClass.SANITY_ARTIFACT),
    StageTransition(CVPRStage.SANITY_GATES_REQUIRED, ("passed sanity gates", "frozen family registry"), "certgen certify", ("data/results/cvpr_certificates/<run_id>",), "BLOCKED_CERTIFICATE_ASSUMPTION", "run first nonclaim certificate pilot", EvidenceClass.PILOT_ARTIFACT),
    StageTransition(CVPRStage.FIRST_PILOT_READY, ("pilot certificates",), "certgen rank", ("data/results/cvpr_rankings/<run_id>",), "BLOCKED_RANKING_VALIDITY", "build the pilot partial ranking", EvidenceClass.PILOT_ARTIFACT),
    StageTransition(CVPRStage.FIRST_PILOT_COMPLETE_NONCLAIM, ("pilot interpretation",), "explicit scale-up gate", ("data/results/cvpr_scale_up_decision.json",), "STOP_INTERPRET_FIRST_PILOT", "stop and interpret before scaling", EvidenceClass.PILOT_ARTIFACT),
    StageTransition(CVPRStage.MULTIBENCHMARK_EXPANSION_READY, ("approved scale-up decision",), "multi-benchmark execution matrix", ("data/results/cvpr_multibench_summary.json",), "BLOCKED_MULTIBENCH_INPUTS", "execute only approved expansion lanes", EvidenceClass.PILOT_ARTIFACT),
    StageTransition(CVPRStage.CVPR_EVIDENCE_GATES_PENDING, ("complete immutable lineage",), "paper evidence firewall", ("data/results/cvpr_paper_gate.json",), "BLOCKED_PAPER_EVIDENCE", "run paper promotion gate", EvidenceClass.PAPER_EVIDENCE),
)


def transition_registry() -> list[dict[str, Any]]:
    return [asdict(item) for item in STAGE_TRANSITIONS]


def configuration_hash(config: Mapping[str, Any]) -> str:
    """Hash a prospective configuration after excluding self-referential fields."""

    payload = {str(key): value for key, value in config.items() if key not in {"configuration_hash", "created_at", "preregistered_at"}}
    return stable_hash_json(payload)


_RUN_COMPONENT = re.compile(r"[^a-z0-9._-]+")


def _slug(value: str) -> str:
    result = _RUN_COMPONENT.sub("-", value.strip().lower()).strip("-")
    if not result:
        raise ValueError("run-id components must be non-empty")
    return result


def build_run_id(
    *, benchmark: str, stage: str, scale: str, feature_space: str, config: Mapping[str, Any], timestamp: str | None = None
) -> str:
    stamp = timestamp or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return "__".join((_slug(benchmark), _slug(stage), _slug(scale), _slug(feature_space), configuration_hash(config)[:12], _slug(stamp)))


def atomic_write_json(payload: Mapping[str, Any], path: str | Path, *, overwrite_identical: bool = True) -> None:
    """Write JSON via atomic rename and refuse a changed existing artifact."""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        import json

        current = json.loads(destination.read_text(encoding="utf-8"))
        if overwrite_identical and stable_hash_json(current) == stable_hash_json(payload):
            return
        raise FileExistsError(f"refusing to overwrite non-identical artifact: {destination}")
    fd, temporary_name = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
    os.close(fd)
    temporary = Path(temporary_name)
    try:
        write_json(dict(payload), temporary)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
