"""Prospectively fixed decision logic for the post-1k pilot handoff."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from certgen.cvpr.contracts import atomic_write_json


SCHEMA_VERSION = "certgen.cvpr.pilot_stop_go.v1"
DECISIONS = {"STOP", "REPAIR", "SCALE_TO_10K", "ADD_DINO", "ADD_CFM", "ADD_SECOND_BENCHMARK"}


def evaluate_pilot_stop_go(summary: Mapping[str, Any]) -> dict[str, Any]:
    """Evaluate gates in fixed order without inspecting any unfrozen alternative."""

    required = {
        "family_operational_status", "control_status", "metric_reproduction_status",
        "certificate_status", "all_primary_undecided", "dino_preflight_status",
        "cfm_preflight_status", "second_benchmark_preregistered",
    }
    missing = sorted(required - set(summary))
    if missing:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "PENDING_REAL_PILOT",
            "decision": None,
            "eligible_expansions": [],
            "blockers": ["missing fixed input: " + field for field in missing],
            "rules_frozen_before_outcomes": True,
            "claim_allowed": False,
        }
    integrity_values = {
        "family": summary["family_operational_status"] == "FAMILY_OPERATIONALLY_READY",
        "controls": summary["control_status"] == "PASS",
        "metric": summary["metric_reproduction_status"] == "PASS",
        "certificates": summary["certificate_status"] == "COMPLETE",
    }
    blockers = [name for name, passed in integrity_values.items() if not passed]
    if blockers:
        decision = "REPAIR"
    elif summary["all_primary_undecided"] is True:
        decision = "STOP"
    else:
        decision = "SCALE_TO_10K"
    expansions: list[str] = []
    if decision == "SCALE_TO_10K" and summary["dino_preflight_status"] == "PASS":
        expansions.append("ADD_DINO")
    if decision == "SCALE_TO_10K" and summary["cfm_preflight_status"] == "PASS":
        expansions.append("ADD_CFM")
    if decision == "SCALE_TO_10K" and summary["second_benchmark_preregistered"] is True:
        expansions.append("ADD_SECOND_BENCHMARK")
    if decision not in DECISIONS or any(item not in DECISIONS for item in expansions):
        raise AssertionError("stop/go evaluator produced an unsupported decision")
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "PILOT_STOP_GO_DECISION_READY",
        "decision": decision,
        "eligible_expansions": expansions,
        "gate_results": integrity_values,
        "blockers": blockers,
        "rules_frozen_before_outcomes": True,
        "requires_new_study_version_for_expansion": bool(expansions or decision == "SCALE_TO_10K"),
        "evidence_class": "pilot_decision_support_only",
        "claim_allowed": False,
    }


def write_pilot_stop_go(summary_path: str | Path, out_path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(summary_path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("pilot summary must be a JSON object")
    result = evaluate_pilot_stop_go(payload)
    atomic_write_json(result, out_path)
    return result
