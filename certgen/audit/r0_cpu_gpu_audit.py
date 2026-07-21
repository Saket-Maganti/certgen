"""R0 CPU/GPU separation audit."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from certgen.certs.api import certify_clean_metric_comparison
from certgen.certs.fid_policy import assert_no_rigorous_fid_claim
from certgen.core.io import write_json
from certgen.fixtures.make_v2_feature_fixtures import make_v2_feature_fixtures
from certgen.metrics.streams import mmd_difference_stream
from certgen.pipeline.cifar10_real_pilot import run_cifar10_r1_readiness


REQUIRED_CPU_COMMANDS = [
    "00_validate_environment_cpu.sh",
    "01_validate_provenance.sh",
    "02_validate_feature_caches.sh",
    "03_reproduce_metric_from_features.sh",
    "04_run_clean_core_certificates_cpu.sh",
    "05_run_optional_stopping_lab_cpu.sh",
    "06_generate_pilot_report_cpu.sh",
    "07_run_r0_audit_cpu.sh",
]


def _read(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def _json_files(root: Path) -> list[Path]:
    return [path for path in root.rglob("*.json") if path.is_file()] if root.exists() else []


def _has_claim_allowed_true(value: Any) -> bool:
    if isinstance(value, dict):
        return any((key == "claim_allowed" and item is True) or _has_claim_allowed_true(item) for key, item in value.items())
    if isinstance(value, list):
        return any(_has_claim_allowed_true(item) for item in value)
    return False


def _claim_allowed_true_artifacts() -> list[str]:
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


def _fid_claim_offenders() -> list[str]:
    offenders: list[str] = []
    for root in [Path("data"), Path("docs"), Path("paper")]:
        paths = list(root.rglob("*.json")) if root.exists() else []
        for path in paths:
            try:
                payload = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
            except Exception:
                continue
            stack = [payload]
            while stack:
                item = stack.pop()
                if isinstance(item, dict):
                    try:
                        assert_no_rigorous_fid_claim(item)
                    except ValueError:
                        offenders.append(str(path))
                    stack.extend(item.values())
                elif isinstance(item, list):
                    stack.extend(item)
    return sorted(set(offenders))


def _validate_cpu_first_config(path: str | Path) -> tuple[bool, str]:
    config = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    required = {
        "execution_mode": "cpu_first",
        "certificate_device": "cpu",
        "reports_device": "cpu",
        "claim_allowed_default": False,
        "fid_certificate_allowed": False,
        "polynomial_kid_certificate_allowed": False,
        "bounded_rbf_mmd_certificate_allowed": True,
        "cmmd_bounded_certificate_allowed": True,
    }
    for key, expected in required.items():
        if config.get(key) != expected:
            return False, f"{key} expected {expected!r}, got {config.get(key)!r}"
    gpu_allowed = set(config.get("gpu_allowed_for", []))
    if gpu_allowed != {"feature_extraction", "optional_sample_generation"}:
        return False, f"unexpected gpu_allowed_for: {sorted(gpu_allowed)}"
    paths = config.get("paths") or {}
    for key in ["provenance_ledger", "sample_manifest", "feature_cache_dir", "preprocessing_lock", "r0_cpu_results_dir"]:
        if key not in paths:
            return False, f"missing paths.{key}"
    return True, "cpu-first config valid"


def _bounded_paths_available() -> tuple[bool, str]:
    r = np.tile(np.array([[1.0, 0.0]]), (16, 1))
    a = r + 0.01
    b = np.tile(np.array([[0.0, 1.0]]), (16, 1))
    mmd = mmd_difference_stream(a, b, r, {"name": "rbf", "normalize": "l2"}, metric_label="mmd_rbf", seed=0)
    cmmd = mmd_difference_stream(a, b, r, {"name": "rbf", "normalize": "l2"}, metric_label="cmmd_clip_mmd", seed=0)
    ok = mmd.bounded and cmmd.bounded and mmd.lower_bound == -3.0 and cmmd.upper_bound == 3.0
    return ok, "bounded RBF-MMD and CMMD streams available"


def _polynomial_kid_blocked() -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as tmp:
        paths = make_v2_feature_fixtures(Path(tmp) / "features", seed=0)
        try:
            certify_clean_metric_comparison(
                paths["model_a_close"],
                paths["model_b_far"],
                paths["reference"],
                "kid_polynomial",
                {},
                {"alpha": 0.05, "budget_units": 4},
                "kid_policy_check",
                "smoke_only",
                str(Path(tmp) / "kid.json"),
            )
        except ValueError as exc:
            return "polynomial" in str(exc).lower(), str(exc)
    return False, "kid_polynomial unexpectedly entered rigorous certificate path"


def run_audit(*, out: str | Path, json_out: str | Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def add(name: str, passed: bool, detail: Any) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    policy = Path("docs/R0_CPU_GPU_EXECUTION_POLICY.md")
    policy_text = _read(policy) if policy.exists() else ""
    add(
        "cpu_gpu_execution_policy_doc_exists",
        policy.exists() and "CertGen certificates and audits are CPU-side" in policy_text,
        str(policy),
    )

    command_dir = Path("commands/r0_cpu")
    missing_commands = [name for name in REQUIRED_CPU_COMMANDS if not (command_dir / name).exists()]
    add("cpu_command_bundle_exists", not missing_commands, missing_commands or "all required commands present")
    unsafe_commands = []
    for name in REQUIRED_CPU_COMMANDS:
        path = command_dir / name
        if path.exists():
            text = _read(path)
            if 'CUDA_VISIBLE_DEVICES=""' not in text or "PYTHONDONTWRITEBYTECODE=1" not in text:
                unsafe_commands.append(name)
    add("cpu_commands_disable_cuda", not unsafe_commands, unsafe_commands or "all CPU commands disable CUDA")

    feature_runbook = Path("docs/KAGGLE_T4X2_FEATURE_EXTRACTION_RUNBOOK_R0.md")
    feature_text = _read(feature_runbook) if feature_runbook.exists() else ""
    add("kaggle_feature_extraction_runbook_exists", feature_runbook.exists(), str(feature_runbook))
    add(
        "feature_runbook_uses_t4x2_sharding",
        "CUDA_VISIBLE_DEVICES=0" in feature_text and "--shard-id 0" in feature_text and "--num-shards 2" in feature_text,
        "two-process sharding documented",
    )

    generation_runbook = Path("docs/KAGGLE_T4X2_PARALLEL_SEED_GENERATION_RUNBOOK_R0.md")
    generation_text = _read(generation_runbook) if generation_runbook.exists() else ""
    add("kaggle_parallel_seed_generation_runbook_exists", generation_runbook.exists(), str(generation_runbook))
    add(
        "generation_runbook_prefers_released_samples",
        "Prefer released samples" in generation_text and "Sample generation is not implemented" in generation_text,
        "preference and placeholder documented",
    )

    runtime_doc = Path("docs/R0_RUNTIME_ESTIMATES_CPU_AND_KAGGLE_T4X2.md")
    runtime_text = _read(runtime_doc) if runtime_doc.exists() else ""
    add(
        "runtime_estimates_doc_exists_and_labeled",
        runtime_doc.exists() and "planning estimates, not empirical project results" in runtime_text,
        str(runtime_doc),
    )

    try:
        config_ok, config_detail = _validate_cpu_first_config("configs/certgen_r0_cpu_first.yaml")
    except Exception as exc:
        config_ok, config_detail = False, str(exc)
    add("cpu_first_config_validates", config_ok, config_detail)

    claim_offenders = _claim_allowed_true_artifacts()
    add("no_real_evidence_claims_promoted", not claim_offenders, claim_offenders or "no claim_allowed=true JSON artifacts")

    fid_offenders = _fid_claim_offenders()
    add("no_rigorous_fid_certificate_claim_exists", not fid_offenders, fid_offenders or "no rigorous FID certificate claims")

    kid_ok, kid_detail = _polynomial_kid_blocked()
    add("polynomial_kid_rigorous_certificate_disabled", kid_ok, kid_detail)

    bounded_ok, bounded_detail = _bounded_paths_available()
    add("bounded_rbf_cmmd_certificate_path_available", bounded_ok, bounded_detail)

    command_index = Path("docs/COMMAND_INDEX_R0.md")
    command_index_text = _read(command_index) if command_index.exists() else ""
    add(
        "tests_are_external_verification_command_documented",
        "python3 -m pytest -q" in command_index_text or "pytest" in command_index_text,
        "pytest command documented externally",
    )

    r1 = run_cifar10_r1_readiness(
        provenance_ledger="registry/provenance/cifar10_r1_ledger.csv",
        sample_manifest="registry/manifests/cifar10_r1_samples.jsonl",
        preprocessing_lock="configs/preprocessing_locks/cifar10_inception_bilinear_299.json",
        feature_cache_dir="data/features/cifar10_r1",
        metric_reproduction_audit="data/results/cifar10_r1_metric_reproduction.json",
        out_json="data/results/r1_cifar10_status.json",
        report="docs/R1_CIFAR10_REAL_PILOT_READINESS.md",
    )
    r1_ok = r1.get("status_code") == "READY_FOR_R1_REAL_PILOT" or (str(r1.get("status_code", "")).startswith("BLOCKED_") and bool(r1.get("blockers")))
    add("r1_cifar10_ready_or_blocked_with_reason", r1_ok, {"status_code": r1.get("status_code"), "blockers": r1.get("blockers", [])})

    passed = all(check["passed"] for check in checks)
    payload = {
        "audit_name": "r0_cpu_gpu_audit",
        "passed": passed,
        "checks_passed": sum(1 for check in checks if check["passed"]),
        "checks_total": len(checks),
        "checks": checks,
        "claim_allowed": False,
        "r1_status_code": r1.get("status_code"),
        "r1_ready": r1.get("ready_for_r1"),
        "exact_next_command": r1.get("exact_next_command"),
    }
    lines = [
        "# R0 CPU/GPU Audit",
        "",
        "`NO_REAL_EVIDENCE`",
        "",
        f"Audit status: `{'passed' if passed else 'failed'}`",
        f"Checks passed: `{payload['checks_passed']}/{payload['checks_total']}`",
        "Claim allowed: `False`",
        "",
        "| Check | Status | Detail |",
        "|---|---:|---|",
    ]
    for check in checks:
        detail = str(check["detail"]).replace("|", "\\|").replace("\n", " ")
        lines.append(f"| `{check['name']}` | `{'pass' if check['passed'] else 'fail'}` | {detail} |")
    lines.extend(["", "## R1 CIFAR-10 Status", "", f"- Status code: `{r1.get('status_code')}`"])
    lines.extend(f"- {blocker}" for blocker in r1.get("blockers", []) or ["none"])
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_json(payload, json_out)
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the R0 CPU/GPU separation audit.")
    parser.add_argument("--out", required=True)
    parser.add_argument("--json-out", required=True)
    args = parser.parse_args(argv)
    payload = run_audit(out=args.out, json_out=args.json_out)
    print(f"R0 CPU/GPU audit status: {'passed' if payload['passed'] else 'failed'}")
    return 0 if payload["passed"] else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
