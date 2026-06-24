"""CERTGEN_R0 technical correction audit."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any

import numpy as np

from certgen.certs.api import certify_clean_metric_comparison
from certgen.certs.multiple_comparisons import plan_e_bh
from certgen.core.io import write_json
from certgen.fixtures.make_v2_feature_fixtures import make_v2_feature_fixtures
from certgen.metrics.kernels import certified_kernel_bounds
from certgen.metrics.streams import mmd_difference_stream
from certgen.pipeline.cifar10_real_pilot import run_cifar10_r1_readiness
from certgen.stats.cs import confidence_sequence
from certgen.stats.design_contracts import CSConfig


DEFAULT_R1_COMMAND = (
    "python3 -m certgen.cli.run_cifar10_real_pilot "
    "--provenance-ledger registry/provenance/cifar10_r1_ledger.csv "
    "--sample-manifest registry/manifests/cifar10_r1_samples.jsonl "
    "--preprocessing-lock configs/preprocessing_locks/cifar10_inception_bilinear_299.json "
    "--feature-cache-dir data/features/cifar10_r1 "
    "--metric-reproduction-audit data/results/cifar10_r1_metric_reproduction.json "
    "--out-json data/results/r1_cifar10_status.json "
    "--report docs/R1_CIFAR10_REAL_PILOT_READINESS.md"
)


def _json_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return [path for path in root.rglob("*.json") if path.is_file()]


def _scan_claim_allowed_true() -> list[str]:
    offenders: list[str] = []
    for root in [Path("data"), Path("registry"), Path("release")]:
        for path in _json_files(root):
            try:
                text = path.read_text(encoding="utf-8", errors="ignore").lower()
            except OSError:
                continue
            if '"claim_allowed": true' in text:
                offenders.append(str(path))
    return offenders


def _scan_rigorous_fid_claims() -> list[str]:
    offenders: list[str] = []
    for path in _json_files(Path("data")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            continue
        stack = [payload]
        while stack:
            item = stack.pop()
            if isinstance(item, dict):
                metric = str(item.get("metric_label") or item.get("metric_name") or item.get("metric") or "").lower()
                theory = str(item.get("theory_status") or "").lower()
                decision = str(item.get("decision") or item.get("status") or "").lower()
                rigorous = bool(item.get("rigorous_anytime_certificate"))
                if ("fid" in metric or "fd_dinov2" in metric) and (rigorous or "rigorous" in theory or "certified" in decision):
                    offenders.append(str(path))
                stack.extend(item.values())
            elif isinstance(item, list):
                stack.extend(item)
    return sorted(set(offenders))


def _write_command_index(path: str | Path) -> None:
    lines = [
        "# R0 Command Index",
        "",
        "`NO_REAL_EVIDENCE`",
        "",
        "## Technical Audit",
        "",
        "`python3 -m certgen.cli.r0_technical_audit --out docs/R0_TECHNICAL_CORRECTION_REPORT.md --json-out data/results/r0_technical_correction_audit.json --command-index docs/R0_COMMAND_INDEX.md --r1-status-json data/results/r1_cifar10_status.json --r1-report docs/R1_CIFAR10_REAL_PILOT_READINESS.md`",
        "",
        "## CIFAR-10 R1 Readiness",
        "",
        f"`{DEFAULT_R1_COMMAND}`",
        "",
        "## Rigorous Certificate Template",
        "",
        "`python3 -m certgen.cli.certify_clean_metric --features-a <model_a_features.npz> --features-b <model_b_features.npz> --features-r <reference_features.npz> --metric mmd_rbf --comparison-id <comparison_id> --alpha 0.05 --budget-units <units> --method betting --block-size <units> --metric-reproduction-audit data/results/cifar10_r1_metric_reproduction.json --out data/results/certificates/<comparison_id>_mmd_rbf.json --evidence-status real_pilot_non_claim`",
        "",
        "Polynomial KID, FID, and FD-style metrics are descriptive-only in R0.",
        "",
    ]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def run_r0_technical_audit(
    *,
    out: str | Path,
    json_out: str | Path,
    command_index: str | Path,
    r1_status_json: str | Path,
    r1_report: str | Path,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def add(name: str, passed: bool, detail: Any) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    claim_offenders = _scan_claim_allowed_true()
    add("no_claim_allowed_true_artifacts", not claim_offenders, claim_offenders or "none")

    fid_offenders = _scan_rigorous_fid_claims()
    add("no_rigorous_fid_certificate_claim", not fid_offenders, fid_offenders or "none")

    try:
        with tempfile.TemporaryDirectory() as tmp:
            paths = make_v2_feature_fixtures(Path(tmp) / "features", seed=23)
            certify_clean_metric_comparison(
                paths["model_a_close"],
                paths["model_b_far"],
                paths["reference"],
                "kid_polynomial",
                {},
                {"alpha": 0.05, "budget_units": 4},
                "r0_kid_block",
                "smoke_only",
                str(Path(tmp) / "blocked_kid.json"),
            )
        kid_blocked = False
        kid_detail = "unexpectedly certified"
    except ValueError as exc:
        kid_blocked = "polynomial" in str(exc).lower()
        kid_detail = str(exc)
    add("polynomial_kid_not_certified_by_default", kid_blocked, kid_detail)

    try:
        r = np.tile(np.array([[1.0, 0.0]]), (24, 1))
        a = r + 0.01
        b = np.tile(np.array([[0.0, 1.0]]), (24, 1))
        stream = mmd_difference_stream(a, b, r, {"name": "rbf", "normalize": "l2"}, seed=0, block_size=3, metric_label="mmd_rbf")
        bounds = certified_kernel_bounds({"name": "rbf", "normalize": "l2"})
        values_in_bounds = all(stream.lower_bound <= value <= stream.upper_bound for value in stream.values)
        add("bounded_rbf_mmd_certificate_path_exists", stream.bounded and values_in_bounds and bounds["bounded_by_construction"], stream.metadata["boundedness_metadata"])
    except Exception as exc:
        add("bounded_rbf_mmd_certificate_path_exists", False, str(exc))

    try:
        cmmd_stream = mmd_difference_stream(a, b, r, {"name": "rbf", "normalize": "l2"}, seed=1, block_size=4, metric_label="cmmd_clip_mmd")
        add("bounded_cmmd_clip_mmd_path_exists", cmmd_stream.bounded and cmmd_stream.metric_label == "cmmd_clip_mmd", cmmd_stream.metadata["boundedness_metadata"])
    except Exception as exc:
        add("bounded_cmmd_clip_mmd_path_exists", False, str(exc))

    try:
        betting = confidence_sequence([-0.8] * 12, CSConfig(alpha=0.05, budget_units=12, lower_bound=-1.0, upper_bound=1.0, method="betting"))
        add("betting_cs_path_exists", betting.time_uniform and "betting" in betting.method_label, betting.method_label)
    except Exception as exc:
        add("betting_cs_path_exists", False, str(exc))

    try:
        ebh = plan_e_bh(0.05, 4)
        add("lightweight_e_bh_design_scaffold_exists", ebh["implemented_for_claims"] is False and ebh["claim_allowed"] is False, ebh)
    except Exception as exc:
        add("lightweight_e_bh_design_scaffold_exists", False, str(exc))

    r1 = run_cifar10_r1_readiness(
        provenance_ledger="registry/provenance/cifar10_r1_ledger.csv",
        sample_manifest="registry/manifests/cifar10_r1_samples.jsonl",
        preprocessing_lock="configs/preprocessing_locks/cifar10_inception_bilinear_299.json",
        feature_cache_dir="data/features/cifar10_r1",
        metric_reproduction_audit="data/results/cifar10_r1_metric_reproduction.json",
        out_json=r1_status_json,
        report=r1_report,
    )
    add("first_real_pilot_ready_or_blocked_with_exact_reason", r1["status"] in {"ready", "blocked"} and bool(r1["blockers"] or r1["ready_for_r1"]), r1["blockers"] or "ready")

    _write_command_index(command_index)
    add("updated_r0_command_index_written", Path(command_index).exists(), str(command_index))

    passed = all(check["passed"] for check in checks)
    payload = {
        "audit_name": "CERTGEN_R0_TECHNICAL_CORRECTION_AND_REAL_PILOT_PREP",
        "passed": passed,
        "checks": checks,
        "checks_passed": sum(1 for check in checks if check["passed"]),
        "checks_total": len(checks),
        "claim_allowed": False,
        "promote_to_paper_evidence": False,
        "r1_ready": r1["ready_for_r1"],
        "r1_status": r1["status"],
        "r1_blockers": r1["blockers"],
        "exact_next_command": r1["exact_next_command"],
    }
    lines = [
        "# CERTGEN_R0 Technical Correction Report",
        "",
        "`NO_REAL_EVIDENCE`",
        "",
        f"Audit status: `{'passed' if passed else 'failed'}`",
        f"Checks passed: `{payload['checks_passed']}/{payload['checks_total']}`",
        "Claim allowed: `False`",
        "Promote to paper evidence: `False`",
        "",
        "| Check | Status | Detail |",
        "|---|---:|---|",
    ]
    for check in checks:
        detail = str(check["detail"]).replace("|", "\\|").replace("\n", " ")
        lines.append(f"| `{check['name']}` | `{'pass' if check['passed'] else 'fail'}` | {detail} |")
    lines.extend(["", "## R1 CIFAR-10 Status", "", f"Status: `{r1['status']}`"])
    lines.extend(f"- {blocker}" for blocker in r1["blockers"] or ["none"])
    lines.extend(["", "## Exact Next Command", "", f"`{r1['exact_next_command']}`", ""])
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text("\n".join(lines), encoding="utf-8")
    write_json(payload, json_out)
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the CertGen R0 technical correction audit.")
    parser.add_argument("--out", default="docs/R0_TECHNICAL_CORRECTION_REPORT.md")
    parser.add_argument("--json-out", default="data/results/r0_technical_correction_audit.json")
    parser.add_argument("--command-index", default="docs/R0_COMMAND_INDEX.md")
    parser.add_argument("--r1-status-json", default="data/results/r1_cifar10_status.json")
    parser.add_argument("--r1-report", default="docs/R1_CIFAR10_REAL_PILOT_READINESS.md")
    args = parser.parse_args(argv)
    payload = run_r0_technical_audit(
        out=args.out,
        json_out=args.json_out,
        command_index=args.command_index,
        r1_status_json=args.r1_status_json,
        r1_report=args.r1_report,
    )
    print(f"R0 audit status: {'passed' if payload['passed'] else 'failed'}; R1 status: {payload['r1_status']}")
    return 0 if payload["passed"] else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
