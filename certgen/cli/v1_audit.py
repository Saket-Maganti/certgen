"""Final V1 audit command."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np

from certgen import __version__
from certgen.certs.decision import make_decision_certificate
from certgen.cli.make_smoke_artifacts import create_smoke_artifacts
from certgen.cli.validate_config import load_config, validate_config
from certgen.core.enums import EvidenceStatus
from certgen.core.io import read_json, to_json_dict, write_json
from certgen.gates.claim_gate import scan_text_for_forbidden_claims
from certgen.gates.evidence_gate import contains_real_evidence_status, validate_evidence_status
from certgen.gates.fid_policy_gate import validate_fid_certificate_request
from certgen.metrics.fid import frechet_distance
from certgen.metrics.kid import kid_polynomial
from certgen.metrics.registry import metric_record_from_registry
from certgen.schemas.comparison import ComparisonRecord
from certgen.schemas.dataset import DatasetRecord


def _check_json_tree_for_real_status(root: Path) -> tuple[bool, str]:
    if not root.exists():
        return True, "data directory not present yet"
    offending = []
    for path in root.rglob("*.json"):
        try:
            data = read_json(path)
        except Exception as exc:
            offending.append(f"{path}: unreadable JSON ({exc})")
            continue
        if contains_real_evidence_status(data):
            offending.append(str(path))
    if offending:
        return False, "; ".join(offending)
    return True, "no generated JSON artifact uses real_evidence_candidate"


def _command_index_has_commands(path: Path) -> tuple[bool, str]:
    if not path.exists():
        return False, "COMMAND_INDEX_V1.md missing"
    text = path.read_text(encoding="utf-8")
    commands = [
        "python -m certgen.cli.validate_config",
        "python -m certgen.cli.make_smoke_artifacts",
        "python -m certgen.cli.validate_registry",
        "python -m certgen.cli.plan_first_pilot",
        "python -m certgen.cli.v1_audit",
    ]
    missing = [command for command in commands if command not in text]
    if missing:
        return False, "missing commands: " + ", ".join(missing)
    return True, "command index includes V1 commands"


def run_audit(*, out: str | Path, json_out: str | Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    try:
        import certgen

        add("package_imports", bool(certgen.__version__), f"certgen {__version__}")
    except Exception as exc:
        add("package_imports", False, str(exc))

    try:
        config = load_config("configs/certgen_v1_smoke.yaml")
        validate_config(config)
        add("smoke_config_validates", True, "configs/certgen_v1_smoke.yaml validates")
    except Exception as exc:
        config = {}
        add("smoke_config_validates", False, str(exc))

    try:
        record = DatasetRecord(
            dataset_id="smoke_dataset",
            name="Smoke Dataset",
            split="toy",
            source_url_or_note="generated toy arrays",
            license_note="not applicable",
            num_items_declared=4,
            evidence_status=EvidenceStatus.NON_EVIDENCE_SMOKE.value,
            provenance_hash="abc123",
        )
        serialized = to_json_dict(record)
        add("schemas_serialize", serialized["dataset_id"] == "smoke_dataset", "DatasetRecord serializes to JSON dict")
    except Exception as exc:
        add("schemas_serialize", False, str(exc))

    try:
        decision = validate_evidence_status(EvidenceStatus.REAL_EVIDENCE_CANDIDATE.value, mode="smoke")
        add("evidence_statuses_enforced", not decision.passed, decision.reason)
    except Exception as exc:
        add("evidence_statuses_enforced", False, str(exc))

    try:
        decision = scan_text_for_forbidden_claims("we find that model A beats model B", evidence_status="non_evidence_smoke")
        add("claim_gate_catches_forbidden_phrases", not decision.passed, decision.reason)
    except Exception as exc:
        add("claim_gate_catches_forbidden_phrases", False, str(exc))

    try:
        fid_record = metric_record_from_registry("fid_inception")
        decision = validate_fid_certificate_request(fid_record, "clean_cs", "smoke")
        add("fid_policy_blocks_clean_cs", not decision.passed, decision.reason)
    except Exception as exc:
        add("fid_policy_blocks_clean_cs", False, str(exc))

    try:
        x = np.zeros((8, 4))
        y = np.ones((8, 4)) * 0.2
        kid_value = kid_polynomial(x, y)
        fid_value = frechet_distance(x, x)
        add("smoke_metrics_run", np.isfinite(kid_value) and abs(fid_value) < 1e-12, f"kid={kid_value:.6f}; fid_identical={fid_value:.6f}")
    except Exception as exc:
        add("smoke_metrics_run", False, str(exc))

    try:
        comparison = ComparisonRecord(
            comparison_id="audit_toy",
            dataset_id="toy",
            model_a_id="a",
            model_b_id="b",
            reference_id="r",
            metric_name="mmd_rbf",
            alpha=0.05,
            max_samples=64,
            evidence_status=EvidenceStatus.NON_EVIDENCE_SMOKE.value,
        )
        cert = make_decision_certificate(
            comparison,
            [-0.95] * 64,
            0.05,
            64,
            metric_record_from_registry("mmd_rbf"),
            EvidenceStatus.NON_EVIDENCE_SMOKE.value,
        )
        add("clean_core_certificate_runs", cert.status == "certified_a_better", f"status={cert.status}")
    except Exception as exc:
        add("clean_core_certificate_runs", False, str(exc))

    try:
        create_smoke_artifacts(
            config_path="configs/certgen_v1_smoke.yaml",
            out_dir="data/smoke/v1",
            compute_metrics=True,
            make_certificate=True,
        )
        report = Path("data/smoke/v1/reports/smoke_certificate_report.md").read_text(encoding="utf-8")
        decision = scan_text_for_forbidden_claims(report, evidence_status="non_evidence_smoke")
        add("reports_pass_claim_gate", decision.passed, decision.reason)
    except Exception as exc:
        add("reports_pass_claim_gate", False, str(exc))

    no_results = Path("docs/NO_RESULTS_YET.md")
    add("no_results_doc_exists", no_results.exists(), str(no_results))

    registry_paths = [
        Path("registry/candidate_benchmarks_template.csv"),
        Path("registry/candidate_model_pairs_template.csv"),
        Path("registry/audit_claims_template.csv"),
    ]
    add("registry_templates_exist", all(path.exists() for path in registry_paths), ", ".join(str(path) for path in registry_paths))

    try:
        ok, detail = _check_json_tree_for_real_status(Path("data"))
        add("no_generated_artifact_marked_real_status", ok, detail)
    except Exception as exc:
        add("no_generated_artifact_marked_real_status", False, str(exc))

    try:
        risky_phrases = ["published wins are undecided", "ranking changes after valid testing"]
        checked_docs = [Path("docs/NO_RESULTS_YET.md"), Path("docs/FIRST_PILOT_PLAN.md")]
        offenders = []
        for path in checked_docs:
            if path.exists():
                lowered = path.read_text(encoding="utf-8").lower()
                offenders.extend(f"{path}: {phrase}" for phrase in risky_phrases if phrase in lowered)
        add("docs_do_not_claim_audit_findings", not offenders, "; ".join(offenders) if offenders else "selected docs are claim-safe")
    except Exception as exc:
        add("docs_do_not_claim_audit_findings", False, str(exc))

    ok, detail = _command_index_has_commands(Path("docs/COMMAND_INDEX_V1.md"))
    add("command_index_exists", ok, detail)

    try:
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q"],
            cwd=Path.cwd(),
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=180,
            check=False,
        )
        add("pytest_passes", result.returncode == 0, result.stdout.strip().splitlines()[-1] if result.stdout.strip() else "no pytest output")
    except Exception as exc:
        add("pytest_passes", False, str(exc))

    status = "passed" if all(check["passed"] for check in checks) else "failed"
    payload = {"audit_status": status, "checks": checks}

    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# CertGen V1 Final Audit",
        "",
        f"Audit status: `{status}`",
        "",
        "| Check | Status | Detail |",
        "|---|---:|---|",
    ]
    for check in checks:
        lines.append(f"| `{check['name']}` | `{'pass' if check['passed'] else 'fail'}` | {check['detail']} |")
    lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")

    write_json(payload, json_out)
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the CertGen V1 final audit.")
    parser.add_argument("--out", required=True)
    parser.add_argument("--json-out", required=True)
    args = parser.parse_args(argv)
    payload = run_audit(out=args.out, json_out=args.json_out)
    print(f"V1 audit status: {payload['audit_status']}")
    return 0 if payload["audit_status"] == "passed" else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
