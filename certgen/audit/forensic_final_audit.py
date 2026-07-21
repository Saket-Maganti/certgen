"""Consolidated, non-empirical coherence audit for the forensic handoff."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from certgen.core.io import write_json


TOP_LEVEL_STATUSES = {
    "FORENSIC_AUDIT_FAILED_REPOSITORY_INCONSISTENT",
    "REPAIRS_COMPLETED_TESTS_FAILING",
    "LOCAL_RESEARCH_CORE_VALID_BLOCKED_BY_THEORY",
    "LOCAL_RESEARCH_CORE_VALID_BLOCKED_BY_REFERENCE_INPUT",
    "READY_FOR_CHECKPOINT_PREFLIGHT",
    "READY_FOR_1K_GENERATION",
    "READY_FOR_FEATURE_EXTRACTION",
    "READY_FOR_METRIC_SANITY",
    "READY_FOR_FIRST_CERTIFICATE_PILOT",
    "FIRST_PILOT_EXISTS_NOT_PAPER_READY",
    "PAPER_EVIDENCE_EXISTS_NEEDS_BREADTH",
    "SUBMISSION_DRAFT_READY",
}

REQUIRED_ARTIFACTS = [
    "CERTGEN_FORENSIC_AUDIT_AND_MAXIMUM_CEILING_REPORT.md",
    "reports/CERTGEN_BASELINE_REPRODUCTION.md",
    "reports/CERTGEN_COMMAND_LEDGER.csv",
    "reports/CERTGEN_CURRENT_STATE.json",
    "reports/CERTGEN_CLAIM_EVIDENCE_LEDGER.csv",
    "reports/CERTGEN_EVIDENCE_BOUNDARY_AUDIT.md",
    "reports/CERTGEN_REPAIR_CHANGELOG.md",
    "reports/CERTGEN_REMAINING_WORK_PRIORITIZED.md",
    "docs/CERTGEN_EXECUTION_CRITICAL_PATH.md",
    "docs/CERTGEN_EXACT_NEXT_ACTION.md",
    "docs/CERTGEN_MAXIMUM_RESEARCH_CEILING.md",
    "docs/CERTGEN_SINGLE_FILE_HANDOFF.md",
    "docs/theory/CERTGEN_STATISTICAL_VALIDITY_AUDIT.md",
    "docs/theory/CERTGEN_FORMAL_ESTIMAND_AND_STREAM.md",
    "docs/theory/CERTGEN_ASSUMPTION_LEDGER.csv",
    "docs/theory/CERTGEN_METRIC_CAPABILITY_REGISTRY.csv",
    "docs/theory/CERTGEN_MULTIPLICITY_PROTOCOL.md",
    "docs/theory/CERTGEN_THEOREM_AND_PROOF_OBLIGATIONS.md",
    "docs/metrics/CERTGEN_FEATURE_PIPELINE_AUDIT.md",
    "docs/metrics/CERTGEN_METRIC_REPRODUCTION_PROTOCOL.md",
    "docs/research/CERTGEN_NOVELTY_FORENSIC_AUDIT.md",
    "docs/research/CERTGEN_CLOSEST_WORK_MATRIX.csv",
    "docs/research/CERTGEN_CLAIM_AND_CONTRIBUTION_CONTRACT.md",
    "docs/experiments/CERTGEN_PREREGISTRATION_PROTOCOL.md",
    "docs/engineering/CERTGEN_ARCHITECTURE_AUDIT.md",
    "docs/execution/CERTGEN_KAGGLE_NOTEBOOK_FORENSIC_AUDIT.md",
    "paper/CERTGEN_PAPER_REDESIGN_PLAN.md",
    "paper/CERTGEN_REVIEWER_SIMULATION.md",
    "paper/CERTGEN_VENUE_CEILING_MATRIX.md",
    "release/CERTGEN_PUBLIC_RELEASE_MANIFEST.txt",
    "release/CERTGEN_INTERNAL_ARCHIVE_CANDIDATES.txt",
]


def _has_claim_true(value: Any) -> bool:
    if isinstance(value, dict):
        return any(
            (key == "claim_allowed" and item is True) or _has_claim_true(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_has_claim_true(item) for item in value)
    return False


def _claim_true_json_paths(root: Path) -> list[str]:
    hits: list[str] = []
    for base_name in ["data", "reports", "release"]:
        base = root / base_name
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix not in {".json", ".jsonl"}:
                continue
            values: list[Any] = []
            try:
                if path.suffix == ".json":
                    values = [json.loads(path.read_text(encoding="utf-8"))]
                else:
                    values = [
                        json.loads(line)
                        for line in path.read_text(encoding="utf-8").splitlines()
                        if line.strip()
                    ]
            except (OSError, json.JSONDecodeError):
                continue
            if any(_has_claim_true(value) for value in values):
                hits.append(str(path.relative_to(root)))
    return sorted(hits)


def _metric_registry_errors(path: Path) -> list[str]:
    if not path.exists():
        return [f"metric capability registry missing: {path}"]
    errors: list[str] = []
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        return ["metric capability registry is empty"]
    for row in rows:
        metric = str(row.get("metric", "")).lower()
        anytime = str(row.get("anytime_certificate_supported", "")).lower()
        paper = str(row.get("paper_claim_status", "")).lower()
        if ("fid" in metric or "polynomial" in metric or "kid" in metric) and anytime in {
            "true",
            "yes",
            "supported",
        }:
            errors.append(f"unsupported anytime capability in registry: {metric}")
        if ("fid" in metric or "polynomial" in metric) and paper in {
            "allowed",
            "claim_allowed",
            "supported",
        }:
            errors.append(f"unsupported paper capability in registry: {metric}")
    return errors


def run_forensic_audit(root: str | Path = ".") -> dict[str, Any]:
    root = Path(root).resolve()
    checks: list[dict[str, Any]] = []

    def add(name: str, passed: bool, detail: Any) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    missing = [path for path in REQUIRED_ARTIFACTS if not (root / path).is_file()]
    add("required_consolidated_artifacts_exist", not missing, missing or "all present")

    claim_hits = _claim_true_json_paths(root)
    add("no_machine_readable_claim_allowed_true", not claim_hits, claim_hits or "none")

    state_path = root / "reports/CERTGEN_CURRENT_STATE.json"
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        state = {}
        add("current_state_is_valid_json", False, str(exc))
    else:
        add("current_state_is_valid_json", True, str(state_path.relative_to(root)))
    add(
        "one_recognized_top_level_status",
        state.get("top_level_status") in TOP_LEVEL_STATUSES,
        state.get("top_level_status"),
    )
    add("current_state_blocks_empirical_claims", state.get("claim_allowed") is False, state.get("claim_allowed"))

    action = state.get("exact_next_action") if isinstance(state, dict) else None
    action_ok = isinstance(action, dict) and bool(action.get("action")) and bool(action.get("exact_command"))
    add("singular_executable_next_action", action_ok, action or "missing")

    metric_errors = _metric_registry_errors(root / "docs/theory/CERTGEN_METRIC_CAPABILITY_REGISTRY.csv")
    add("metric_capability_boundary_is_conservative", not metric_errors, metric_errors or "passed")

    ledger_path = root / "reports/CERTGEN_CLAIM_EVIDENCE_LEDGER.csv"
    ledger_errors: list[str] = []
    if ledger_path.exists():
        with ledger_path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        for index, row in enumerate(rows, start=2):
            if str(row.get("claim_allowed", "")).lower() in {"true", "yes", "1"}:
                ledger_errors.append(f"line {index}: claim_allowed is true")
    else:
        ledger_errors.append("claim evidence ledger missing")
    add("claim_evidence_ledger_has_no_promoted_claim", not ledger_errors, ledger_errors or "passed")

    passed = all(check["passed"] for check in checks)
    return {
        "audit_name": "CERTGEN_FORENSIC_REPOSITORY_COHERENCE_AUDIT",
        "passed": passed,
        "checks_passed": sum(check["passed"] for check in checks),
        "checks_total": len(checks),
        "checks": checks,
        "project_status": state.get("top_level_status"),
        "claim_allowed": False,
        "audit_is_empirical_evidence": False,
    }


def write_report(payload: dict[str, Any], path: str | Path) -> None:
    lines = [
        "# CertGen Forensic Repository Coherence Audit",
        "",
        "This is a repository-integrity audit, not empirical model evidence.",
        "",
        f"Passed: `{payload['passed']}`",
        f"Checks: `{payload['checks_passed']}/{payload['checks_total']}`",
        f"Project status: `{payload.get('project_status')}`",
        "Claim allowed: `false`",
        "",
        "| Check | Passed | Detail |",
        "|---|---:|---|",
    ]
    for check in payload["checks"]:
        detail = str(check["detail"]).replace("|", "\\|").replace("\n", " ")
        lines.append(f"| `{check['name']}` | `{check['passed']}` | {detail} |")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the consolidated CertGen forensic coherence audit.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--json-out", default="reports/CERTGEN_FORENSIC_MACHINE_AUDIT.json")
    parser.add_argument("--out", default="reports/CERTGEN_FORENSIC_MACHINE_AUDIT.md")
    args = parser.parse_args(argv)
    payload = run_forensic_audit(args.root)
    write_json(payload, args.json_out)
    write_report(payload, args.out)
    print(f"forensic_audit={payload['passed']} checks={payload['checks_passed']}/{payload['checks_total']}")
    return 0 if payload["passed"] else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
