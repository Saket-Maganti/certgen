"""Claim-safe V3 pilot report cards."""

from __future__ import annotations

from pathlib import Path

from certgen.core.io import read_json
from certgen.gates.claim_gate import scan_report_for_overclaims


def render_pilot_report(summary: dict) -> str:
    claim_allowed = bool(summary.get("claim_allowed"))
    mode = summary.get("mode", "dry_run")
    if not claim_allowed and summary.get("evidence_status") == "dry_run_only":
        label = "NO_REAL_VALIDATED_FEATURES. This report is a planning/dry-run artifact only."
    elif not claim_allowed:
        label = "REAL_FEATURES_USED_IN_NON_CLAIM_MODE. Results may be used for debugging and go/no-go planning only."
    else:
        label = "claim gate marked eligible"
    lines = [
        "# Pilot Report Card V3",
        "",
        label,
        "",
        "This artifact is not paper evidence and must not be used to claim a decidedness fraction, ranking movement, model superiority, or published-result error.",
        "",
        f"- Pilot ID: `{summary.get('pilot_id')}`",
        f"- Mode: `{mode}`",
        f"- Evidence status: `{summary.get('evidence_status')}`",
        f"- Claim allowed: `{claim_allowed}`",
        f"- Blockers: `{summary.get('claim_blockers', [])}`",
        f"- Pilot result computed: `{summary.get('pilot_result_computed')}`",
        f"- Undecided fraction: `{summary.get('undecided_fraction')}`",
        "",
        "## Benchmark/Model Pair Table",
    ]
    for comp in summary.get("comparisons", []):
        lines.append(f"- `{comp.get('comparison_id')}`: `{comp}`")
    lines.extend(["", "## Certificate Summary"])
    for cert in summary.get("certificates", []):
        lines.append(f"- `{cert}`")
    lines.extend(
        [
            "",
            "## FID/FD Descriptive-Only Section",
            "",
            "FID and FD-DINOv2 remain descriptive-only unless a future rigorous method is established.",
            "",
            "## Reproducibility Checklist",
            "",
            "- Provenance ledger checked.",
            "- Feature caches validated when present.",
            "- Certificate replay available.",
            "",
            "## Exact Commands",
            "",
            "- `python -m certgen.cli.run_first_pilot ...`",
            "",
            "## Forbidden Interpretations",
            "",
            "- No model superiority claim.",
            "- No ranking movement claim.",
            "- No published-result error claim.",
        ]
    )
    report = "\n".join(lines) + "\n"
    decision = scan_report_for_overclaims(report, claim_allowed=claim_allowed)
    if not decision.passed:
        raise ValueError(decision.reason)
    return report


def render_pilot_report_file(summary_json: str, out: str) -> str:
    summary = read_json(summary_json)
    report = render_pilot_report(summary)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(report, encoding="utf-8")
    return report
