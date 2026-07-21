"""V5 state intake and gap audit."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from certgen.core.io import read_json, write_json


CRITICAL_V4_FILES = [
    "docs/V4_FINAL_AUDIT.md",
    "data/results/v4_final_audit.json",
    "docs/V4_SINGLE_FILE_HANDOFF.md",
    "docs/COMMAND_INDEX_V4.md",
]

CVPR_READY_ITEMS = {
    "paper_identity": "docs/paper/CVPR_PAPER_IDENTITY.md",
    "claim_contract": "data/contracts/claim_contract_v5.json",
    "related_work_board": "registry/related_work/related_work_board_v5.csv",
    "analysis_plan_lock": "data/contracts/analysis_plan_lock_v5.json",
    "result_contracts": "data/contracts/result_contracts_v5.json",
    "main_paper_scaffold": "paper/sections/00_abstract.tex",
    "supplement_scaffold": "paper/supplement.tex",
    "reproducibility_capsule": "docs/reproducibility/REPRODUCIBILITY_CAPSULE_V5.md",
    "command_bundle": "commands/v5/00_validate_state.sh",
    "result_injection_contract": "data/contracts/result_injection_contract_v5.json",
    "reviewer_harness": "docs/review/REVIEWER_ATTACKS_V5.md",
    "cvpr_scorecard": "data/results/cvpr_readiness_scorecard_v5.json",
}


def _timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _scan_claim_boundary(root: Path) -> tuple[str, list[str]]:
    offenders: list[str] = []
    for base in [root / "data/smoke", root / "data/results"]:
        if not base.exists():
            continue
        for path in base.glob("**/*.json"):
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
            if '"claim_allowed": true' in text:
                offenders.append(f"unsupported claim_allowed=true: {path}")
            if '"evidence_status": "claim_eligible"' in text and "real" not in str(path):
                offenders.append(f"claim_eligible outside real gate: {path}")
    return ("failed" if offenders else "clean"), offenders


def _run_tests(root: Path) -> tuple[str, str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["CERTGEN_SKIP_V2_AUDIT_TEST"] = "1"
    env["CERTGEN_SKIP_V3_AUDIT_TEST"] = "1"
    env["CERTGEN_SKIP_V4_AUDIT_TEST"] = "1"
    env["CERTGEN_SKIP_V5_AUDIT_TEST"] = "1"
    result = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=root, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=300)
    detail = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else "no pytest output"
    return ("passed" if result.returncode == 0 else "failed"), detail


def run_v5_state_intake(root: str | Path = ".", *, run_tests: bool = False) -> dict[str, Any]:
    root = Path(root)
    checks: list[dict[str, Any]] = []
    blockers: list[str] = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})
        if not passed:
            blockers.append(f"{name}: {detail}")

    for item in CRITICAL_V4_FILES:
        add(f"exists_{item}", (root / item).exists(), item)

    v4_json = root / "data/results/v4_final_audit.json"
    v4_detected = v4_json.exists()
    v4_audit_passed = False
    v4_warnings: list[str] = []
    if v4_json.exists():
        try:
            v4_payload = read_json(v4_json)
            v4_audit_passed = bool(v4_payload.get("passed"))
            v4_warnings = list(v4_payload.get("warnings", []))
            add("v4_audit_passed", v4_audit_passed, "data/results/v4_final_audit.json")
            add("v4_unknown_license_warning_documented", any("unknown license" in w.lower() for w in v4_warnings), "unknown-license template warning is explicit")
        except Exception as exc:
            add("v4_audit_passed", False, str(exc))
    else:
        add("v4_audit_passed", False, "missing v4 audit json")

    claim_boundary_status, claim_offenders = _scan_claim_boundary(root)
    add("claim_boundary_clean", claim_boundary_status == "clean", "; ".join(claim_offenders) or "clean")

    try:
        import certgen

        add("core_package_imports", bool(certgen.__version__), certgen.__version__)
    except Exception as exc:
        add("core_package_imports", False, str(exc))

    tests_status = "not_run"
    tests_detail = "not requested"
    if run_tests:
        tests_status, tests_detail = _run_tests(root)
        add("pytest_command_works", tests_status == "passed", tests_detail)
    else:
        add("pytest_command_works", True, "not_run in intake; final audit runs tests")

    missing = [key for key, rel in CVPR_READY_ITEMS.items() if not (root / rel).exists()]
    required_actions = [f"add_{key}" for key in missing]
    add("v5_worklist_emitted", bool(required_actions) or not missing, ", ".join(required_actions) or "complete")

    payload = {
        "v5_state_intake_version": "0.5.0",
        "timestamp_utc": _timestamp(),
        "v4_detected": v4_detected,
        "v4_audit_passed": v4_audit_passed,
        "tests_status": tests_status,
        "tests_detail": tests_detail,
        "claim_boundary_status": claim_boundary_status,
        "claim_boundary_issues": claim_offenders,
        "missing_cvpr_ready_items": missing,
        "required_v5_actions": required_actions,
        "checks": checks,
        "blockers": blockers,
        "passed": not blockers,
        "claim_allowed": False,
        "evidence_status": "dry_run_only",
    }
    return payload


def write_v5_state_intake(out: str | Path, json_out: str | Path, *, root: str | Path = ".", run_tests: bool = False) -> dict[str, Any]:
    payload = run_v5_state_intake(root, run_tests=run_tests)
    lines = [
        "# V5 State Intake",
        "",
        "`NO_REAL_EVIDENCE`",
        "",
        f"Passed: `{payload['passed']}`",
        f"V4 detected: `{payload['v4_detected']}`",
        f"V4 audit passed: `{payload['v4_audit_passed']}`",
        f"Claim boundary: `{payload['claim_boundary_status']}`",
        f"Tests status: `{payload['tests_status']}`",
        "",
        "## Missing CVPR-Ready Items",
    ]
    lines.extend(f"- {item}" for item in payload["missing_cvpr_ready_items"] or ["none"])
    lines.extend(["", "## Required V5 Actions"])
    lines.extend(f"- {item}" for item in payload["required_v5_actions"] or ["none"])
    lines.extend(["", "## Checks", "", "| Check | Status | Detail |", "|---|---:|---|"])
    for check in payload["checks"]:
        lines.append(f"| `{check['name']}` | `{'pass' if check['passed'] else 'fail'}` | {check['detail']} |")
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_json(payload, json_out)
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run V5 state intake audit.")
    parser.add_argument("--out", required=True)
    parser.add_argument("--json-out", required=True)
    parser.add_argument("--run-tests", action="store_true")
    args = parser.parse_args(argv)
    payload = write_v5_state_intake(args.out, args.json_out, run_tests=args.run_tests)
    print(f"V5 state intake: {'passed' if payload['passed'] else 'failed'}")
    return 0 if payload["passed"] else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
