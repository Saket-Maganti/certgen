"""R1B generation-package audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from certgen.core.io import read_json, write_json
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

    add(
        "reference_materialization_path_exists",
        Path("certgen/data/build_cifar10_reference_manifest.py").exists()
        and Path("registry/manifests/cifar10_r1_reference.jsonl").exists()
        and Path("data/results/r1b_cifar10_reference_summary.json").exists(),
        "reference builder, manifest path, and R1B reference summary",
    )
    add(
        "kaggle_1k_generation_command_exists",
        Path("commands/r1b_kaggle_generation/00_generate_1000_per_model_t4x2.sh").exists(),
        "commands/r1b_kaggle_generation/00_generate_1000_per_model_t4x2.sh",
    )
    add(
        "generated_manifest_validation_command_exists",
        Path("commands/r1b_cpu/01_validate_generated_manifests.sh").exists()
        and Path("certgen/generation/validate_cifar10_generated_pilot.py").exists(),
        "commands/r1b_cpu/01_validate_generated_manifests.sh",
    )
    add(
        "sample_package_builder_exists",
        Path("certgen/data/build_cifar10_r1_sample_package.py").exists(),
        "python -m certgen.data.build_cifar10_r1_sample_package",
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
    add("readiness_taxonomy_updated", all(token in readiness_text for token in REQUIRED_TAXONOMY), r1.get("status_code"))

    r1b_certificate_files = [str(path) for path in Path("data/results").glob("r1b*certificate*")]
    add("no_certificate_run", not r1b_certificate_files, r1b_certificate_files or "no R1B certificate artifacts")

    package_summary_path = Path("data/results/r1b_feature_extraction_package_summary.json")
    package_summary = read_json(package_summary_path) if package_summary_path.exists() else {"passed": False}
    add(
        "no_feature_extraction_claimed_unless_package_validates",
        package_summary.get("passed") is True or r1.get("kaggle_feature_extraction_ready") is False,
        {"package_passed": package_summary.get("passed"), "kaggle_feature_extraction_ready": r1.get("kaggle_feature_extraction_ready")},
    )

    add(
        "no_paper_evidence_promotion",
        package_summary.get("evidence_status") == "sample_package_only" and package_summary.get("claim_allowed") is False,
        package_summary.get("status_code"),
    )

    claim_offenders = _claim_allowed_true_artifacts()
    add("no_claim_allowed_true", not claim_offenders, claim_offenders or "no claim_allowed=true JSON artifacts")

    passed = all(check["passed"] for check in checks)
    payload = {
        "audit_name": "r1b_generation_package_audit",
        "passed": passed,
        "checks_passed": sum(1 for check in checks if check["passed"]),
        "checks_total": len(checks),
        "checks": checks,
        "claim_allowed": False,
        "r1_status_code": r1.get("status_code"),
        "reference_status": read_json("data/results/r1b_cifar10_reference_summary.json").get("status_code")
        if Path("data/results/r1b_cifar10_reference_summary.json").exists()
        else "missing",
        "generated_package_status": read_json("data/results/r1b_generated_manifest_summary.json").get("status_code")
        if Path("data/results/r1b_generated_manifest_summary.json").exists()
        else "missing",
        "kaggle_generation_command_ready": Path("commands/r1b_kaggle_generation/00_generate_1000_per_model_t4x2.sh").exists(),
        "kaggle_feature_extraction_ready": r1.get("kaggle_feature_extraction_ready"),
    }
    lines = [
        "# R1B Generation Package Audit",
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
            "## Current Status",
            "",
            f"- R1 status code: `{payload['r1_status_code']}`",
            f"- Reference status: `{payload['reference_status']}`",
            f"- Generated package status: `{payload['generated_package_status']}`",
            f"- Kaggle generation command ready: `{payload['kaggle_generation_command_ready']}`",
            f"- Kaggle feature extraction ready: `{payload['kaggle_feature_extraction_ready']}`",
            "- No certificate run was performed.",
        ]
    )
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_json(payload, json_out)
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the R1B generation-package audit.")
    parser.add_argument("--out", required=True)
    parser.add_argument("--json-out", required=True)
    args = parser.parse_args(argv)
    payload = run_audit(out=args.out, json_out=args.json_out)
    print(f"R1B generation package audit: {'passed' if payload['passed'] else 'failed'}")
    return 0 if payload["passed"] else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
