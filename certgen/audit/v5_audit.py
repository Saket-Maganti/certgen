"""CertGen V5 final audit."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from certgen.audit.analysis_plan_audit import audit_analysis_plan_lock
from certgen.audit.claim_contract import audit_claim_contract
from certgen.audit.claim_trace_audit_v5 import audit_claim_trace_v5
from certgen.audit.cvpr_readiness import write_cvpr_readiness
from certgen.audit.paper_scaffold_audit import audit_paper_scaffold
from certgen.audit.proof_obligation_audit import audit_proof_obligations
from certgen.audit.related_work_audit import audit_related_work_board
from certgen.audit.release_safety_v5 import write_release_safety_v5
from certgen.audit.result_contract_audit import audit_result_contracts
from certgen.audit.reviewer_harness_audit import audit_reviewer_harness
from certgen.audit.v5_state_intake import write_v5_state_intake
from certgen.commands.generate_v5_command_bundle import generate_v5_command_bundle
from certgen.core.io import write_json
from certgen.reporting.result_contracts import PLACEHOLDER_TOKEN


FINAL_VERDICT = (
    "CertGen is now CVPR-ready-except-runs: the codebase, paper scaffold, result contracts, "
    "claim gates, reproducibility capsule, and reviewer defenses are prepared. It is not "
    "CVPR-submission-ready because no real claim-eligible empirical audit has been executed. "
    "The next step is real execution: populate one provenance ledger, validate/materialize "
    "real feature caches, reproduce one metric point estimate, run the first real clean-core "
    "pilot in non-claim mode, and only then evaluate the first-benchmark undecided fraction."
)


def _md(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _run_pytest() -> tuple[bool, str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["CERTGEN_SKIP_V2_AUDIT_TEST"] = "1"
    env["CERTGEN_SKIP_V3_AUDIT_TEST"] = "1"
    env["CERTGEN_SKIP_V4_AUDIT_TEST"] = "1"
    env["CERTGEN_SKIP_V5_AUDIT_TEST"] = "1"
    result = subprocess.run([sys.executable, "-m", "pytest", "-q"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env, timeout=300)
    detail = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else "no pytest output"
    return result.returncode == 0, detail


def _scan_nonclaim_trees() -> list[str]:
    offenders: list[str] = []
    for base in [Path("data/smoke"), Path("data/results")]:
        if not base.exists():
            continue
        for path in base.glob("**/*.json"):
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
            if '"claim_allowed": true' in text:
                offenders.append(f"claim_allowed=true: {path}")
            if '"evidence_status": "claim_eligible"' in text:
                offenders.append(f"claim_eligible present: {path}")
    return offenders


def run_v5_final_audit(*, out: str | Path, json_out: str | Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    blockers: list[str] = []
    warnings: list[str] = []

    def add(name: str, passed: bool, detail: object) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})
        if not passed:
            blockers.append(f"{name}: {detail}")

    try:
        import certgen

        add("package_imports_as_v5", certgen.__version__.startswith("0.5."), certgen.__version__)
    except Exception as exc:
        add("package_imports_as_v5", False, exc)

    state = write_v5_state_intake("docs/V5_STATE_INTAKE.md", "data/results/v5_state_intake.json", run_tests=False)
    add("v5_state_intake_exists", state["passed"], f"missing={len(state['missing_cvpr_ready_items'])}")

    tests_ok, tests_detail = _run_pytest()
    add("all_tests_pass_or_recorded", tests_ok, tests_detail)

    add("claim_contract_exists", Path("data/contracts/claim_contract_v5.json").exists() and Path("docs/paper/CLAIM_CONTRACT.md").exists(), "claim contract files")
    claim_audit = audit_claim_contract()
    write_json(claim_audit, "data/results/v5_claim_contract_audit.json")
    add("forbidden_claims_audit_passes", claim_audit["passed"], claim_audit["errors"] or "passed")

    rw = audit_related_work_board()
    write_json(rw, "data/results/v5_related_work_audit.json")
    add("related_work_board_exists", Path("registry/related_work/related_work_board_v5.csv").exists() and rw["passed"], rw["errors"] or "passed")
    board_text = Path("registry/related_work/related_work_board_v5.csv").read_text(encoding="utf-8", errors="ignore") if Path("registry/related_work/related_work_board_v5.csv").exists() else ""
    add("related_work_unverified_marked", "needs_verification" in board_text and "verified,true" not in board_text.lower(), "unverified citations marked")

    analysis = audit_analysis_plan_lock()
    add("analysis_plan_lock_exists", Path("data/contracts/analysis_plan_lock_v5.json").exists() and analysis["passed"], analysis["errors"] or "passed")
    add("analysis_plan_hash_exists", Path("data/results/analysis_plan_lock_hash_v5.txt").exists(), "analysis hash")

    result_contracts = audit_result_contracts()
    add("result_contracts_exist", Path("data/contracts/result_contracts_v5.json").exists() and result_contracts["passed"], result_contracts["errors"] or "passed")
    add("table_manifest_exists", Path("docs/paper/TABLE_MANIFEST_V5.md").exists(), "docs/paper/TABLE_MANIFEST_V5.md")
    add("figure_manifest_exists", Path("docs/paper/FIGURE_MANIFEST_V5.md").exists(), "docs/paper/FIGURE_MANIFEST_V5.md")

    paper = audit_paper_scaffold()
    add("main_paper_scaffold_exists", paper["passed"], paper["errors"] or "passed")
    results_text = Path("paper/sections/05_results_placeholder.tex").read_text(encoding="utf-8", errors="ignore") if Path("paper/sections/05_results_placeholder.tex").exists() else ""
    add("results_section_placeholders_only", PLACEHOLDER_TOKEN in results_text and "claim_allowed=true" not in results_text.lower(), "placeholder results section")

    proof = audit_proof_obligations()
    add("supplement_scaffold_exists", Path("paper/supplement.tex").exists() and proof["passed"], proof["errors"] or "passed")
    add("proof_obligation_tracker_exists", Path("docs/paper/PROOF_OBLIGATION_TRACKER.md").exists() and Path("data/contracts/proof_obligations_v5.json").exists(), "proof tracker")

    fid_text = Path("paper/supplement/05_fid_fd_policy.tex").read_text(encoding="utf-8", errors="ignore").lower() if Path("paper/supplement/05_fid_fd_policy.tex").exists() else ""
    add("fid_fd_policy_exists_and_enforced", "descriptive" in fid_text and "does not directly certify fid" in fid_text, "FID/FD policy caveat")

    add("reproducibility_capsule_exists", Path("docs/reproducibility/REPRODUCIBILITY_CAPSULE_V5.md").exists(), "reproducibility docs")
    release = write_release_safety_v5()
    add("release_anonymity_scan_passes", release["passed"], release["issues"] or "passed")

    generate_v5_command_bundle()
    add("v5_command_bundle_exists", all(Path(f"commands/v5/{idx:02d}_{name}.sh").exists() for idx, name in [
        (0, "validate_state"),
        (1, "validate_provenance_ledger"),
        (2, "validate_or_materialize_feature_caches"),
        (3, "reproduce_metric_point_estimate"),
        (4, "run_first_clean_core_pilot_nonclaim"),
        (5, "render_pilot_report_card_nonclaim"),
        (6, "v5_final_audit"),
    ]), "commands/v5")

    trace = audit_claim_trace_v5()
    add("result_injection_protocol_exists", Path("docs/paper/RESULT_INJECTION_PROTOCOL.md").exists() and trace["passed"], trace["errors"] or "passed")
    add("claim_trace_protocol_exists", Path("docs/paper/CLAIM_TRACE_PROTOCOL.md").exists(), "docs/paper/CLAIM_TRACE_PROTOCOL.md")

    reviewer = audit_reviewer_harness()
    write_json(reviewer, "data/results/v5_reviewer_harness.json")
    add("reviewer_attack_harness_exists", Path("docs/review/REVIEWER_ATTACKS_V5.md").exists() and reviewer["passed"], reviewer["errors"] or "passed")
    add("author_response_bank_exists", Path("docs/review/AUTHOR_RESPONSE_BANK_V5.md").exists(), "docs/review/AUTHOR_RESPONSE_BANK_V5.md")

    readiness = write_cvpr_readiness()
    add("cvpr_readiness_scorecard_exists", Path("docs/CVPR_READINESS_SCORECARD_V5.md").exists() and readiness["passed"], readiness["errors"] or "passed")
    add("kill_list_exists", Path("docs/CVPR_KILL_LIST_V5.md").exists() and len(readiness["kill_list"]) >= 10, "kill list")

    offenders = _scan_nonclaim_trees()
    add("no_fake_real_evidence_exists", not offenders and claim_audit["passed"], offenders or "clean")
    add("no_claim_allowed_true_for_non_evidence", not offenders, offenders or "clean")

    handoff = Path("docs/V5_SINGLE_FILE_HANDOFF.md")
    add("v5_handoff_exists", handoff.exists() and FINAL_VERDICT in handoff.read_text(encoding="utf-8", errors="ignore"), "docs/V5_SINGLE_FILE_HANDOFF.md")
    add("v5_command_index_exists", Path("docs/COMMAND_INDEX_V5.md").exists(), "docs/COMMAND_INDEX_V5.md")
    stop = Path("docs/V5_STOP_CONDITION.md")
    stop_text = stop.read_text(encoding="utf-8", errors="ignore").lower() if stop.exists() else ""
    add("stop_condition_real_execution_not_v6", "real execution" in stop_text and "not v6 infrastructure" in stop_text, "docs/V5_STOP_CONDITION.md")
    add("audit_has_at_least_30_checks", len(checks) + 1 >= 30, f"{len(checks) + 1} checks")

    passed = not blockers
    payload = {
        "audit_name": "v5_final_audit",
        "passed": passed,
        "checks_passed": sum(1 for check in checks if check["passed"]),
        "checks_total": len(checks),
        "checks": checks,
        "blockers": blockers,
        "warnings": warnings,
        "claim_allowed": False,
        "evidence_status": "template_only",
        "final_verdict": FINAL_VERDICT,
        "next_action": "real execution: populate one provenance ledger, validate/materialize real feature caches, reproduce one metric point estimate, and run the first real clean-core pilot in non-claim mode",
    }
    lines = [
        "# CertGen V5 Final Audit",
        "",
        f"Summary: `{'passed' if passed else 'failed'}`",
        "",
        "`NO_REAL_EVIDENCE`",
        "",
        f"Checks passed: `{payload['checks_passed']}/{payload['checks_total']}`",
        "Claim allowed: `false`",
        "Evidence status: `template_only`",
        "",
        "| Check | Status | Detail |",
        "|---|---:|---|",
    ]
    for check in checks:
        lines.append(f"| `{check['name']}` | `{'pass' if check['passed'] else 'fail'}` | {_md(check['detail'])} |")
    lines.extend(["", "## Blockers"])
    lines.extend(f"- {blocker}" for blocker in blockers or ["none"])
    lines.extend(["", "## Final Verdict", "", FINAL_VERDICT, ""])
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text("\n".join(lines), encoding="utf-8")
    write_json(payload, json_out)
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run CertGen V5 final audit.")
    parser.add_argument("--out", required=True)
    parser.add_argument("--json-out", required=True)
    args = parser.parse_args(argv)
    payload = run_v5_final_audit(out=args.out, json_out=args.json_out)
    print(f"V5 audit status: {'passed' if payload['passed'] else 'failed'}")
    return 0 if payload["passed"] else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
