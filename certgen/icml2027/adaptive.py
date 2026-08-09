"""Exploratory edge-allocation schedulers for CertGen-Active simulations."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from typing import Any


POLICY_VALIDITY = {
    "uniform": "VALIDITY_INHERITED",
    "round_robin": "VALIDITY_INHERITED",
    "uncertainty_first": "EXPLORATORY_NOT_PROVEN",
    "largest_confidence_width": "EXPLORATORY_NOT_PROVEN",
    "graph_frontier": "EXPLORATORY_NOT_PROVEN",
}


def select_edge(
    edges: Sequence[dict[str, Any]],
    policy: str,
    *,
    step: int,
) -> int:
    if policy not in POLICY_VALIDITY:
        raise ValueError(f"unsupported allocation policy: {policy}")
    unresolved = [index for index, edge in enumerate(edges) if not bool(edge.get("resolved", False))]
    if not unresolved:
        raise ValueError("no unresolved edges remain")
    if policy == "round_robin":
        return unresolved[step % len(unresolved)]
    if policy == "uniform":
        return min(unresolved, key=lambda index: (int(edges[index].get("samples", 0)), index))
    if policy == "uncertainty_first":
        return min(
            unresolved,
            key=lambda index: (abs(float(edges[index].get("estimate", 0.0))) / max(float(edges[index].get("width", 1.0)), 1e-12), index),
        )
    if policy == "largest_confidence_width":
        return max(unresolved, key=lambda index: (float(edges[index].get("width", 0.0)), -index))
    degrees: dict[str, int] = defaultdict(int)
    for edge in edges:
        if edge.get("resolved"):
            degrees[str(edge["source"])] += 1
            degrees[str(edge["target"])] += 1
    return max(
        unresolved,
        key=lambda index: (
            degrees[str(edges[index]["source"])] + degrees[str(edges[index]["target"])],
            float(edges[index].get("width", 0.0)),
            -index,
        ),
    )


def policy_contract(policy: str) -> dict[str, Any]:
    if policy not in POLICY_VALIDITY:
        raise ValueError(f"unsupported allocation policy: {policy}")
    return {
        "policy": policy,
        "validity_status": POLICY_VALIDITY[policy],
        "confirmatory_eligible": POLICY_VALIDITY[policy] in {"VALIDITY_PROVEN", "VALIDITY_INHERITED"},
        "claim_allowed": False,
    }
