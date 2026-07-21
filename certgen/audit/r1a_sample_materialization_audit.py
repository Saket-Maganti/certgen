"""R1A sample-materialization audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from certgen.core.io import write_json
from certgen.generation.generate_cifar10_diffusers import checkpoint_adapter_statuses
from certgen.pipeline.cifar10_real_pilot import run_cifar10_r1_readiness


REQUIRED_TAXONOMY = [
    "BLOCKED_MISSING_REFERENCE_SAMPLES",
    "BLOCKED_GENERATION_NOT_RUN",
    "BLOCKED_GENERATION_INCOMPLETE",
    "BLOCKED_GENERATION_MANIFEST_INVALID",
    "READY_FOR_KAGGLE_FEATURE_EXTRACTION",
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


def run_audit(*, out: str | Path, json_out: str | Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def add(name: str, passed: bool, detail: Any) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    policy = Path("docs/R1A_CIFAR10_SAMPLE_MATERIALIZATION_POLICY.md")
    policy_text = _read(policy) if policy.exists() else ""
    add(
        "r1a_policy_doc_exists",
        policy.exists() and "sample-package artifacts, not paper evidence" in policy_text,
        str(policy),
    )

    ref_doc = Path("docs/CIFAR10_REFERENCE_MATERIALIZATION_R1A.md")
    ref_text = _read(ref_doc) if ref_doc.exists() else ""
    add(
        "cifar10_reference_materialization_doc_exists",
        ref_doc.exists() and "license_unknown_reference_only" in ref_text and "train: 50,000" in ref_text,
        str(ref_doc),
    )

    add(
        "reference_manifest_builder_exists",
        Path("certgen/data/build_cifar10_reference_manifest.py").exists(),
        "python -m certgen.data.build_cifar10_reference_manifest",
    )

    runbook = Path("docs/KAGGLE_T4X2_CIFAR10_GENERATION_R1A.md")
    runbook_text = _read(runbook) if runbook.exists() else ""
    add(
        "kaggle_generation_runbook_exists",
        runbook.exists()
        and "google/ddpm-cifar10-32" in runbook_text
        and "FrankCCCCC/ddpm_ema_cifar10" in runbook_text
        and "FrankCCCCC/cfm-cifar10-32" in runbook_text
        and "--execute" in runbook_text,
        str(runbook),
    )

    adapters = checkpoint_adapter_statuses()
    adapter_ok = all(str(item.get("adapter_status", "")).startswith("ready_guarded") for item in adapters.values())
    add("generation_adapter_exists_or_blocked_status_documented", adapter_ok, adapters)

    add(
        "manifest_merge_tool_exists",
        Path("certgen/generation/merge_sample_manifests.py").exists(),
        "python -m certgen.generation.merge_sample_manifests",
    )

    runtime_doc = Path("docs/R1A_CIFAR10_GENERATION_RUNTIME_ESTIMATES.md")
    runtime_text = _read(runtime_doc) if runtime_doc.exists() else ""
    add(
        "runtime_estimates_exist_and_are_planning_only",
        runtime_doc.exists() and "planning estimates only, not empirical project results" in runtime_text,
        str(runtime_doc),
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
    readiness_text = _read("docs/R1_CIFAR10_REAL_PILOT_READINESS.md")
    add(
        "r1_readiness_report_has_updated_blocker_taxonomy",
        all(token in readiness_text for token in REQUIRED_TAXONOMY),
        r1.get("status_code"),
    )

    claim_offenders = _claim_allowed_true_artifacts()
    add("no_claim_allowed_true", not claim_offenders, claim_offenders or "no claim_allowed=true JSON artifacts")

    fake_result_issues = []
    if "measured result" in runtime_text.lower() and "not empirical project results" not in runtime_text.lower():
        fake_result_issues.append(str(runtime_doc))
    add("no_fake_empirical_results", not fake_result_issues, fake_result_issues or "planning-only language present")

    r1a_certificate_files = [str(path) for path in Path("data/results").glob("r1a*certificate*")]
    add("no_certificate_run_performed_for_r1a", not r1a_certificate_files, r1a_certificate_files or "no R1A certificate artifacts")

    samples_missing = not r1.get("sample_materialization", {}).get("reference_materialized") or not r1.get("sample_materialization", {}).get("generated_samples_materialized")
    add(
        "no_feature_extraction_claimed_if_samples_missing",
        not (samples_missing and r1.get("kaggle_feature_extraction_ready")),
        {"samples_missing": samples_missing, "kaggle_feature_extraction_ready": r1.get("kaggle_feature_extraction_ready")},
    )

    passed = all(check["passed"] for check in checks)
    payload = {
        "audit_name": "r1a_sample_materialization_audit",
        "passed": passed,
        "checks_passed": sum(1 for check in checks if check["passed"]),
        "checks_total": len(checks),
        "checks": checks,
        "claim_allowed": False,
        "r1_status_code": r1.get("status_code"),
        "kaggle_generation_ready": adapter_ok,
        "kaggle_feature_extraction_ready": r1.get("kaggle_feature_extraction_ready"),
    }
    lines = [
        "# R1A Sample Materialization Audit",
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
    lines.extend(
        [
            "",
            "## R1 Status",
            "",
            f"- Status code: `{r1.get('status_code')}`",
            f"- Kaggle generation ready: `{adapter_ok}`",
            f"- Kaggle feature extraction ready: `{r1.get('kaggle_feature_extraction_ready')}`",
            "- No certificate run was performed.",
        ]
    )
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_json(payload, json_out)
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the R1A sample-materialization audit.")
    parser.add_argument("--out", required=True)
    parser.add_argument("--json-out", required=True)
    args = parser.parse_args(argv)
    payload = run_audit(out=args.out, json_out=args.json_out)
    print(f"R1A sample materialization audit: {'passed' if payload['passed'] else 'failed'}")
    return 0 if payload["passed"] else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
