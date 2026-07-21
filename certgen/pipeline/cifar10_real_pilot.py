"""R1 CIFAR-10 real-pilot readiness checks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from certgen.core.io import read_json, write_json
from certgen.features.cache_validate import validate_v3_feature_cache
from certgen.generation.generate_cifar10_diffusers import checkpoint_adapter_statuses
from certgen.registry.provenance import validate_provenance_ledger


REQUIRED_LOCK_FIELDS = {
    "lock_id",
    "image_size",
    "resize_policy",
    "interpolation",
    "normalization",
    "color_mode",
    "feature_extractor",
    "sample_order_policy",
    "reference_set_policy",
    "hash",
}

REQUIRED_MANIFEST_FIELDS = {"sample_id", "role", "path"}
LEGACY_REQUIRED_ROLES = {"reference", "model_a", "model_b"}
R1B_REQUIRED_ROLES = {"reference", "google_ddpm", "frank_ddpm_ema", "frank_cfm"}

R1_CANDIDATES = [
    {
        "candidate_id": "cifar10_null_split_reference_vs_reference",
        "role": "null_calibration_pair",
        "purpose": "same-source CIFAR-10 split-vs-split calibration",
        "status": "selected_blocked_missing_local_reference_samples",
    },
    {
        "candidate_id": "cifar10_reference_vs_corruption_sanity",
        "role": "obvious_gap_sanity_pair",
        "purpose": "reference samples versus clearly corrupted/noise replacement samples for software sanity only",
        "status": "selected_blocked_missing_local_reference_samples",
    },
    {
        "candidate_id": "google_ddpm_vs_frank_cfm",
        "role": "medium_gap_pair",
        "purpose": "Apache-2.0 DDPM checkpoint versus Apache-2.0 CIFAR flow-matching checkpoint after generated samples exist",
        "status": "selected_blocked_missing_generated_samples",
    },
    {
        "candidate_id": "google_ddpm_vs_frank_ddpm_ema",
        "role": "close_gap_pair",
        "purpose": "two Apache-2.0 DDPM-style CIFAR-10 checkpoints after generated samples exist",
        "status": "selected_blocked_missing_generated_samples",
    },
    {
        "candidate_id": "google_ddpm_preprocessing_sensitivity",
        "role": "preprocessing_sensitivity_pair",
        "purpose": "same generated samples under the primary preprocessing lock and a later explicitly locked variant",
        "status": "selected_blocked_until_primary_samples_exist",
    },
]


SELECTED_CANDIDATE_MODEL_PAIRS = [
    {
        "pair_id": "cifar10_null_split_reference_vs_reference",
        "role": "null_calibration_pair",
        "model_a": "cifar10_test_split_a",
        "model_b": "cifar10_test_split_b",
        "status": "blocked_missing_local_reference_samples",
    },
    {
        "pair_id": "cifar10_reference_vs_corruption_sanity",
        "role": "obvious_gap_sanity_pair",
        "model_a": "cifar10_reference_samples",
        "model_b": "deterministic_corruption_of_same_reference_samples",
        "status": "blocked_missing_local_reference_samples",
    },
    {
        "pair_id": "google_ddpm_vs_frank_cfm",
        "role": "medium_gap_pair",
        "model_a": "google/ddpm-cifar10-32",
        "model_b": "FrankCCCCC/cfm-cifar10-32",
        "status": "blocked_missing_generated_samples",
    },
    {
        "pair_id": "google_ddpm_vs_frank_ddpm_ema",
        "role": "close_gap_pair",
        "model_a": "google/ddpm-cifar10-32",
        "model_b": "FrankCCCCC/ddpm_ema_cifar10",
        "status": "blocked_missing_generated_samples",
    },
    {
        "pair_id": "google_ddpm_preprocessing_sensitivity",
        "role": "preprocessing_sensitivity_pair",
        "model_a": "google/ddpm-cifar10-32_primary_preprocessing",
        "model_b": "google/ddpm-cifar10-32_alternate_locked_preprocessing",
        "status": "blocked_until_primary_samples_exist",
    },
]


REPLACEMENT_CANDIDATES = [
    {
        "candidate_id": "minimal_diffusion_cifar10_released_50k",
        "status": "blocked_until_asset_license_and_google_drive_artifact_are_verified",
        "reason": "README advertises released CIFAR-10 synthetic images but the downloadable artifact was not locally verified in R1.",
    },
    {
        "candidate_id": "openai_improved_diffusion_cifar10",
        "status": "blocked_until_checkpoint_or_released_samples_are_verified",
        "reason": "MIT code is public but R1 did not verify a concrete CIFAR-10 generated-sample artifact.",
    },
    {
        "candidate_id": "nvlabs_edm_cifar10",
        "status": "blocked_license_noncommercial",
        "reason": "Repository license is CC BY-NC-SA 4.0 and is not selected for the public/free R1 source lock.",
    },
]


CPU_AFTER_CACHE_COMMANDS = [
    "commands/r0_cpu/01_validate_provenance.sh",
    "commands/r0_cpu/02_validate_feature_caches.sh",
    "commands/r0_cpu/03_reproduce_metric_from_features.sh",
    "commands/r0_cpu/04_run_clean_core_certificates_cpu.sh",
    "commands/r0_cpu/06_generate_pilot_report_cpu.sh",
]


KAGGLE_INCEPTION_FEATURE_EXTRACTION_COMMAND = (
    "CUDA_VISIBLE_DEVICES=0 python -m certgen.features.extract "
    "--input-manifest $CERTGEN_INPUT_ROOT/cifar10_r1_feature_extraction_samples.jsonl "
    "--provenance-ledger $CERTGEN_INPUT_ROOT/cifar10_r1_ledger.csv "
    "--preprocessing-lock $CERTGEN_INPUT_ROOT/cifar10_inception_bilinear_299.json "
    "--extractor inception_v3_pool3 --out-dir /kaggle/working/features/inception "
    "--device cuda --batch-size 64 --shard-id 0 --num-shards 2 --resume --execute & "
    "CUDA_VISIBLE_DEVICES=1 python -m certgen.features.extract "
    "--input-manifest $CERTGEN_INPUT_ROOT/cifar10_r1_feature_extraction_samples.jsonl "
    "--provenance-ledger $CERTGEN_INPUT_ROOT/cifar10_r1_ledger.csv "
    "--preprocessing-lock $CERTGEN_INPUT_ROOT/cifar10_inception_bilinear_299.json "
    "--extractor inception_v3_pool3 --out-dir /kaggle/working/features/inception "
    "--device cuda --batch-size 64 --shard-id 1 --num-shards 2 --resume --execute & wait"
)

KAGGLE_CLIP_FEATURE_EXTRACTION_COMMAND = (
    "CUDA_VISIBLE_DEVICES=0 python -m certgen.features.extract "
    "--input-manifest $CERTGEN_INPUT_ROOT/cifar10_r1_feature_extraction_samples.jsonl "
    "--provenance-ledger $CERTGEN_INPUT_ROOT/cifar10_r1_ledger.csv "
    "--preprocessing-lock $CERTGEN_INPUT_ROOT/cifar10_inception_bilinear_299.json "
    "--extractor clip_vit --out-dir /kaggle/working/features/clip "
    "--device cuda --batch-size 64 --shard-id 0 --num-shards 2 --resume --execute & "
    "CUDA_VISIBLE_DEVICES=1 python -m certgen.features.extract "
    "--input-manifest $CERTGEN_INPUT_ROOT/cifar10_r1_feature_extraction_samples.jsonl "
    "--provenance-ledger $CERTGEN_INPUT_ROOT/cifar10_r1_ledger.csv "
    "--preprocessing-lock $CERTGEN_INPUT_ROOT/cifar10_inception_bilinear_299.json "
    "--extractor clip_vit --out-dir /kaggle/working/features/clip "
    "--device cuda --batch-size 64 --shard-id 1 --num-shards 2 --resume --execute & wait"
)

KAGGLE_FEATURE_EXTRACTION_COMMAND = KAGGLE_INCEPTION_FEATURE_EXTRACTION_COMMAND + " && " + KAGGLE_CLIP_FEATURE_EXTRACTION_COMMAND


def _materialization_state(manifest_path: str | Path | None, *, require_local_files: bool = True) -> dict[str, Any]:
    state: dict[str, Any] = {
        "reference_rows": 0,
        "generated_rows": 0,
        "generated_counts_by_role": {},
        "missing_reference_paths": [],
        "missing_generated_paths": [],
        "generation_blockers": [],
        "manifest_invalid": [],
        "reference_materialized": False,
        "generated_samples_materialized": False,
    }
    if not manifest_path or not Path(manifest_path).exists():
        state["generation_blockers"].append("sample manifest missing")
        return state
    for line in Path(manifest_path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        role = str(row.get("role", ""))
        source_type = str(row.get("source_type", ""))
        path_value = row.get("path") or row.get("image_path")
        missing = bool(path_value) and require_local_files and not Path(str(path_value)).exists()
        if role == "reference" or source_type == "reference_dataset":
            state["reference_rows"] += 1
            if missing:
                state["missing_reference_paths"].append(str(path_value))
        if role in {"model_a", "model_b"} or "checkpoint" in source_type or row.get("checkpoint_id"):
            state["generated_rows"] += 1
            role_key = role if role else str(row.get("checkpoint_id") or row.get("model_id") or "unknown")
            state["generated_counts_by_role"][role_key] = state["generated_counts_by_role"].get(role_key, 0) + 1
            if missing:
                state["missing_generated_paths"].append(str(path_value))
            status_text = " ".join(str(row.get(key, "")) for key in ["source_status", "generation_status", "adapter_status"])
            if "blocked" in status_text or "needed" in status_text or "not_run" in status_text:
                state["generation_blockers"].append(status_text.strip())
            if row.get("claim_allowed") is True:
                state["manifest_invalid"].append(f"{row.get('sample_id', '<unknown>')}: claim_allowed=true")
            for dim in ["width", "height", "channels"]:
                if dim in row and int(row.get(dim, 0)) <= 0:
                    state["manifest_invalid"].append(f"{row.get('sample_id', '<unknown>')}: invalid {dim}")
    state["reference_materialized"] = state["reference_rows"] > 0 and not state["missing_reference_paths"]
    state["generated_samples_materialized"] = (
        state["generated_rows"] > 0
        and not state["missing_generated_paths"]
        and not state["generation_blockers"]
        and not state["manifest_invalid"]
    )
    return state


def _status_code(
    *,
    blockers: list[str],
    ready: bool,
    materialization: dict[str, Any],
    caches_passed: bool,
    metric_reproduction_passed: bool,
    adapter_statuses: dict[str, dict[str, Any]],
) -> str:
    if ready:
        return "READY_FOR_CPU_CERTIFICATE_PILOT"
    unsupported = [
        checkpoint
        for checkpoint, status in adapter_statuses.items()
        if str(status.get("adapter_status", "")).startswith("blocked")
    ]
    if unsupported:
        return "BLOCKED_GENERATION_ADAPTER_UNSUPPORTED"
    if materialization.get("missing_reference_paths") or materialization.get("reference_rows") == 0:
        return "BLOCKED_MISSING_REFERENCE_SAMPLES"
    if materialization.get("manifest_invalid"):
        return "BLOCKED_GENERATION_MANIFEST_INVALID"
    if materialization.get("missing_generated_paths") or materialization.get("generation_blockers") or materialization.get("generated_rows") == 0:
        return "BLOCKED_GENERATION_NOT_RUN"
    if materialization.get("reference_materialized") and materialization.get("generated_samples_materialized") and not caches_passed:
        return "READY_FOR_KAGGLE_FEATURE_EXTRACTION"
    if not caches_passed:
        return "BLOCKED_FEATURE_EXTRACTION_NOT_RUN"
    if not metric_reproduction_passed:
        return "BLOCKED_METRIC_REPRODUCTION"
    lowered = "\n".join(blockers).lower()
    if (
        "provenance ledger missing" in lowered
        or "sample manifest missing" in lowered
        or "manifest missing role" in lowered
        or "local sample path missing" in lowered
    ):
        return "BLOCKED_MISSING_REFERENCE_SAMPLES"
    if "license" in lowered or "provenance:" in lowered:
        return "BLOCKED_PROVENANCE_OR_LICENSE"
    if "feature cache missing" in lowered:
        return "BLOCKED_FEATURE_EXTRACTION_NOT_RUN"
    if "metric reproduction" in lowered:
        return "BLOCKED_METRIC_REPRODUCTION"
    return "BLOCKED_MISSING_REFERENCE_SAMPLES"


def validate_sample_manifest(path: str | Path | None, *, require_local_files: bool = True) -> dict[str, Any]:
    if not path:
        return {"passed": False, "errors": ["sample manifest path not provided"], "warnings": [], "rows": 0}
    manifest_path = Path(path)
    if not manifest_path.exists():
        return {"passed": False, "errors": [f"sample manifest missing: {manifest_path}"], "warnings": [], "rows": 0}
    errors: list[str] = []
    warnings: list[str] = []
    rows = 0
    roles: set[str] = set()
    for line_no, line in enumerate(manifest_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        rows += 1
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"line {line_no}: invalid json: {exc}")
            continue
        missing = sorted(REQUIRED_MANIFEST_FIELDS - set(row))
        if missing:
            errors.append(f"line {line_no}: missing fields {missing}")
        role = str(row.get("role", ""))
        if role:
            roles.add(role)
        sample_path = row.get("path")
        if require_local_files and sample_path and not Path(str(sample_path)).exists():
            errors.append(f"line {line_no}: local sample path missing: {sample_path}")
        if not row.get("sha256"):
            warnings.append(f"line {line_no}: sha256 absent")
    if not (LEGACY_REQUIRED_ROLES <= roles or R1B_REQUIRED_ROLES <= roles):
        missing_legacy = sorted(LEGACY_REQUIRED_ROLES - roles)
        missing_r1b = sorted(R1B_REQUIRED_ROLES - roles)
        errors.append(f"manifest missing required role set: legacy_missing={missing_legacy}; r1b_missing={missing_r1b}")
    return {"passed": not errors, "errors": errors, "warnings": warnings, "rows": rows}


def validate_preprocessing_lock_file(path: str | Path | None) -> dict[str, Any]:
    if not path:
        return {"passed": False, "errors": ["preprocessing lock path not provided"], "warnings": []}
    lock_path = Path(path)
    if not lock_path.exists():
        return {"passed": False, "errors": [f"preprocessing lock missing: {lock_path}"], "warnings": []}
    lock = read_json(lock_path)
    errors: list[str] = []
    warnings: list[str] = []
    for field in sorted(REQUIRED_LOCK_FIELDS):
        value = lock.get(field)
        if value in {None, "", "default", "unknown", "TBD"}:
            errors.append(f"preprocessing lock field missing or vague: {field}")
    if str(lock.get("hash", "")).startswith("template_"):
        errors.append("preprocessing lock hash is still a template value")
    if lock.get("feature_extractor") != "inception_v3_pool3":
        warnings.append("primary CIFAR-10 lock is not Inception; CLIP path requires a separate lock or explicit extension")
    return {"passed": not errors, "errors": errors, "warnings": warnings, "lock_id": lock.get("lock_id")}


def _validate_feature_cache_pair(feature_cache_dir: str | Path | None) -> dict[str, Any]:
    if not feature_cache_dir:
        return {"passed": False, "errors": ["feature cache directory not provided"], "warnings": []}
    root = Path(feature_cache_dir)
    expected = [
        ("reference_inception", "reference_inception.npz", "reference_inception.sidecar.json", "mmd_rbf"),
        ("model_a_inception", "model_a_inception.npz", "model_a_inception.sidecar.json", "mmd_rbf"),
        ("model_b_inception", "model_b_inception.npz", "model_b_inception.sidecar.json", "mmd_rbf"),
        ("reference_clip", "reference_clip.npz", "reference_clip.sidecar.json", "cmmd_clip_mmd"),
        ("model_a_clip", "model_a_clip.npz", "model_a_clip.sidecar.json", "cmmd_clip_mmd"),
        ("model_b_clip", "model_b_clip.npz", "model_b_clip.sidecar.json", "cmmd_clip_mmd"),
    ]
    errors: list[str] = []
    warnings: list[str] = []
    checked = []
    for cache_id, npz_name, sidecar_name, metric in expected:
        npz = root / npz_name
        sidecar = root / sidecar_name
        if not npz.exists() or not sidecar.exists():
            errors.append(f"feature cache missing for {cache_id}: {npz_name} and/or {sidecar_name}")
            continue
        result = validate_v3_feature_cache(features_path=npz, sidecar_path=sidecar, metric=metric, strict_hash=False)
        checked.append(cache_id)
        errors.extend(f"{cache_id}: {error}" for error in result.errors)
        warnings.extend(f"{cache_id}: {warning}" for warning in result.warnings)
    return {"passed": not errors, "errors": errors, "warnings": warnings, "checked": checked}


def run_cifar10_r1_readiness(
    *,
    provenance_ledger: str | Path | None,
    sample_manifest: str | Path | None,
    preprocessing_lock: str | Path | None,
    feature_cache_dir: str | Path | None,
    metric_reproduction_audit: str | Path | None,
    out_json: str | Path,
    report: str | Path,
    require_local_files: bool = True,
) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []

    if provenance_ledger and Path(provenance_ledger).exists():
        provenance = validate_provenance_ledger(provenance_ledger, allow_missing_local=not require_local_files, require_real_pilot=True)
        blockers.extend(f"provenance: {error}" for error in provenance["errors"])
        warnings.extend(f"provenance: {warning}" for warning in provenance["warnings"])
    else:
        provenance = {"passed": False, "errors": ["provenance ledger missing"], "warnings": [], "rows": 0}
        blockers.append(f"provenance ledger missing: {provenance_ledger or '<not provided>'}")

    manifest = validate_sample_manifest(sample_manifest, require_local_files=require_local_files)
    blockers.extend(f"manifest: {error}" for error in manifest["errors"])
    warnings.extend(f"manifest: {warning}" for warning in manifest["warnings"])

    lock = validate_preprocessing_lock_file(preprocessing_lock)
    blockers.extend(f"preprocessing: {error}" for error in lock["errors"])
    warnings.extend(f"preprocessing: {warning}" for warning in lock["warnings"])

    caches = _validate_feature_cache_pair(feature_cache_dir)
    blockers.extend(f"features: {error}" for error in caches["errors"])
    warnings.extend(f"features: {warning}" for warning in caches["warnings"])

    if metric_reproduction_audit and Path(metric_reproduction_audit).exists():
        reproduction = read_json(metric_reproduction_audit)
        if reproduction.get("within_tolerance") is not True:
            blockers.append("metric reproduction audit exists but within_tolerance is not true")
        if reproduction.get("claim_allowed") is True:
            blockers.append("metric reproduction audit has claim_allowed=true")
    else:
        reproduction = {"within_tolerance": False}
        blockers.append(f"metric reproduction audit missing: {metric_reproduction_audit or '<not provided>'}")

    materialization = _materialization_state(sample_manifest, require_local_files=require_local_files)
    metric_reproduction_passed = bool(reproduction.get("within_tolerance") is True)
    adapter_statuses = checkpoint_adapter_statuses()
    source_package_ready_for_kaggle = (
        provenance.get("passed")
        and manifest.get("passed")
        and lock.get("passed")
        and materialization.get("reference_materialized")
        and materialization.get("generated_samples_materialized")
    )
    ready = not blockers
    status_code = _status_code(
        blockers=blockers,
        ready=ready,
        materialization=materialization,
        caches_passed=bool(caches.get("passed")),
        metric_reproduction_passed=metric_reproduction_passed,
        adapter_statuses=adapter_statuses,
    )
    exact_next_command = (
        "python3 -m certgen.cli.run_cifar10_real_pilot "
        "--provenance-ledger registry/provenance/cifar10_r1_ledger.csv "
        "--sample-manifest registry/manifests/cifar10_r1_samples.jsonl "
        "--preprocessing-lock configs/preprocessing_locks/cifar10_inception_bilinear_299.json "
        "--feature-cache-dir data/features/cifar10_r1 "
        "--metric-reproduction-audit data/results/cifar10_r1_metric_reproduction.json "
        "--out-json data/results/r1_cifar10_status.json "
        "--report docs/R1_CIFAR10_REAL_PILOT_READINESS.md"
    )
    payload = {
        "status": "ready" if ready else "blocked",
        "status_code": status_code,
        "ready_for_r1": ready,
        "claim_allowed": False,
        "promote_to_paper_evidence": False,
        "blockers": blockers,
        "warnings": warnings,
        "candidates": R1_CANDIDATES,
        "replacement_candidates": REPLACEMENT_CANDIDATES,
        "selected_benchmark": "cifar10",
        "selected_candidate_model_pairs": SELECTED_CANDIDATE_MODEL_PAIRS,
        "source_status": "verified" if provenance.get("passed") and manifest.get("passed") else "not_verified",
        "license_status": "not_verified"
        if any("license unknown" in warning.lower() for warning in warnings)
        else ("verified_or_allowed" if provenance.get("passed") else "not_verified"),
        "sample_availability": "available" if manifest.get("passed") else "not_verified",
        "feature_cache_status": "validated" if caches.get("passed") else "missing_or_unvalidated",
        "metric_reproduction_status": reproduction.get("reproduction_status", "missing_or_not_within_tolerance"),
        "kaggle_feature_extraction_needed": not caches.get("passed"),
        "kaggle_feature_extraction_ready": bool(source_package_ready_for_kaggle and not caches.get("passed")),
        "estimated_kaggle_runtime_if_needed": "planning estimate only: Inception 50k CIFAR images ~10-40 min; CLIP ~20-90 min; DINOv2 ~30-120 min on T4x2",
        "kaggle_feature_extraction_command": KAGGLE_FEATURE_EXTRACTION_COMMAND if source_package_ready_for_kaggle else None,
        "kaggle_inception_feature_extraction_command": KAGGLE_INCEPTION_FEATURE_EXTRACTION_COMMAND if source_package_ready_for_kaggle else None,
        "kaggle_clip_feature_extraction_command": KAGGLE_CLIP_FEATURE_EXTRACTION_COMMAND if source_package_ready_for_kaggle else None,
        "sample_materialization": materialization,
        "generation_adapter_statuses": adapter_statuses,
        "cpu_commands_after_feature_caches": CPU_AFTER_CACHE_COMMANDS,
        "gates": {
            "provenance": provenance,
            "sample_manifest": manifest,
            "preprocessing_lock": lock,
            "feature_caches": caches,
            "metric_reproduction": reproduction,
        },
        "certificate_metrics_when_ready": ["mmd_rbf", "cmmd_clip_mmd"],
        "descriptive_only_metrics": ["kid_polynomial", "fid_inception", "fd_dinov2"],
        "exact_next_command": exact_next_command,
    }
    write_json(payload, out_json)

    lines = [
        "# CERTGEN_R1_CIFAR10_REAL_PILOT Readiness",
        "",
        "`NO_REAL_EVIDENCE`",
        "",
        f"Status: `{status_code}`",
        "Claim allowed: `False`",
        "",
        "## Summary",
        "",
        "- Selected benchmark: `cifar10`",
        f"- Selected candidate model pairs: `{len(SELECTED_CANDIDATE_MODEL_PAIRS)}`",
        f"- Source status: `{payload['source_status']}`",
        f"- License status: `{payload['license_status']}`",
        f"- Sample availability: `{payload['sample_availability']}`",
        f"- Feature-cache status: `{payload['feature_cache_status']}`",
        f"- Metric reproduction status: `{payload['metric_reproduction_status']}`",
        f"- Kaggle feature extraction needed: `{payload['kaggle_feature_extraction_needed']}`",
        f"- Kaggle feature extraction ready: `{payload['kaggle_feature_extraction_ready']}`",
        f"- Estimated Kaggle runtime if needed: {payload['estimated_kaggle_runtime_if_needed']}",
        "- Updated R1B blocker taxonomy: `BLOCKED_MISSING_REFERENCE_SAMPLES`, `BLOCKED_GENERATION_NOT_RUN`, `BLOCKED_GENERATION_INCOMPLETE`, `BLOCKED_GENERATION_MANIFEST_INVALID`, `READY_FOR_KAGGLE_FEATURE_EXTRACTION`",
        "",
        "## Blockers",
    ]
    lines.extend(f"- {item}" for item in blockers or ["none"])
    lines.extend(["", "## Selected Candidate Model Pairs", "", "| pair_id | role | model_a | model_b | status |", "|---|---|---|---|---|"])
    lines.extend(
        f"| `{item['pair_id']}` | `{item['role']}` | `{item['model_a']}` | `{item['model_b']}` | `{item['status']}` |"
        for item in SELECTED_CANDIDATE_MODEL_PAIRS
    )
    lines.extend(["", "## Candidate Role Table", "", "| candidate_id | role | status | purpose |", "|---|---|---|---|"])
    lines.extend(f"| `{item['candidate_id']}` | `{item['role']}` | `{item['status']}` | {item['purpose']} |" for item in R1_CANDIDATES)
    lines.extend(["", "## Replacement-Candidate Table", "", "| candidate_id | status | reason |", "|---|---|---|"])
    lines.extend(f"| `{item['candidate_id']}` | `{item['status']}` | {item['reason']} |" for item in REPLACEMENT_CANDIDATES)
    lines.extend(["", "## R1B Sample Materialization", "", "| item | value |", "|---|---|"])
    lines.extend(
        [
            f"| `reference_rows` | `{materialization['reference_rows']}` |",
            f"| `generated_rows` | `{materialization['generated_rows']}` |",
            f"| `missing_reference_paths` | `{len(materialization['missing_reference_paths'])}` |",
            f"| `missing_generated_paths` | `{len(materialization['missing_generated_paths'])}` |",
            f"| `generation_blockers` | `{len(materialization['generation_blockers'])}` |",
        ]
    )
    lines.extend(["", "## Generation Adapter Status", "", "| checkpoint_id | adapter_status | pipeline_class |", "|---|---|---|"])
    lines.extend(
        f"| `{checkpoint}` | `{status.get('adapter_status')}` | `{status.get('pipeline_class')}` |"
        for checkpoint, status in adapter_statuses.items()
    )
    lines.extend(["", "## Kaggle Feature Extraction Command", ""])
    if source_package_ready_for_kaggle:
        lines.extend(
            [
                "### Inception",
                "",
                f"`{KAGGLE_INCEPTION_FEATURE_EXTRACTION_COMMAND}`",
                "",
                "### CLIP",
                "",
                f"`{KAGGLE_CLIP_FEATURE_EXTRACTION_COMMAND}`",
            ]
        )
    else:
        lines.append("`not_ready: source package is not feature-extraction-ready`")
    lines.extend(["", "## CPU Commands After Feature Caches Are Available"])
    lines.extend(f"- `{command}`" for command in CPU_AFTER_CACHE_COMMANDS)
    lines.extend(["", "## Exact Next Command", "", f"`{exact_next_command}`", ""])
    Path(report).parent.mkdir(parents=True, exist_ok=True)
    Path(report).write_text("\n".join(lines), encoding="utf-8")
    return payload
