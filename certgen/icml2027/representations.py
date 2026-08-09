"""Cross-representation classification and conservative consensus policies."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from certgen.icml2027.common import read_rows, write_csv, write_json


RESOLVED = {"A_BETTER", "B_BETTER", "PRACTICALLY_EQUIVALENT"}


def classify_representation_decisions(decisions: list[str]) -> str:
    if not decisions or "INVALID" in decisions:
        return "INVALID"
    unique = set(decisions)
    if unique == {"A_BETTER"}:
        return "CONSENSUS_A_BETTER"
    if unique == {"B_BETTER"}:
        return "CONSENSUS_B_BETTER"
    if unique == {"PRACTICALLY_EQUIVALENT"}:
        return "CONSENSUS_EQUIVALENT"
    if unique == {"UNRESOLVED"}:
        return "CONSENSUS_UNRESOLVED"
    if "A_BETTER" in unique and "B_BETTER" in unique:
        return "DIRECTION_CONFLICT"
    resolved = unique & RESOLVED
    if resolved and "UNRESOLVED" in unique:
        return "ONE_RESOLVED_ONE_UNRESOLVED"
    return "REPRESENTATION_SPECIFIC"


def consensus_decision(decisions: list[str], policy: str) -> str:
    classification = classify_representation_decisions(decisions)
    if policy == "unanimous_direction":
        return {
            "CONSENSUS_A_BETTER": "A_BETTER",
            "CONSENSUS_B_BETTER": "B_BETTER",
        }.get(classification, "UNRESOLVED")
    if policy == "all_representations_equivalent":
        return "PRACTICALLY_EQUIVALENT" if classification == "CONSENSUS_EQUIVALENT" else "UNRESOLVED"
    if policy == "any_conflict_blocks":
        if classification in {"DIRECTION_CONFLICT", "REPRESENTATION_SPECIFIC", "INVALID"}:
            return "INVALID" if classification == "INVALID" else "UNRESOLVED"
        return consensus_decision(decisions, "unanimous_direction")
    if policy == "majority_direction_exploratory":
        counts = Counter(value for value in decisions if value in {"A_BETTER", "B_BETTER"})
        if counts["A_BETTER"] == counts["B_BETTER"]:
            return "UNRESOLVED"
        return max(("A_BETTER", "B_BETTER"), key=counts.__getitem__)
    raise ValueError(f"unsupported consensus policy: {policy}")


def analyze_representation_agreement(input_path: str | Path, out_dir: str | Path) -> dict[str, Any]:
    rows = read_rows(input_path)
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        comparison = str(row.get("comparison") or row.get("comparison_id") or "")
        feature = str(row.get("feature_space") or row.get("feature_space_id") or "")
        decision = str(row.get("decision") or "")
        if not comparison or not feature or not decision:
            raise ValueError("each row requires comparison, feature_space, and decision")
        grouped[(comparison, feature)].append(row)
    by_comparison: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for (comparison, feature), group in grouped.items():
        decision_set = {str(row["decision"]) for row in group}
        if len(decision_set) != 1:
            raise ValueError(f"duplicate conflicting rows for {comparison}/{feature}")
        by_comparison[comparison].append({"feature_space": feature, "decision": decision_set.pop()})
    output_rows: list[dict[str, Any]] = []
    conflict_edges: list[dict[str, Any]] = []
    for comparison, feature_rows in sorted(by_comparison.items()):
        feature_rows.sort(key=lambda row: row["feature_space"])
        decisions = [str(row["decision"]) for row in feature_rows]
        classification = classify_representation_decisions(decisions)
        row = {
            "comparison": comparison,
            "classification": classification,
            "representation_count": len(feature_rows),
            "decisions_json": json.dumps(feature_rows, sort_keys=True),
            "unanimous_direction": consensus_decision(decisions, "unanimous_direction"),
            "all_representations_equivalent": consensus_decision(decisions, "all_representations_equivalent"),
            "any_conflict_blocks": consensus_decision(decisions, "any_conflict_blocks"),
            "majority_direction_exploratory": consensus_decision(decisions, "majority_direction_exploratory"),
            "claim_allowed": False,
        }
        output_rows.append(row)
        if classification in {"DIRECTION_CONFLICT", "REPRESENTATION_SPECIFIC"}:
            conflict_edges.append({"comparison": comparison, "classification": classification, "representations": feature_rows})
    target = Path(out_dir)
    write_csv(target / "representation_agreement.csv", output_rows)
    write_json(
        target / "representation_conflict_graph.json",
        {"schema_version": "certgen.icml2027.representation_conflict_graph.v1", "edges": conflict_edges, "claim_allowed": False},
    )
    summary = {
        "schema_version": "certgen.icml2027.representation_summary.v1",
        "comparisons": len(output_rows),
        "classification_counts": dict(sorted(Counter(row["classification"] for row in output_rows).items())),
        "majority_direction_confirmatory": False,
        "claim_allowed": False,
    }
    write_json(target / "representation_summary.json", summary)
    return summary
