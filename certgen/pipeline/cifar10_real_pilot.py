"""R1 CIFAR-10 real-pilot readiness checks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from certgen.core.io import read_json, write_json
from certgen.features.cache_validate import validate_v3_feature_cache
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

R1_CANDIDATES = [
    {
        "candidate_id": "cifar10_null_real_split",
        "role": "null_calibration_pair",
        "purpose": "same-source CIFAR-10 split-vs-split calibration",
        "status": "candidate_requires_real_manifest",
    },
    {
        "candidate_id": "cifar10_obvious_gap_corruption_sanity",
        "role": "obvious_gap_sanity_pair",
        "purpose": "reference samples versus clearly corrupted/noise replacement samples for software sanity only",
        "status": "candidate_requires_real_reference_manifest",
    },
    {
        "candidate_id": "cifar10_medium_gap_public_baseline_pair",
        "role": "medium_gap_pair",
        "purpose": "public released-sample baseline versus stronger public released-sample model",
        "status": "candidate_requires_source_selection",
    },
    {
        "candidate_id": "cifar10_close_gap_two_strong_models",
        "role": "close_gap_pair",
        "purpose": "two strong public CIFAR-10 generators with similar reported metric values",
        "status": "candidate_requires_source_selection",
    },
    {
        "candidate_id": "cifar10_preprocessing_sensitivity_pair",
        "role": "preprocessing_sensitivity_pair",
        "purpose": "same samples under declared preprocessing-lock variant if local sources permit",
        "status": "candidate_requires_primary_ready_path",
    },
]


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
    for required_role in ["reference", "model_a", "model_b"]:
        if required_role not in roles:
            errors.append(f"manifest missing role: {required_role}")
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

    ready = not blockers
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
        "ready_for_r1": ready,
        "claim_allowed": False,
        "promote_to_paper_evidence": False,
        "blockers": blockers,
        "warnings": warnings,
        "candidates": R1_CANDIDATES,
        "replacement_candidates": R1_CANDIDATES,
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
        f"Status: `{payload['status']}`",
        "Claim allowed: `False`",
        "",
        "## Blockers",
    ]
    lines.extend(f"- {item}" for item in blockers or ["none"])
    lines.extend(["", "## Candidate Pairs"])
    lines.extend(f"- `{item['candidate_id']}`: {item['role']} ({item['status']})" for item in R1_CANDIDATES)
    lines.extend(["", "## Exact Next Command", "", f"`{exact_next_command}`", ""])
    Path(report).parent.mkdir(parents=True, exist_ok=True)
    Path(report).write_text("\n".join(lines), encoding="utf-8")
    return payload
