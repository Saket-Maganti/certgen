"""Prospectively specified, nonclaim analyses over completed certificates."""

from __future__ import annotations

import csv
import json
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable, Mapping

from certgen.core.hashing import stable_hash_json
from certgen.cvpr.contracts import atomic_write_json


DECIDED = {"A_BETTER", "B_BETTER"}
UNRESOLVED = {"UNDECIDED_AT_BUDGET"}
INVALID = {"INVALID_INPUT", "BLOCKED_ASSUMPTION"}


def _certificates(certificates: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = [dict(row) for row in certificates]
    if not rows:
        raise ValueError("at least one certificate is required")
    seen: set[tuple[str, str, int]] = set()
    for row in rows:
        if row.get("claim_allowed") is not False:
            raise ValueError("pre-execution analysis requires claim_allowed=false inputs")
        decision = str(row.get("decision"))
        if decision not in DECIDED | UNRESOLVED | INVALID:
            raise ValueError(f"unsupported certificate decision: {decision}")
        key = (str(row.get("comparison_id")), str(row.get("feature_space")), int(row.get("sample_budget", 0)))
        if not all(key) or key in seen:
            raise ValueError(f"duplicate or incomplete certificate identity: {key}")
        seen.add(key)
    return rows


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    field: json.dumps(row.get(field), sort_keys=True)
                    if isinstance(row.get(field), (dict, list))
                    else row.get(field)
                    for field in fields
                }
            )


def write_cross_feature_analysis(
    certificates: Iterable[Mapping[str, Any]], out_dir: str | Path
) -> dict[str, Any]:
    """Write agreement/disagreement artifacts without treating disagreement as error."""

    rows = _certificates(certificates)
    target = Path(out_dir)
    if target.exists():
        raise FileExistsError(f"refusing to overwrite cross-feature analysis: {target}")
    target.mkdir(parents=True)
    spaces = sorted({str(row["feature_space"]) for row in rows})
    by_comparison: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_comparison.setdefault(str(row["comparison_id"]), []).append(row)
    agreement_rows: list[dict[str, Any]] = []
    for left, right in combinations(spaces, 2):
        comparable = 0
        same = 0
        opposite = 0
        for group in by_comparison.values():
            indexed = {str(row["feature_space"]): row for row in group}
            if left not in indexed or right not in indexed:
                continue
            left_decision = str(indexed[left]["decision"])
            right_decision = str(indexed[right]["decision"])
            if left_decision in DECIDED and right_decision in DECIDED:
                comparable += 1
                same += int(left_decision == right_decision)
                opposite += int(left_decision != right_decision)
        agreement_rows.append(
            {
                "feature_space_a": left,
                "feature_space_b": right,
                "jointly_decided": comparable,
                "same_direction": same,
                "opposite_direction": opposite,
                "agreement_fraction": same / comparable if comparable else None,
            }
        )
    disagreements: list[dict[str, Any]] = []
    one_unresolved: list[dict[str, Any]] = []
    invalid_feature_lanes: list[dict[str, Any]] = []
    consensus: list[dict[str, Any]] = []
    feature_specific: list[dict[str, Any]] = []
    for comparison_id, group in sorted(by_comparison.items()):
        decisions = {str(row["feature_space"]): str(row["decision"]) for row in group}
        directional = {value for value in decisions.values() if value in DECIDED}
        base = {
            "comparison_id": comparison_id,
            "model_a": group[0].get("model_a"),
            "model_b": group[0].get("model_b"),
            "feature_decisions": decisions,
        }
        if len(directional) > 1:
            disagreements.append({**base, "interpretation": "feature_specific_direction_disagreement_not_error"})
        if directional and any(value in UNRESOLVED for value in decisions.values()):
            one_unresolved.append(base)
        for row in group:
            if str(row["decision"]) in INVALID:
                invalid_feature_lanes.append(
                    {
                        **base,
                        "feature_space": str(row["feature_space"]),
                        "decision": str(row["decision"]),
                        "consensus_eligible": False,
                    }
                )
        if len(group) == len(spaces) and len(directional) == 1 and all(value in DECIDED for value in decisions.values()):
            decision = next(iter(directional))
            consensus.append(
                {
                    **base,
                    "winner": group[0]["model_a"] if decision == "A_BETTER" else group[0]["model_b"],
                    "loser": group[0]["model_b"] if decision == "A_BETTER" else group[0]["model_a"],
                }
            )
        else:
            feature_specific.append(base)
    _write_csv(target / "agreement_matrix.csv", agreement_rows, ["feature_space_a", "feature_space_b", "jointly_decided", "same_direction", "opposite_direction", "agreement_fraction"])
    _write_csv(target / "direction_disagreements.csv", disagreements, ["comparison_id", "model_a", "model_b", "feature_decisions", "interpretation"])
    _write_csv(target / "decided_in_one_unresolved_in_another.csv", one_unresolved, ["comparison_id", "model_a", "model_b", "feature_decisions"])
    _write_csv(target / "decided_vs_unresolved.csv", one_unresolved, ["comparison_id", "model_a", "model_b", "feature_decisions"])
    _write_csv(target / "invalid_feature_lanes.csv", invalid_feature_lanes, ["comparison_id", "model_a", "model_b", "feature_space", "decision", "feature_decisions", "consensus_eligible"])
    atomic_write_json({"edges": consensus, "claim_allowed": False}, target / "consensus_edges.json")
    atomic_write_json({"edges": feature_specific, "claim_allowed": False}, target / "feature_specific_edges.json")
    atomic_write_json(
        {
            "edges": feature_specific,
            "policy": "representation-specific conclusions must name the feature space",
            "claim_allowed": False,
        },
        target / "representation_specific_edges.json",
    )
    atomic_write_json(
        {
            "direct_agreement": "consensus only when all valid registered lanes decide the same direction",
            "direction_disagreement": "representation-specific, not automatically an implementation error",
            "decided_vs_unresolved": "no consensus edge",
            "invalid_feature_lane": "blocks consensus eligibility",
            "claim_allowed": False,
        },
        target / "cross_feature_policy.json",
    )
    return {
        "status": "CROSS_FEATURE_ANALYSIS_COMPLETE",
        "feature_spaces": spaces,
        "comparisons": len(by_comparison),
        "direction_disagreements": len(disagreements),
        "analysis_hash": stable_hash_json({"rows": rows, "rules": "prospective_v1"}),
        "claim_allowed": False,
    }


def write_ranking_stability(
    certificates: Iterable[Mapping[str, Any]], out_dir: str | Path
) -> dict[str, Any]:
    rows = _certificates(certificates)
    target = Path(out_dir)
    if target.exists():
        raise FileExistsError(f"refusing to overwrite ranking stability analysis: {target}")
    target.mkdir(parents=True)
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault((str(row["comparison_id"]), str(row["feature_space"])), []).append(row)
    stability: list[dict[str, Any]] = []
    for (comparison_id, feature_space), group in sorted(grouped.items()):
        ordered = sorted(group, key=lambda row: int(row["sample_budget"]))
        decided = [row for row in ordered if row["decision"] in DECIDED]
        first = decided[0] if decided else None
        protocol_hashes = {
            stable_hash_json(
                {
                    key: row.get(key)
                    for key in ("configuration_hash", "family_configuration_hash", "preprocessing_hash", "reference_draw_hash")
                }
            )
            for row in ordered
        }
        disappeared = bool(
            first
            and any(
                int(row["sample_budget"]) > int(first["sample_budget"])
                and row["decision"] not in DECIDED
                for row in ordered
            )
        )
        stability.append(
            {
                "comparison_id": comparison_id,
                "feature_space": feature_space,
                "edge_appearance_budget": int(first["sample_budget"]) if first else None,
                "first_decision_sample_count": first.get("first_decision_n") if first else None,
                "edge_disappearance": disappeared,
                "edge_disappearance_interpretation": "protocol_differs" if disappeared and len(protocol_hashes) > 1 else ("requires_audit" if disappeared else None),
                "unresolved_at_budgets": [int(row["sample_budget"]) for row in ordered if row["decision"] in UNRESOLVED],
                "decisions_by_budget": {str(row["sample_budget"]): row["decision"] for row in ordered},
                "protocol_consistent": len(protocol_hashes) == 1,
            }
        )
    _write_csv(target / "ranking_stability.csv", stability, ["comparison_id", "feature_space", "edge_appearance_budget", "first_decision_sample_count", "edge_disappearance", "edge_disappearance_interpretation", "unresolved_at_budgets", "decisions_by_budget", "protocol_consistent"])
    summary = {
        "schema_version": "certgen.cvpr.ranking_stability.v1",
        "registered_budgets": sorted({int(row["sample_budget"]) for row in rows}),
        "partial_order_stability": stability,
        "forced_total_order": False,
        "claim_allowed": False,
    }
    atomic_write_json(summary, target / "ranking_stability.json")
    return summary


def point_vs_certified_contract(
    *, point_estimates: Iterable[Mapping[str, Any]], ranking: Mapping[str, Any]
) -> dict[str, Any]:
    points = sorted(
        (dict(row) for row in point_estimates),
        key=lambda row: (float(row["point_estimate"]), str(row["model_id"])),
    )
    return {
        "schema_version": "certgen.cvpr.point_vs_certified.v1",
        "point_estimate_total_order": [str(row["model_id"]) for row in points],
        "point_estimates_are_descriptive": True,
        "certified_direct_edges": list(ranking.get("directed_certified_edges", [])),
        "transitive_implications": list(ranking.get("transitive_implications", [])),
        "unresolved_pairs": list(ranking.get("unresolved_pairs", [])),
        "invalid_pairs": list(ranking.get("invalid_pairs", [])),
        "forced_total_order": False,
        "claim_allowed": False,
    }


def compute_accounting_contract(records: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    required = {
        "run_id", "images_generated", "images_feature_extracted", "gpu_seconds", "cpu_seconds",
        "samples_at_first_decision", "fixed_budget_samples", "retrospective_savings", "online_realized_savings",
    }
    rows = [dict(row) for row in records]
    for row in rows:
        missing = sorted(required - set(row))
        if missing:
            raise ValueError("compute accounting row missing: " + ", ".join(missing))
        for field in required - {"run_id", "samples_at_first_decision"}:
            value = row[field]
            if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
                raise ValueError(f"{field} must be a nonnegative measured value")
        if row["samples_at_first_decision"] is not None and int(row["samples_at_first_decision"]) < 0:
            raise ValueError("samples_at_first_decision must be null or nonnegative")
    return {
        "schema_version": "certgen.cvpr.compute_accounting.v1",
        "records": rows,
        "savings_separation": "retrospective_savings and online_realized_savings are never interchangeable",
        "evidence_class": "execution_metadata",
        "claim_allowed": False,
    }


def qualitative_gallery_contract(panels: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    required = {"image_paths", "model_ids", "feature_space_decisions", "point_estimate_direction", "certificate_status", "first_decision_sample_count", "limitations"}
    rows = [dict(panel) for panel in panels]
    for panel in rows:
        missing = sorted(required - set(panel))
        if missing:
            raise ValueError("gallery panel missing: " + ", ".join(missing))
    return {
        "schema_version": "certgen.cvpr.qualitative_gallery.v1",
        "panels": rows,
        "distribution_claim_disclaimer": "Representative images are illustrative and are not proof of distribution-level superiority.",
        "claim_allowed": False,
    }


def summarize_samples_to_decision(certificates: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    rows = list(certificates)
    if not rows:
        raise ValueError("at least one certificate is required")
    decided = [row for row in rows if row.get("decision") in {"A_BETTER", "B_BETTER"}]
    censored = [row for row in rows if row.get("decision") == "UNDECIDED_AT_BUDGET"]
    invalid = [row for row in rows if row.get("decision") in {"INVALID_INPUT", "BLOCKED_ASSUMPTION"}]
    event_times = sorted(int(row["first_decision_n"]) for row in decided if row.get("first_decision_n") is not None)
    censoring_budgets = sorted(int(row["sample_budget"]) for row in censored)
    return {
        "schema_version": "certgen.cvpr.samples_to_decision.v1",
        "total_registered": len(rows),
        "decided": len(decided),
        "censored_undecided": len(censored),
        "invalid_or_blocked": len(invalid),
        "event_times": event_times,
        "censoring_budgets": censoring_budgets,
        "decided_only_summary_prohibited": bool(censored),
        "kaplan_meier_estimate": None,
        "kaplan_meier_status": "not_implemented_without_separate_statistical_justification",
        "evidence_class": "pilot_only",
        "claim_allowed": False,
    }


def validate_gate_result(payload: Mapping[str, Any]) -> list[str]:
    required = {"gate_id", "run_id", "inputs", "configuration_hash", "status", "measured_values", "tolerances", "failure_reason", "evidence_class", "claim_allowed"}
    errors = [f"missing field: {field}" for field in sorted(required - set(payload))]
    if payload.get("claim_allowed") is not False:
        errors.append("pre-execution gate results must keep claim_allowed=false")
    if payload.get("status") not in {"PASS", "FAIL", "BLOCKED", "NOT_RUN"}:
        errors.append("gate status must be PASS, FAIL, BLOCKED, or NOT_RUN")
    return errors
