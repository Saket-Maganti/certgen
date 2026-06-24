"""V5 CVPR readiness scorecard and kill list."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from certgen.core.io import write_json


KILLERS = [
    "no released samples for meaningful pairs",
    "unable to reproduce point estimates",
    "FID policy overclaimed",
    "undecided fraction near zero and no compute-savings story",
    "reviewer sees it as incremental KID with stopping rule",
    "related work misses obvious papers",
    "paper reads like stats-only",
    "no ranking or audit consequence",
    "claim gates allow fake evidence",
    "paper contains unsupported result numbers",
]


def build_cvpr_readiness_scorecard(real_results_present: bool = False) -> dict[str, Any]:
    empirical_actual = 1 if not real_results_present else 5
    return {
        "scores": {
            "paper_framing": 8,
            "statistical_correctness": 7,
            "clean_core_metric_implementation": 8,
            "fid_fd_policy_honesty": 9,
            "provenance_release_readiness": 7,
            "reproducibility": 8,
            "related_work_preparedness": 5,
            "result_contract_readiness": 9,
            "reviewer_defense_readiness": 7,
            "empirical_evidence_readiness": 4,
            "empirical_evidence_actual_status": empirical_actual,
            "cvpr_submission_readiness": 3 if not real_results_present else 6,
        },
        "status": {
            "infrastructure": "ready_except_runs",
            "empirical_evidence": "blocked_until_real_runs" if not real_results_present else "in_progress",
            "submission": "not_submission_ready",
        },
        "kill_list": KILLERS,
        "claim_allowed": False,
        "evidence_status": "template_only",
    }


def audit_cvpr_readiness(real_results_present: bool = False) -> dict[str, Any]:
    payload = build_cvpr_readiness_scorecard(real_results_present)
    errors: list[str] = []
    if not real_results_present and payload["scores"]["empirical_evidence_actual_status"] > 2:
        errors.append("no-results state cannot receive high empirical score")
    for killer in KILLERS:
        if killer not in payload["kill_list"]:
            errors.append(f"missing killer: {killer}")
    return {**payload, "passed": not errors, "errors": errors}


def write_cvpr_readiness(report: str | Path = "docs/CVPR_READINESS_SCORECARD_V5.md", kill_list: str | Path = "docs/CVPR_KILL_LIST_V5.md", json_out: str | Path = "data/results/cvpr_readiness_scorecard_v5.json") -> dict[str, Any]:
    payload = audit_cvpr_readiness(False)
    lines = ["# CVPR Readiness Scorecard V5", "", "`NO_REAL_EVIDENCE`", "", f"Infrastructure: `{payload['status']['infrastructure']}`", f"Empirical evidence: `{payload['status']['empirical_evidence']}`", f"Submission: `{payload['status']['submission']}`", "", "| Category | Score |", "|---|---:|"]
    for key, value in payload["scores"].items():
        lines.append(f"| `{key}` | {value} |")
    Path(report).parent.mkdir(parents=True, exist_ok=True)
    Path(report).write_text("\n".join(lines) + "\n", encoding="utf-8")
    kill_lines = ["# CVPR Kill List V5", "", "`NO_REAL_EVIDENCE`", ""]
    kill_lines.extend(f"- {killer}" for killer in payload["kill_list"])
    Path(kill_list).write_text("\n".join(kill_lines) + "\n", encoding="utf-8")
    write_json(payload, json_out)
    return payload
