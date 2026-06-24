"""First real pilot controller and go/no-go logic."""

from __future__ import annotations

from pathlib import Path

from certgen.core.io import read_json, write_json


def go_no_go(undecided_fraction: float | None, *, gates_passed: bool, synthetic: bool = False, ranking_instability: bool = False, samples_story: bool = False) -> str:
    if synthetic:
        return "NONCLAIM_DRY_RUN"
    if not gates_passed or undecided_fraction is None:
        return "BLOCKED"
    if undecided_fraction >= 0.25 or ranking_instability:
        return "GO_STRONG"
    if undecided_fraction >= 0.05 or samples_story:
        return "GO_CONDITIONAL"
    return "NO_GO_FOR_AUDIT_HEADLINE"


def run_first_real_pilot_controller(plan: str | Path, out_dir: str | Path, report: str | Path, dry_run: bool = True) -> dict:
    plan_data = read_json(plan)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    gates_passed = not plan_data.get("blockers")
    status = go_no_go(None, gates_passed=gates_passed, synthetic=dry_run)
    payload = {
        "pilot_status": status,
        "stages": {
            "stage_0_dry_run": True,
            "stage_1_provenance_gate": gates_passed,
            "stage_2_feature_cache_gate": False if dry_run else None,
            "stage_3_reproduction_gate": False if dry_run else None,
            "stage_4_certificate_gate": False if dry_run else None,
        },
        "evidence_status": "dry_run_only" if dry_run else "real_verified_nonclaim",
        "claim_allowed": False,
        "next_action": "supply validated real feature caches" if dry_run else "inspect non-claim pilot report",
    }
    write_json(payload, out_dir / "summary.json")
    lines = ["# V4 First Real Pilot Controller", "", "`NO_REAL_EVIDENCE`", "", f"Pilot status: `{status}`", f"Claim allowed: `{payload['claim_allowed']}`", "", f"Next action: {payload['next_action']}"]
    Path(report).parent.mkdir(parents=True, exist_ok=True)
    Path(report).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload
