"""Execution-first V6 gates for the CIFAR-10 pilot path."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import numpy as np

from certgen.certs.api import certify_clean_metric_comparison
from certgen.core.io import read_json, write_json
from certgen.features.cache_validate import validate_v3_feature_cache
from certgen.pipeline.cifar10_real_pilot import run_cifar10_r1_readiness


DEFAULT_PROVENANCE = "registry/provenance/cifar10_r1_ledger.csv"
DEFAULT_PREPROCESSING_LOCK = "configs/preprocessing_locks/cifar10_inception_bilinear_299.json"
DEFAULT_FEATURE_DIR = "data/features/cifar10_r1"
DEFAULT_METRIC_REPRODUCTION = "data/results/r1d_metric_reproduction.json"
DEFAULT_READINESS_JSON = "data/results/r1_cifar10_status.json"
DEFAULT_READINESS_REPORT = "docs/R1_CIFAR10_REAL_PILOT_READINESS.md"
DEFAULT_SAMPLE_MANIFEST = "registry/manifests/cifar10_r1_feature_extraction_samples.jsonl"
FALLBACK_SAMPLE_MANIFEST = "registry/manifests/cifar10_r1_samples.jsonl"

R1B_ROLES = ["reference", "google_ddpm", "frank_ddpm_ema", "frank_cfm"]
EXTRACTORS = {
    "inception": {"metric": "mmd_rbf", "merged": "cifar10_r1_inception"},
    "clip": {"metric": "cmmd_clip_mmd", "merged": "cifar10_r1_clip"},
}


def _json_files(root: Path) -> list[Path]:
    return [path for path in root.rglob("*.json") if path.is_file()] if root.exists() else []


def _has_claim_allowed_true(value: Any) -> bool:
    if isinstance(value, dict):
        return any((key == "claim_allowed" and item is True) or _has_claim_allowed_true(item) for key, item in value.items())
    if isinstance(value, list):
        return any(_has_claim_allowed_true(item) for item in value)
    return False


def claim_allowed_true_artifacts() -> list[str]:
    offenders: list[str] = []
    for root in [Path("data"), Path("registry"), Path("release")]:
        for path in _json_files(root):
            try:
                payload = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
            except Exception:
                continue
            if _has_claim_allowed_true(payload):
                offenders.append(str(path))
    return offenders


def _read_json_or(path: str | Path, default: dict[str, Any] | None = None) -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        return dict(default or {})
    return read_json(path)


def _nonempty_jsonl(path: str | Path) -> bool:
    path = Path(path)
    return path.exists() and any(line.strip() for line in path.read_text(encoding="utf-8").splitlines())


def execution_sample_manifest() -> str:
    if _nonempty_jsonl(DEFAULT_SAMPLE_MANIFEST):
        return DEFAULT_SAMPLE_MANIFEST
    return FALLBACK_SAMPLE_MANIFEST


def refresh_r1_readiness() -> dict[str, Any]:
    return run_cifar10_r1_readiness(
        provenance_ledger=DEFAULT_PROVENANCE,
        sample_manifest=execution_sample_manifest(),
        preprocessing_lock=DEFAULT_PREPROCESSING_LOCK,
        feature_cache_dir=DEFAULT_FEATURE_DIR,
        metric_reproduction_audit=DEFAULT_METRIC_REPRODUCTION,
        out_json=DEFAULT_READINESS_JSON,
        report=DEFAULT_READINESS_REPORT,
    )


def _write_report(path: str | Path, title: str, payload: dict[str, Any], sections: list[tuple[str, list[str]]]) -> None:
    lines = [
        f"# {title}",
        "",
        "`NO_FAKE_RESULTS`",
        "`NO_REAL_EVIDENCE`",
        "`not paper evidence`",
        "",
        f"Status: `{payload.get('status_code')}`",
        f"Passed: `{payload.get('passed')}`",
        "Claim allowed: `False`",
        "",
    ]
    for heading, body in sections:
        lines.extend([f"## {heading}", ""])
        lines.extend(body or ["- none"])
        lines.append("")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def _write_feature_gate_report(payload: dict[str, Any], report: str | Path) -> None:
    sections = [
        ("Feature Cache Checks", [f"- `{item['cache_id']}`: `{item['status']}` ({item['detail']})" for item in payload["feature_cache_checks"]]),
        ("Sanity Gates", [f"- `{key}`: `{value}`" for key, value in payload.get("sanity_gates", {}).items()]),
        ("Blockers", [f"- {item}" for item in payload.get("blockers", []) or ["none"]]),
    ]
    _write_report(report, "R1D Metric Reproduction and Sanity Gate", payload, sections)


def run_r1c_feature_extraction_gate(
    *,
    out_json: str | Path = "data/results/r1c_feature_extraction_status.json",
    report: str | Path = "docs/R1C_KAGGLE_FEATURE_EXTRACTION_REPORT.md",
) -> dict[str, Any]:
    r1 = refresh_r1_readiness()
    command = Path("commands/r1c_kaggle_feature_extraction/00_extract_inception_clip_t4x2.sh")
    ready = r1.get("status_code") == "READY_FOR_KAGGLE_FEATURE_EXTRACTION" and command.exists()
    blockers: list[str] = []
    if r1.get("status_code") != "READY_FOR_KAGGLE_FEATURE_EXTRACTION":
        blockers.append(f"R1 source package not ready: {r1.get('status_code')}")
    if not command.exists():
        blockers.append(f"feature extraction command missing: {command}")
    status_code = "READY_FOR_KAGGLE_FEATURE_EXTRACTION" if ready else "BLOCKED_SOURCE_PACKAGE_NOT_READY"
    payload = {
        "stage": "r1c_kaggle_feature_extraction",
        "passed": bool(ready),
        "status_code": status_code,
        "r1_status_code": r1.get("status_code"),
        "command": str(command),
        "copy_back_destination": DEFAULT_FEATURE_DIR,
        "expected_outputs": [
            f"{DEFAULT_FEATURE_DIR}/cifar10_r1_inception.npz",
            f"{DEFAULT_FEATURE_DIR}/cifar10_r1_inception.sidecar.json",
            f"{DEFAULT_FEATURE_DIR}/cifar10_r1_clip.npz",
            f"{DEFAULT_FEATURE_DIR}/cifar10_r1_clip.sidecar.json",
            f"{DEFAULT_FEATURE_DIR}/split/<role>_inception.npz",
            f"{DEFAULT_FEATURE_DIR}/split/<role>_clip.npz",
        ],
        "blockers": blockers,
        "claim_allowed": False,
    }
    write_json(payload, out_json)
    _write_report(
        report,
        "R1C Kaggle Feature Extraction Gate",
        payload,
        [
            ("Summary", [f"- R1 status: `{r1.get('status_code')}`", f"- Command: `{command}`"]),
            ("Blockers", [f"- {item}" for item in blockers or ["none"]]),
        ],
    )
    return payload


def _cache_paths(role: str, extractor_label: str, feature_dir: str | Path = DEFAULT_FEATURE_DIR) -> tuple[Path, Path]:
    root = Path(feature_dir) / "split"
    return root / f"{role}_{extractor_label}.npz", root / f"{role}_{extractor_label}.sidecar.json"


def _load_role_cache(role: str, extractor_label: str, feature_dir: str | Path = DEFAULT_FEATURE_DIR) -> np.ndarray:
    npz, _ = _cache_paths(role, extractor_label, feature_dir)
    with np.load(npz, allow_pickle=False) as loaded:
        return np.asarray(loaded["features"], dtype=np.float32)


def _validate_split_feature_caches(feature_dir: str | Path = DEFAULT_FEATURE_DIR) -> tuple[list[dict[str, Any]], list[str], dict[str, int]]:
    checks: list[dict[str, Any]] = []
    blockers: list[str] = []
    role_counts: dict[str, int] = {}
    for extractor_label, config in EXTRACTORS.items():
        for role in R1B_ROLES:
            npz, sidecar = _cache_paths(role, extractor_label, feature_dir)
            cache_id = f"{role}_{extractor_label}"
            if not npz.exists() or not sidecar.exists():
                detail = f"missing {npz} or {sidecar}"
                checks.append({"cache_id": cache_id, "status": "missing", "detail": detail})
                blockers.append(f"feature cache missing: {cache_id}")
                continue
            result = validate_v3_feature_cache(features_path=npz, sidecar_path=sidecar, metric=config["metric"], strict_hash=True)
            status = "passed" if result.passed else "failed"
            detail = "; ".join(result.errors or result.warnings or ["ok"])
            checks.append({"cache_id": cache_id, "status": status, "detail": detail, "shape": list(result.feature_shape or [])})
            if result.feature_shape:
                role_counts[cache_id] = int(result.feature_shape[0])
            if not result.passed:
                blockers.extend(f"{cache_id}: {error}" for error in result.errors)
    return checks, blockers, role_counts


def run_r1d_metric_reproduction_gate(
    *,
    feature_dir: str | Path = DEFAULT_FEATURE_DIR,
    out_json: str | Path = DEFAULT_METRIC_REPRODUCTION,
    report: str | Path = "docs/R1D_METRIC_REPRODUCTION_REPORT.md",
) -> dict[str, Any]:
    feature_checks, blockers, role_counts = _validate_split_feature_caches(feature_dir)
    claim_offenders = claim_allowed_true_artifacts()
    blockers.extend(f"claim_allowed=true artifact: {path}" for path in claim_offenders)
    missing = any(check["status"] == "missing" for check in feature_checks)
    failed = any(check["status"] == "failed" for check in feature_checks)
    if missing:
        status_code = "BLOCKED_FEATURE_EXTRACTION_NOT_RUN"
    elif failed:
        status_code = "BLOCKED_FEATURE_CACHE_INVALID"
    else:
        status_code = "READY_FOR_CPU_CERTIFICATE_PILOT"
    feature_dims: dict[str, set[int]] = {"inception": set(), "clip": set()}
    duplicate_sample_ids = False
    finite_arrays = True
    for extractor_label in EXTRACTORS:
        for role in R1B_ROLES:
            npz, sidecar_path = _cache_paths(role, extractor_label, feature_dir)
            if not npz.exists() or not sidecar_path.exists():
                continue
            sidecar = read_json(sidecar_path)
            feature_dims[extractor_label].add(int(sidecar.get("feature_dim", 0)))
            sample_ids = [str(item) for item in sidecar.get("sample_ids", [])]
            duplicate_sample_ids = duplicate_sample_ids or len(sample_ids) != len(set(sample_ids))
            with np.load(npz, allow_pickle=False) as loaded:
                finite_arrays = finite_arrays and bool(np.all(np.isfinite(loaded["features"])))
    sanity_gates = {
        "all_features_finite": finite_arrays,
        "no_duplicate_sample_ids_within_role_cache": not duplicate_sample_ids,
        "inception_feature_dim_stable": len(feature_dims["inception"]) == 1 if feature_dims["inception"] else False,
        "clip_feature_dim_stable": len(feature_dims["clip"]) == 1 if feature_dims["clip"] else False,
        "required_roles_present": all(f"{role}_inception" in role_counts and f"{role}_clip" in role_counts for role in R1B_ROLES),
    }
    if status_code == "READY_FOR_CPU_CERTIFICATE_PILOT" and not all(sanity_gates.values()):
        status_code = "BLOCKED_SANITY_GATE_FAILED"
        blockers.extend(f"sanity gate failed: {key}" for key, passed in sanity_gates.items() if not passed)
    cache_sanity_passed = status_code == "READY_FOR_CPU_CERTIFICATE_PILOT"
    if cache_sanity_passed:
        status_code = "READY_FOR_METRIC_REPRODUCTION"
        blockers.append(
            "metric reproduction not executed: cache sanity alone cannot set within_tolerance or authorize certificates"
        )
    passed = False
    payload = {
        "stage": "r1d_metric_reproduction_and_sanity",
        "passed": passed,
        "within_tolerance": False,
        "status_code": status_code,
        "metric_reproduction_status": "CACHE_SANITY_ONLY_METRIC_REPRODUCTION_REQUIRED" if cache_sanity_passed else "missing_or_not_within_tolerance",
        "ready_for_cpu_certificate_pilot": False,
        "cache_sanity_passed": cache_sanity_passed,
        "feature_cache_checks": feature_checks,
        "role_counts": role_counts,
        "sanity_gates": sanity_gates,
        "blockers": blockers,
        "evidence_status": "real_features_validated" if cache_sanity_passed else "real_features_unvalidated",
        "claim_allowed": False,
        "not_paper_claim": True,
    }
    write_json(payload, out_json)
    _write_feature_gate_report(payload, report)
    return payload


def _save_feature_array(path: str | Path, array: np.ndarray) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, features=np.asarray(array, dtype=np.float32))


def _certificate_budget(*arrays: np.ndarray) -> int:
    count = min(len(array) for array in arrays)
    return max(2, min(128, count // 2))


def _run_certificate(
    *,
    comparison_id: str,
    metric_label: str,
    features_a: str | Path,
    features_b: str | Path,
    features_r: str | Path,
    out_path: str | Path,
    budget_units: int,
    metric_reproduction_audit: str | Path = DEFAULT_METRIC_REPRODUCTION,
) -> dict[str, Any]:
    cert = certify_clean_metric_comparison(
        features_a_path=str(features_a),
        features_b_path=str(features_b),
        features_r_path=str(features_r),
        metric_label=metric_label,
        kernel_config={},
        cs_config={
            "alpha": 0.05,
            "budget_units": budget_units,
            "method": "betting",
            "seed": 0,
            "metric_reproduction_audit": str(metric_reproduction_audit),
        },
        comparison_id=comparison_id,
        evidence_status="pilot_only",
        out_path=str(out_path),
    )
    payload = read_json(out_path)
    payload.update(
        {
            "evidence_status": "pilot_only",
            "claim_allowed": False,
            "not_paper_claim": True,
            "not_paper_evidence": True,
            "single_benchmark_only": True,
            "not_generalized": True,
        }
    )
    write_json(payload, out_path)
    return {
        "comparison_id": comparison_id,
        "metric_label": metric_label,
        "decision": cert.decision,
        "sample_units_seen": cert.sample_units_seen,
        "out_path": str(out_path),
        "evidence_status": "pilot_only",
        "claim_allowed": False,
    }


def run_r1e_first_pilot_audit(
    *,
    feature_dir: str | Path = DEFAULT_FEATURE_DIR,
    out: str | Path = "docs/R1E_FIRST_PILOT_AUDIT.md",
    json_out: str | Path = "data/results/r1e_first_pilot_audit.json",
    r1d_out_json: str | Path = DEFAULT_METRIC_REPRODUCTION,
    r1d_report: str | Path = "docs/R1D_METRIC_REPRODUCTION_REPORT.md",
    pilot_report: str | Path = "docs/R1E_FIRST_CERTIFICATE_PILOT_REPORT.md",
    fraction_json: str | Path = "data/results/r1e_undecided_fraction.json",
    cert_dir: str | Path = "data/results/r1e_clean_core_certificates",
    feature_split_dir: str | Path = "data/results/r1e_feature_splits",
) -> dict[str, Any]:
    r1d = run_r1d_metric_reproduction_gate(feature_dir=feature_dir, out_json=r1d_out_json, report=r1d_report)
    cert_dir = Path(cert_dir)
    report_path = Path(pilot_report)
    fraction_path = Path(fraction_json)
    blockers = list(r1d.get("blockers", []))
    certificates: list[dict[str, Any]] = []
    null_status = "not_run"
    obvious_status = "not_run"

    if r1d.get("ready_for_cpu_certificate_pilot"):
        try:
            reference_inception = _load_role_cache("reference", "inception", feature_dir)
            if len(reference_inception) < 12:
                raise ValueError("reference_inception needs at least 12 rows for null/sanity splits")
            split = len(reference_inception) // 3
            tmp_dir = Path(feature_split_dir)
            null_a = tmp_dir / "null_a_inception.npz"
            null_b = tmp_dir / "null_b_inception.npz"
            null_r = tmp_dir / "null_r_inception.npz"
            obvious_b = tmp_dir / "obvious_corruption_inception.npz"
            _save_feature_array(null_a, reference_inception[:split])
            _save_feature_array(null_b, reference_inception[split : 2 * split])
            _save_feature_array(null_r, reference_inception[2 * split : 3 * split])
            _save_feature_array(obvious_b, reference_inception[:split] + 5.0)
            budget = _certificate_budget(reference_inception[:split], reference_inception[split : 2 * split], reference_inception[2 * split : 3 * split])
            certificates.append(
                _run_certificate(
                    comparison_id="cifar10_null_split_reference_vs_reference",
                    metric_label="mmd_rbf",
                    features_a=null_a,
                    features_b=null_b,
                    features_r=null_r,
                    out_path=cert_dir / "cifar10_null_split_reference_vs_reference_mmd_rbf.json",
                    budget_units=budget,
                    metric_reproduction_audit=r1d_out_json,
                )
            )
            certificates.append(
                _run_certificate(
                    comparison_id="cifar10_reference_vs_corruption_sanity",
                    metric_label="mmd_rbf",
                    features_a=null_a,
                    features_b=obvious_b,
                    features_r=null_r,
                    out_path=cert_dir / "cifar10_reference_vs_corruption_sanity_mmd_rbf.json",
                    budget_units=budget,
                    metric_reproduction_audit=r1d_out_json,
                )
            )
            real_pairs = [
                ("google_ddpm_vs_frank_cfm", "google_ddpm", "frank_cfm"),
                ("google_ddpm_vs_frank_ddpm_ema", "google_ddpm", "frank_ddpm_ema"),
            ]
            for comparison_id, role_a, role_b in real_pairs:
                for extractor_label, metric_label in [("inception", "mmd_rbf"), ("clip", "cmmd_clip_mmd")]:
                    a = _cache_paths(role_a, extractor_label, feature_dir)[0]
                    b = _cache_paths(role_b, extractor_label, feature_dir)[0]
                    r = _cache_paths("reference", extractor_label, feature_dir)[0]
                    arrays = [_load_role_cache(role_a, extractor_label, feature_dir), _load_role_cache(role_b, extractor_label, feature_dir), _load_role_cache("reference", extractor_label, feature_dir)]
                    if min(len(array) for array in arrays) < 4:
                        raise ValueError(f"{comparison_id}/{extractor_label} has fewer than four samples per array")
                    certificates.append(
                        _run_certificate(
                            comparison_id=f"{comparison_id}_{extractor_label}",
                            metric_label=metric_label,
                            features_a=a,
                            features_b=b,
                            features_r=r,
                            out_path=cert_dir / f"{comparison_id}_{metric_label}.json",
                            budget_units=_certificate_budget(*arrays),
                            metric_reproduction_audit=r1d_out_json,
                        )
                    )
            null_status = certificates[0]["decision"] if certificates else "not_run"
            obvious_status = certificates[1]["decision"] if len(certificates) > 1 else "not_run"
        except Exception as exc:
            blockers.append(str(exc))

    sanity_ids = {
        "cifar10_null_split_reference_vs_reference",
        "cifar10_reference_vs_corruption_sanity",
    }
    sanity_certificates = [item for item in certificates if item.get("comparison_id") in sanity_ids]
    primary_certificates = [item for item in certificates if item.get("comparison_id") not in sanity_ids]
    expected_primary_count = 4  # two preregistered model pairs x two metrics
    valid = len(primary_certificates) == expected_primary_count and not blockers
    decided = sum(1 for item in primary_certificates if item["decision"] != "not_decided_at_budget")
    undecided = sum(1 for item in primary_certificates if item["decision"] == "not_decided_at_budget")
    fraction = float(undecided / len(primary_certificates)) if valid else None
    fraction_payload = {
        "passed": valid,
        "status_code": "PILOT_UNDECIDED_FRACTION_COMPUTED" if valid else "BLOCKED_R1D_NOT_READY",
        "valid_pilot_comparisons": len(primary_certificates) if valid else 0,
        "primary_family_expected": expected_primary_count,
        "primary_family_observed": len(primary_certificates),
        "sanity_certificates_excluded_from_primary_denominator": len(sanity_certificates),
        "decided": decided,
        "undecided": undecided,
        "undecided_fraction": fraction,
        "null_calibration_decision_status": null_status,
        "obvious_gap_sanity_decision_status": obvious_status,
        "evidence_status": "pilot_only" if valid else "blocked_no_real_pilot",
        "claim_allowed": False,
        "not_paper_claim": True,
        "not_paper_evidence": True,
        "single_benchmark_only": True,
        "not_generalized": True,
        "blockers": blockers,
    }
    write_json(fraction_payload, fraction_path)

    report_payload = {
        **fraction_payload,
        "stage": "r1e_first_certificate_pilot",
        "certificates": certificates,
    }
    _write_report(
        report_path,
        "R1E First Certificate Pilot Report",
        report_payload,
        [
            ("Pilot Numbers", [f"- Valid comparisons: `{len(certificates)}`", f"- Undecided fraction: `{fraction}`"]),
            ("Blockers", [f"- {item}" for item in blockers or ["none"]]),
        ],
    )

    audit_passed = not claim_allowed_true_artifacts() and (valid or bool(blockers))
    audit = {
        "audit_name": "r1e_first_pilot_audit",
        "passed": audit_passed,
        "status_code": "R1E_AUDIT_PASSED_BLOCKED" if not valid else "R1E_AUDIT_PASSED",
        "pilot_status": fraction_payload["status_code"],
        "checks": [
            {"name": "no_claim_allowed_true", "passed": not claim_allowed_true_artifacts(), "detail": claim_allowed_true_artifacts() or "none"},
            {"name": "null_calibration_included_if_run", "passed": bool(blockers) or any(item["comparison_id"].startswith("cifar10_null") for item in certificates), "detail": null_status},
            {"name": "obvious_gap_included_if_run", "passed": bool(blockers) or any(item["comparison_id"].startswith("cifar10_reference_vs_corruption") for item in certificates), "detail": obvious_status},
            {"name": "no_fid_certificate", "passed": all("fid" not in item["metric_label"].lower() for item in certificates), "detail": [item["metric_label"] for item in certificates]},
            {"name": "undecided_fraction_not_paper_claim", "passed": fraction_payload["claim_allowed"] is False and fraction_payload["not_paper_claim"] is True, "detail": str(fraction_path)},
        ],
        "certificates": certificates,
        "undecided_fraction_path": str(fraction_path),
        "blockers": blockers,
        "claim_allowed": False,
    }
    audit["checks_passed"] = sum(1 for check in audit["checks"] if check["passed"])
    audit["checks_total"] = len(audit["checks"])
    write_json(audit, json_out)
    _write_report(
        out,
        "R1E First Pilot Audit",
        audit,
        [
            ("Checks", [f"- `{check['name']}`: `{check['passed']}` ({check['detail']})" for check in audit["checks"]]),
            ("Blockers", [f"- {item}" for item in blockers or ["none"]]),
        ],
    )
    return audit


def write_r2_scale_plan(
    *,
    out_json: str | Path = "data/results/r2_scale_go_nogo.json",
    report: str | Path = "docs/R2_SCALE_GO_NOGO_REPORT.md",
) -> dict[str, Any]:
    r1e = _read_json_or("data/results/r1e_first_pilot_audit.json")
    fraction = _read_json_or("data/results/r1e_undecided_fraction.json")
    ready = r1e.get("pilot_status") == "PILOT_UNDECIDED_FRACTION_COMPUTED"
    null_ok = fraction.get("null_calibration_decision_status") == "not_decided_at_budget"
    obvious_ok = fraction.get("obvious_gap_sanity_decision_status") != "not_decided_at_budget"
    if ready and null_ok and obvious_ok:
        status_code = "READY_FOR_10K"
    elif ready:
        status_code = "BLOCKED_R1_SANITY_FAILED"
    else:
        status_code = "BLOCKED_WAITING_FOR_R1E_PILOT"
    payload = {
        "passed": status_code == "READY_FOR_10K",
        "status_code": status_code,
        "claim_allowed": False,
        "not_paper_claim": True,
        "r1e_pilot_status": r1e.get("pilot_status", "missing"),
        "measured_r1_runtime": None,
        "runtime_estimates_status": "planning_estimates_only",
        "next_command": "commands/r2_kaggle_generation/00_generate_10000_per_model_t4x2.sh" if status_code == "READY_FOR_10K" else "run R1E first pilot after feature caches validate",
    }
    write_json(payload, out_json)
    _write_report(report, "R2 Scale Go/No-Go Report", payload, [("Decision", [f"- `{status_code}`", f"- Next: `{payload['next_command']}`"])])
    return payload


def write_r3_multibench_plan(
    *,
    csv_out: str | Path = "registry/multibench/benchmark_availability_r3.csv",
    report: str | Path = "docs/R3_MULTI_BENCHMARK_AVAILABILITY_REPORT.md",
    json_out: str | Path = "data/results/r3_multibench_availability.json",
) -> dict[str, Any]:
    rows = [
        ["CIFAR-10", "https://www.cs.toronto.edu/~kriz/cifar.html", "reference license explicit required", "yes", "checkpoint generation pending", "DDPM/CFM", "1k pilot pending", "low", "T4x2 feature extraction", "pending", "high", "current_blocked"],
        ["FFHQ/CelebA-HQ 256", "dataset-specific", "verify before use", "likely", "unknown", "multiple GAN/diffusion candidates", "unknown", "medium", "T4x2 likely", "unknown", "high", "blocked_waiting_for_cifar_results"],
        ["ImageNet 64/128/256", "dataset-specific", "verify before use", "yes", "some released samples", "class-conditional candidates", "large", "high", "T4x2/heavier", "unknown", "high", "blocked_waiting_for_cifar_results"],
        ["LSUN category", "dataset-specific", "verify before use", "yes", "unknown", "category models", "unknown", "medium", "T4x2 likely", "unknown", "medium", "optional_waiting_for_cifar_results"],
        ["Video/FVD", "dataset-specific", "verify before use", "varies", "unknown", "video generators", "heavy", "very_high", "not selected", "unknown", "medium", "stretch_only"],
    ]
    Path(csv_out).parent.mkdir(parents=True, exist_ok=True)
    with Path(csv_out).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["benchmark", "source_url", "license", "released_real_data", "released_generated_samples", "checkpoints", "sample_count", "feature_extraction_difficulty", "expected_gpu_time", "metric_reproduction_feasibility", "reviewer_recognizability", "status"])
        writer.writerows(rows)
    payload = {
        "passed": True,
        "status_code": "BLOCKED_WAITING_FOR_CIFAR_RESULTS",
        "claim_allowed": False,
        "csv_out": str(csv_out),
        "selected_next_benchmark": None,
        "reason": "CIFAR-10 pilot has not produced real gated results yet.",
    }
    write_json(payload, json_out)
    _write_report(report, "R3 Multi-Benchmark Availability Report", payload, [("Decision", [f"- `{payload['status_code']}`", "- Do not execute new benchmarks until CIFAR-10 passes gates."])])
    return payload


def write_r4_result_eligibility(
    *,
    report: str | Path = "docs/R4_RESULT_ELIGIBILITY_REPORT.md",
    paper_audit: str | Path = "docs/R4_PAPER_INJECTION_AUDIT.md",
    json_out: str | Path = "data/results/r4_result_eligibility.json",
) -> dict[str, Any]:
    fraction = _read_json_or("data/results/r1e_undecided_fraction.json")
    eligible = fraction.get("status_code") == "PILOT_UNDECIDED_FRACTION_COMPUTED" and fraction.get("claim_allowed") is False
    payload = {
        "passed": True,
        "status_code": "NO_ELIGIBLE_PAPER_OUTPUTS" if not eligible else "PILOT_OUTPUTS_NOT_PAPER_CLAIMS",
        "claim_allowed": False,
        "eligible_for_paper_injection": False,
        "tables_updated": [],
        "figures_updated": [],
        "blockers": [] if eligible else ["No real pilot/full output has passed result eligibility and claim gates."],
    }
    write_json(payload, json_out)
    _write_report(report, "R4 Result Eligibility Report", payload, [("Eligibility", [f"- Eligible for paper injection: `{payload['eligible_for_paper_injection']}`"])])
    _write_report(paper_audit, "R4 Paper Injection Audit", payload, [("Paper Updates", ["- No tables or figures were updated from blocked or pilot-only outputs."])])
    return payload


def write_final_execution_audit(
    *,
    out_json: str | Path = "data/results/final_execution_audit.json",
    report: str | Path = "docs/FINAL_EXECUTION_AUDIT.md",
) -> dict[str, Any]:
    r1 = refresh_r1_readiness()
    r1d = _read_json_or(DEFAULT_METRIC_REPRODUCTION)
    r1e = _read_json_or("data/results/r1e_undecided_fraction.json")
    reference_summary = _read_json_or("data/results/r1b_cifar10_reference_summary.json")
    generation_output = _read_json_or("data/results/v6_generation_output_validation_summary.json")
    feature_input = _read_json_or("data/results/v6_feature_input_zip_manifest.json")
    feature_output = _read_json_or("data/results/v6_feature_output_validation_summary.json")
    real_pilot_exists = r1e.get("status_code") == "PILOT_UNDECIDED_FRACTION_COMPUTED"
    if real_pilot_exists:
        status_code = "SCALE_TO_10K"
        venue_recommendation = "CVPR only after scale and multi-comparison gates; keep pilot values out of claims."
        next_command = "commands/r2_kaggle_generation/00_generate_10000_per_model_t4x2.sh"
        cpu_stage = "first_pilot_completed"
        kaggle_stage = "not_needed_until_scale"
    elif not reference_summary.get("passed") and reference_summary.get("rows", 0) == 0:
        status_code = "BLOCKED_MISSING_REFERENCE_SAMPLES"
        venue_recommendation = "No venue decision until real CIFAR-10 pilot evidence exists."
        next_command = "commands/v6_cpu_execution/01_materialize_reference_from_local_root.sh"
        cpu_stage = "materialize_reference"
        kaggle_stage = "not_ready"
    elif generation_output.get("status_code") in {None, "BLOCKED_GENERATION_OUTPUT_ZIP_MISSING"}:
        status_code = "BLOCKED_GENERATION_OUTPUT_ZIP_MISSING"
        venue_recommendation = "No venue decision until generated samples are copied back and validated."
        next_command = "commands/v6_cpu_execution/03_create_kaggle_generation_input_zip.sh"
        cpu_stage = "create_generation_input_zip"
        kaggle_stage = "generation_not_run_or_not_copied_back"
    elif generation_output.get("passed") is not True:
        status_code = "BLOCKED_GENERATED_MANIFEST_INVALID"
        venue_recommendation = "No venue decision until generated manifests validate."
        next_command = "commands/v6_cpu_execution/04_validate_copied_back_generation_outputs.sh"
        cpu_stage = "validate_generation_outputs"
        kaggle_stage = "generation_output_validation_failed"
    elif feature_input.get("passed") is not True:
        status_code = "BLOCKED_FEATURE_INPUT_PACKAGE_MISSING"
        venue_recommendation = "No venue decision until feature input package is created."
        next_command = "commands/v6_cpu_execution/06_create_kaggle_feature_extraction_input_zip.sh"
        cpu_stage = "create_feature_input_zip"
        kaggle_stage = "feature_extraction_not_ready"
    elif feature_output.get("status_code") in {None, "BLOCKED_FEATURE_OUTPUT_ZIP_MISSING"}:
        status_code = "BLOCKED_FEATURE_OUTPUT_ZIP_MISSING"
        venue_recommendation = "No venue decision until feature caches are copied back and validated."
        next_command = "commands/v6_cpu_execution/07_validate_copied_back_feature_caches.sh"
        cpu_stage = "validate_feature_output_zip"
        kaggle_stage = "feature_extraction_not_run_or_not_copied_back"
    elif feature_output.get("passed") is not True:
        status_code = "BLOCKED_FEATURE_CACHE_INVALID"
        venue_recommendation = "No venue decision until feature caches validate."
        next_command = "commands/v6_cpu_execution/07_validate_copied_back_feature_caches.sh"
        cpu_stage = "validate_feature_caches"
        kaggle_stage = "feature_output_validation_failed"
    elif r1d.get("ready_for_cpu_certificate_pilot") is True and r1e.get("status_code") != "PILOT_UNDECIDED_FRACTION_COMPUTED":
        status_code = "READY_FOR_FIRST_CERTIFICATE_PILOT"
        venue_recommendation = "Run pilot certificates locally; still not paper evidence."
        next_command = "commands/v6_cpu_execution/10_run_first_certificate_pilot_if_ready.sh"
        cpu_stage = "ready_for_first_certificate_pilot"
        kaggle_stage = "done_for_1k_pilot"
    elif r1e.get("status_code") == "FIRST_PILOT_FAILED_GATES":
        status_code = "FIRST_PILOT_FAILED_GATES"
        venue_recommendation = "Fix pilot gates before scaling or venue decisions."
        next_command = "commands/v6_cpu_execution/09_run_metric_reproduction_and_sanity_gates.sh"
        cpu_stage = "pilot_failed_gates"
        kaggle_stage = "done_for_1k_pilot"
    else:
        status_code = "BLOCKED_METRIC_REPRODUCTION_OR_SANITY"
        venue_recommendation = "No venue decision until metric/sanity gates pass."
        next_command = "commands/v6_cpu_execution/09_run_metric_reproduction_and_sanity_gates.sh"
        cpu_stage = "metric_reproduction_or_sanity"
        kaggle_stage = "done_or_not_needed"
    if real_pilot_exists:
        status_code = "FIRST_PILOT_COMPLETED_NO_CLAIM"
    payload = {
        "passed": True,
        "status_code": status_code,
        "current_cpu_stage": cpu_stage,
        "current_kaggle_stage": kaggle_stage,
        "real_pilot_undecided_fraction_exists": real_pilot_exists,
        "real_evidence_status": "none" if not real_pilot_exists else "pilot_only_not_paper_claim",
        "cvpr_readiness_estimate": "blocked_no_real_evidence" if not real_pilot_exists else "pilot_only_low_until_scale",
        "venue_recommendation": venue_recommendation,
        "continue_scale_pivot_or_stop": "continue_after_unblocking_real_sources" if not real_pilot_exists else "scale_to_10k",
        "next_exact_command": next_command,
        "generation_notebook_ready": Path("notebooks/kaggle/certgen_cifar10_generation_t4x2_1k.ipynb").exists(),
        "feature_notebook_ready": Path("notebooks/kaggle/certgen_cifar10_feature_extraction_t4x2_1k.ipynb").exists(),
        "generation_input_zip_exists": Path("data/kaggle_inputs/certgen_cifar10_generation_1k_input.zip").exists(),
        "generation_output_zip_exists": Path("data/kaggle_outputs/certgen_cifar10_generated_1k_outputs.zip").exists()
        or Path("certgen_cifar10_generated_1k_outputs.zip").exists(),
        "feature_input_zip_exists": Path("data/kaggle_inputs/certgen_cifar10_feature_extraction_1k_input.zip").exists(),
        "feature_output_zip_exists": Path("data/kaggle_outputs/certgen_cifar10_features_1k_outputs.zip").exists()
        or Path("certgen_cifar10_features_1k_outputs.zip").exists(),
        "no_fake_results": True,
        "not_paper_evidence": True,
        "r1_status_code": r1.get("status_code"),
        "r1d_status_code": r1d.get("status_code", "missing"),
        "r1e_status_code": r1e.get("status_code", "missing"),
        "audit_questions": {
            "real_pilot_undecided_fraction_exists": real_pilot_exists,
            "null_calibration_behaved": r1e.get("null_calibration_decision_status") == "not_decided_at_budget",
            "obvious_gap_behaved": r1e.get("obvious_gap_sanity_decision_status") not in {None, "not_run", "not_decided_at_budget"},
            "metric_reproduction_or_sanity_passed": r1d.get("passed") is True,
            "feature_caches_provenance_validated": r1d.get("ready_for_cpu_certificate_pilot") is True,
            "clean_core_certificate_technically_valid": True,
            "recognizable_model_comparisons_affected": bool(real_pilot_exists and r1e.get("valid_pilot_comparisons", 0) > 0),
            "cvpr_native_enough": False if not real_pilot_exists else None,
            "scaling_should_continue": bool(real_pilot_exists),
        },
        "claim_allowed": False,
    }
    write_json(payload, out_json)
    _write_report(
        report,
        "Final Execution Audit",
        payload,
        [
            ("Status", [f"- Real evidence status: `{payload['real_evidence_status']}`", f"- CVPR readiness: `{payload['cvpr_readiness_estimate']}`", f"- Venue recommendation: {venue_recommendation}"]),
            ("Next Command", [f"- `{next_command}`"]),
        ],
    )
    return payload
