"""Machine-readable benchmark/model study-selection rubric."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from certgen.icml2027.common import load_mapping, write_csv, write_json


CRITERIA = (
    "scientific_value",
    "model_family_diversity",
    "benchmark_diversity",
    "public_availability",
    "license_clarity",
    "compute_cost",
    "released_sample_availability",
    "feature_compatibility",
    "preflight_complexity",
    "reviewer_value",
    "risk",
)
NEGATIVE = {"compute_cost", "preflight_complexity", "risk"}


def plan_study_selection(config_path: str | Path, out_path: str | Path) -> dict[str, Any]:
    config = load_mapping(config_path)
    weights = {criterion: float(config.get("weights", {}).get(criterion, 1.0)) for criterion in CRITERIA}
    rows: list[dict[str, Any]] = []
    for candidate in config.get("candidates", []):
        if not isinstance(candidate, dict) or not candidate.get("candidate_id"):
            raise ValueError("each selection candidate requires candidate_id")
        scores = candidate.get("scores", {})
        if set(scores) != set(CRITERIA):
            raise ValueError(f"candidate {candidate['candidate_id']} must score every rubric criterion")
        normalized: dict[str, float] = {}
        total = 0.0
        for criterion in CRITERIA:
            raw = float(scores[criterion])
            if not 0.0 <= raw <= 5.0:
                raise ValueError(f"score {criterion} must be in [0,5]")
            normalized[criterion] = raw
            contribution = (5.0 - raw if criterion in NEGATIVE else raw) * weights[criterion]
            total += contribution
        gates = candidate.get("gates", {})
        executable = all(bool(gates.get(key, False)) for key in (
            "source_verified", "license_reviewed", "revision_pinned", "adapter_validated",
            "reference_protocol_frozen", "feature_protocol_frozen", "compute_feasible",
            "released_sample_semantics_clear",
        ))
        rows.append(
            {
                "candidate_id": candidate["candidate_id"],
                **normalized,
                "weighted_score": total,
                "go_no_go": "GO" if executable else "NO_GO",
                "blocker": "" if executable else candidate.get("blocker", "one or more execution gates are false"),
                "planning_only": True,
                "claim_allowed": False,
            }
        )
    rows.sort(key=lambda row: (-float(row["weighted_score"]), str(row["candidate_id"])))
    target = Path(out_path)
    write_csv(target, rows)
    payload = {
        "schema_version": "certgen.icml2027.study_selection.v1",
        "ranked_candidates": rows,
        "auto_execute": False,
        "planning_only": True,
        "claim_allowed": False,
    }
    write_json(target.with_suffix(".summary.json"), payload)
    return payload
