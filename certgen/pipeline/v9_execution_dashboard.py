"""V9 execution dashboard renderer."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from certgen.core.io import read_json, write_json
from certgen.pipeline.v9_next_action import write_next_action


def _json(path: str | Path) -> dict[str, Any]:
    try:
        return read_json(path)
    except Exception:
        return {}


def build_dashboard(out_json: str | Path = "data/results/v9_execution_dashboard.json", out_report: str | Path = "docs/V9_EXECUTION_DASHBOARD.md") -> dict[str, Any]:
    next_action = write_next_action()
    final_audit = _json("data/results/final_execution_audit.json")
    preflight = _json("data/results/v9_checkpoint_preflight_import_status.json")
    generation = _json("data/results/v6_generation_output_validation_summary.json")
    feature = _json("data/results/v6_feature_output_validation_summary.json")
    sanity = _json("data/results/r1d_metric_reproduction.json")
    certificate = _json("data/results/r1e_undecided_fraction.json")
    payload = {
        "current_stage": next_action["action"],
        "completed_local_safe_upgrades": [
            "cifar_reference_super_onramp",
            "checkpoint_preflight_notebook",
            "hardened_generation_notebook",
            "hardened_feature_notebook",
            "import_repair_v2",
            "exact_next_action_engine",
            "runtime_budget_planner",
            "notebook_static_analyzer_v2",
            "paper_firewall_v2",
        ],
        "missing_real_inputs": [
            item
            for item, present in {
                "local CIFAR-10 reference samples": final_audit.get("r1_status_code") != "BLOCKED_MISSING_REFERENCE_SAMPLES",
                "copied-back generation ZIP": generation.get("passed") is True,
                "copied-back feature ZIP": feature.get("passed") is True,
                "metric sanity audit": sanity.get("ready_for_cpu_certificate_pilot") is True,
                "pilot certificates": certificate.get("status_code") == "PILOT_UNDECIDED_FRACTION_COMPUTED",
            }.items()
            if not present
        ],
        "kaggle_preflight_status": preflight.get("status_code", "not_run"),
        "generation_status": generation.get("status_code", "not_run"),
        "feature_extraction_status": feature.get("status_code", "not_run"),
        "metric_sanity_status": sanity.get("status_code", "missing"),
        "certificate_status": certificate.get("status_code", "missing"),
        "paper_evidence_status": "blocked_no_paper_evidence",
        "exact_next_action": next_action,
        "artifact_taxonomy": {
            "planning_artifacts": "runbooks, configs, ZIP manifests",
            "run_logs": "Kaggle wall-time/status logs only",
            "cache_artifacts": "feature caches after local validation",
            "sanity_artifacts": "R1D sanity-only non-claim outputs",
            "pilot_only_artifacts": "R1E first pilot non-claim outputs",
            "paper_evidence": "none",
        },
        "claim_allowed": False,
        "no_fake_results": True,
        "not_paper_evidence": True,
    }
    write_json(payload, out_json)
    lines = [
        "# V9 Execution Dashboard",
        "",
        "`NO_FAKE_RESULTS`",
        "`NO_REAL_EVIDENCE`",
        "`not paper evidence`",
        "",
        f"Current stage: `{payload['current_stage']}`",
        f"Paper evidence status: `{payload['paper_evidence_status']}`",
        f"Exact next action: `{next_action['action']}`",
        f"Exact command: `{next_action['exact_command']}`",
        "",
        "## Missing Real Inputs",
    ]
    lines.extend(f"- {item}" for item in payload["missing_real_inputs"] or ["none"])
    lines.extend(["", "## Status Table", "", "| Lane | Status |", "|---|---|"])
    for lane in ["kaggle_preflight_status", "generation_status", "feature_extraction_status", "metric_sanity_status", "certificate_status"]:
        lines.append(f"| `{lane}` | `{payload[lane]}` |")
    lines.extend(["", "## Artifact Taxonomy", "", "| Type | Meaning |", "|---|---|"])
    for key, value in payload["artifact_taxonomy"].items():
        lines.append(f"| `{key}` | {value} |")
    Path(out_report).parent.mkdir(parents=True, exist_ok=True)
    Path(out_report).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-json", default="data/results/v9_execution_dashboard.json")
    parser.add_argument("--out-report", default="docs/V9_EXECUTION_DASHBOARD.md")
    args = parser.parse_args(argv)
    payload = build_dashboard(args.out_json, args.out_report)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
