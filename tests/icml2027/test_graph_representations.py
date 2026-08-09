from __future__ import annotations

import json
from pathlib import Path

from certgen.icml2027.adaptive import policy_contract, select_edge
from certgen.icml2027.ranking import (
    graph_payload,
    incomparability_graph,
    strongly_connected_components,
    transitive_closure,
    transitive_reduction,
)
from certgen.icml2027.representations import (
    analyze_representation_agreement,
    classify_representation_decisions,
    consensus_decision,
)


def test_sparse_graph_utilities_and_cycles() -> None:
    nodes = ["a", "b", "c", "d"]
    edges = [("a", "b"), ("b", "c"), ("a", "c")]
    assert ("a", "c") in transitive_closure(edges, nodes)
    assert transitive_reduction(edges, nodes) == [("a", "b"), ("b", "c")]
    assert ("a", "d") in incomparability_graph(edges, nodes)
    assert strongly_connected_components([("a", "b"), ("b", "a")], nodes)[0] == ["a", "b"]
    payload = graph_payload(nodes, [{"source": "a", "target": "b", "decision": "A_BETTER"}])
    assert payload["cycles"] == []
    assert payload["claim_allowed"] is False


def test_representation_classification_and_consensus(tmp_path: Path) -> None:
    assert classify_representation_decisions(["A_BETTER", "B_BETTER"]) == "DIRECTION_CONFLICT"
    assert consensus_decision(["A_BETTER", "A_BETTER"], "unanimous_direction") == "A_BETTER"
    assert consensus_decision(["A_BETTER", "B_BETTER", "A_BETTER"], "majority_direction_exploratory") == "A_BETTER"
    source = tmp_path / "rows.json"
    source.write_text(
        json.dumps(
            [
                {"comparison": "a_vs_b", "feature_space": "inception", "decision": "A_BETTER"},
                {"comparison": "a_vs_b", "feature_space": "clip", "decision": "B_BETTER"},
                {"comparison": "c_vs_d", "feature_space": "inception", "decision": "UNRESOLVED"},
                {"comparison": "c_vs_d", "feature_space": "clip", "decision": "UNRESOLVED"},
            ]
        ),
        encoding="utf-8",
    )
    summary = analyze_representation_agreement(source, tmp_path / "out")
    assert summary["classification_counts"]["DIRECTION_CONFLICT"] == 1
    assert (tmp_path / "out/representation_conflict_graph.json").is_file()


def test_adaptive_policy_validity_labels() -> None:
    edges = [
        {"source": "a", "target": "b", "samples": 4, "width": 1.0, "estimate": 0.0, "resolved": False},
        {"source": "a", "target": "c", "samples": 2, "width": 2.0, "estimate": 0.2, "resolved": False},
    ]
    assert select_edge(edges, "uniform", step=0) == 1
    assert select_edge(edges, "largest_confidence_width", step=0) == 1
    assert policy_contract("graph_frontier")["validity_status"] == "EXPLORATORY_NOT_PROVEN"
