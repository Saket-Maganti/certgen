"""V9 runtime budget planner."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from certgen.core.io import write_json


PLANS = {
    "1k": {
        "checkpoint_preflight": "5-20 min on Kaggle T4x2",
        "generation": "30 min-3 hr total for three models on Kaggle T4x2",
        "feature_extraction": "Inception 5-30 min; CLIP 10-45 min",
        "cpu_imports": "seconds-minutes",
        "cpu_sanity_gates": "seconds-minutes",
        "cpu_certificate_pilot": "seconds-minutes after gates pass",
    },
    "10k": {
        "checkpoint_preflight": "reuse 1k preflight unless checkpoints changed",
        "generation": "1-8 hr/model planning estimate",
        "feature_extraction": "Inception 10-60 min; CLIP 30-120 min",
        "cpu_imports": "minutes, dominated by hashing",
        "cpu_sanity_gates": "minutes",
        "cpu_certificate_pilot": "minutes",
    },
    "50k": {
        "checkpoint_preflight": "reuse 1k preflight unless checkpoints changed",
        "generation": "6-24+ hr/model planning estimate",
        "feature_extraction": "Inception 30-180 min; CLIP 1-6 hr",
        "cpu_imports": "minutes-tens of minutes, dominated by hashing",
        "cpu_sanity_gates": "minutes-tens of minutes",
        "cpu_certificate_pilot": "minutes-tens of minutes",
    },
}


def build_plan(scale: str, out_json: str | Path = "data/results/v9_runtime_budget_plan.json", out_report: str | Path = "docs/V9_RUNTIME_BUDGET_PLAN.md") -> dict:
    if scale not in PLANS:
        raise ValueError(f"scale must be one of {sorted(PLANS)}")
    payload = {
        "scale": scale,
        "planning_estimates": PLANS[scale],
        "all_scales": PLANS,
        "label": "planning estimates only, not empirical project results",
        "claim_allowed": False,
        "no_fake_results": True,
        "not_paper_evidence": True,
    }
    write_json(payload, out_json)
    lines = [
        "# V9 Runtime Budget Plan",
        "",
        "`planning estimates only, not empirical project results`",
        "`NO_FAKE_RESULTS`",
        "`NO_REAL_EVIDENCE`",
        "",
        f"Selected scale: `{scale}`",
        "",
        "| Stage | Estimate |",
        "|---|---|",
    ]
    for key, value in PLANS[scale].items():
        lines.append(f"| `{key}` | {value} |")
    Path(out_report).parent.mkdir(parents=True, exist_ok=True)
    Path(out_report).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", choices=sorted(PLANS), required=True)
    parser.add_argument("--out-json", default="data/results/v9_runtime_budget_plan.json")
    parser.add_argument("--out-report", default="docs/V9_RUNTIME_BUDGET_PLAN.md")
    args = parser.parse_args(argv)
    payload = build_plan(args.scale, args.out_json, args.out_report)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
