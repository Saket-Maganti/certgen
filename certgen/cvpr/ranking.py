"""Certified partial-ranking graphs with strict family compatibility checks."""

from __future__ import annotations

import csv
import json
import os
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from certgen.core.hashing import file_sha256, stable_hash_json
from certgen.cvpr.contracts import atomic_write_json
from certgen.cvpr.registries import validate_family_record


DECISIONS = {"A_BETTER", "B_BETTER", "UNDECIDED_AT_BUDGET", "INVALID_INPUT", "BLOCKED_ASSUMPTION"}


def _load_certificates(paths: Iterable[str | Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"certificate is not an object: {path}")
        if payload.get("decision") not in DECISIONS:
            raise ValueError(f"certificate has unsupported decision: {path}")
        rows.append(
            {
                **payload,
                "_certificate_artifact": str(Path(path).resolve()),
                "_certificate_sha256": file_sha256(path),
            }
        )
    if not rows:
        raise ValueError("at least one certificate is required")
    return rows


def _compatibility_errors(rows: list[dict[str, Any]], *, allow_multiple_feature_spaces: bool) -> list[str]:
    errors: list[str] = []
    exact_fields = ["family_id", "family_configuration_hash", "alpha_total", "alpha_pair", "benchmark", "metric", "kernel", "bandwidth", "configuration_hash", "reference_population_hash", "reference_draw_hash"]
    for field in exact_fields:
        values = {json.dumps(row.get(field), sort_keys=True) for row in rows}
        if len(values) != 1:
            errors.append(f"mixed {field} values are not ranking-compatible")
    if not allow_multiple_feature_spaces and len({row.get("feature_space") for row in rows}) != 1:
        errors.append("mixed feature spaces require an explicit aggregation protocol")
    for feature_space in {str(row.get("feature_space")) for row in rows}:
        lane = [row for row in rows if str(row.get("feature_space")) == feature_space]
        if len({json.dumps(row.get("preprocessing_hash"), sort_keys=True) for row in lane}) != 1:
            errors.append(f"mixed preprocessing_hash values within feature space {feature_space}")
    seen: set[tuple[str, str]] = set()
    for row in rows:
        key = (str(row.get("comparison_id")), str(row.get("feature_space")))
        if key in seen:
            errors.append(f"duplicate comparison/feature-space certificate: {key}")
        seen.add(key)
        if row.get("claim_allowed") is not False:
            errors.append("pre-execution ranking refuses claim_allowed=true inputs")
    return errors


def _reachability(nodes: set[str], edges: list[dict[str, Any]]) -> dict[str, set[str]]:
    adjacency: dict[str, set[str]] = {node: set() for node in nodes}
    for edge in edges:
        adjacency[str(edge["winner"])].add(str(edge["loser"]))
    closure: dict[str, set[str]] = {}
    for node in nodes:
        reached: set[str] = set()
        stack = list(adjacency[node])
        while stack:
            current = stack.pop()
            if current in reached:
                continue
            reached.add(current)
            stack.extend(adjacency.get(current, ()))
        closure[node] = reached
    return closure


def _incomparability(nodes: set[str], edges: list[dict[str, Any]]) -> tuple[list[dict[str, str]], list[list[str]]]:
    closure = _reachability(nodes, edges)
    pairs: list[dict[str, str]] = []
    adjacency: dict[str, set[str]] = {node: set() for node in nodes}
    ordered = sorted(nodes)
    for index, left in enumerate(ordered):
        for right in ordered[index + 1 :]:
            if right not in closure[left] and left not in closure[right]:
                pairs.append({"model_a": left, "model_b": right})
                adjacency[left].add(right)
                adjacency[right].add(left)
    groups: list[list[str]] = []
    unseen = set(nodes)
    while unseen:
        start = min(unseen)
        component: set[str] = set()
        stack = [start]
        while stack:
            current = stack.pop()
            if current in component:
                continue
            component.add(current)
            unseen.discard(current)
            stack.extend(adjacency[current] - component)
        if len(component) > 1:
            groups.append(sorted(component))
    return pairs, groups


def _contradiction_components(nodes: set[str], feature_graphs: dict[str, dict[str, Any]]) -> list[list[str]]:
    combined = [edge for graph in feature_graphs.values() for edge in graph["directed_certified_edges"]]
    closure = _reachability(nodes, combined)
    components: list[list[str]] = []
    remaining = set(nodes)
    while remaining:
        start = min(remaining)
        component = {node for node in remaining if node == start or (node in closure[start] and start in closure[node])}
        remaining -= component
        if len(component) > 1:
            components.append(sorted(component))
    return components


def build_partial_ranking(
    certificate_paths: Iterable[str | Path], *, out_dir: str | Path, aggregation_rule: str | None = None,
    family_path: str | Path | None = None,
) -> dict[str, Any]:
    rows = _load_certificates(certificate_paths)
    multi_feature = len({row.get("feature_space") for row in rows}) > 1
    if multi_feature and aggregation_rule not in {"unanimous_direction_or_unresolved"}:
        raise ValueError("multi-feature ranking requires aggregation_rule=unanimous_direction_or_unresolved")
    errors = _compatibility_errors(rows, allow_multiple_feature_spaces=aggregation_rule is not None)
    if errors:
        raise ValueError("invalid ranking inputs: " + "; ".join(errors))
    family: dict[str, Any] | None = None
    if family_path is not None:
        family_payload = json.loads(Path(family_path).read_text(encoding="utf-8"))
        if not isinstance(family_payload, dict):
            raise ValueError("ranking family must be a JSON object")
        verdict = validate_family_record(family_payload, require_frozen=True)
        if not verdict["passed"]:
            raise ValueError("ranking family is invalid: " + "; ".join(verdict["errors"]))
        for certificate in rows:
            if certificate.get("family_id") != family_payload.get("family_id") or certificate.get("family_configuration_hash") != family_payload.get("configuration_hash"):
                raise ValueError("certificate does not belong to the supplied frozen family")
        expected_hypotheses = {
            str(item["hypothesis_id"]): item
            for item in family_payload.get("hypotheses", [])
            if isinstance(item, dict) and item.get("hypothesis_id")
        }
        actual_hypotheses: set[str] = set()
        for certificate in rows:
            hypothesis_id = certificate.get("hypothesis_id")
            if not hypothesis_id:
                matches = [
                    item for item in expected_hypotheses.values()
                    if str(item.get("comparison_id")) == str(certificate.get("comparison_id"))
                    and str(item.get("feature_space")) == str(certificate.get("feature_space"))
                    and str(item.get("metric")) == str(certificate.get("metric"))
                    and int(item.get("sample_budget", -1)) == int(certificate.get("sample_budget", -2))
                ]
                if len(matches) != 1:
                    raise ValueError("certificate cannot be resolved to exactly one frozen hypothesis")
                hypothesis_id = matches[0]["hypothesis_id"]
                certificate["hypothesis_id"] = hypothesis_id
            actual_hypotheses.add(str(hypothesis_id))
        if expected_hypotheses:
            excluded_hypotheses = set(map(str, family_payload.get("excluded_hypotheses", [])))
            missing_hypotheses = sorted(set(expected_hypotheses) - actual_hypotheses - excluded_hypotheses)
            extra_hypotheses = sorted(actual_hypotheses - set(expected_hypotheses))
            if missing_hypotheses or extra_hypotheses:
                raise ValueError(
                    f"ranking requires complete frozen-family certificate coverage: missing={missing_hypotheses}, extra={extra_hypotheses}"
                )
        family = family_payload
    target = Path(out_dir)
    if target.exists():
        raise FileExistsError(f"refusing to overwrite ranking directory: {target}")
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    nodes: set[str] = set()
    for row in rows:
        grouped[str(row["comparison_id"])].append(row)
        nodes.update((str(row["model_a"]), str(row["model_b"])))
    edges: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    invalid_pairs: list[dict[str, Any]] = []
    disagreements: list[dict[str, Any]] = []
    for comparison_id, group in sorted(grouped.items()):
        invalid_rows = [row for row in group if row.get("decision") in {"INVALID_INPUT", "BLOCKED_ASSUMPTION"}]
        if invalid_rows:
            invalid_pairs.append({"comparison_id": comparison_id, "model_a": group[0]["model_a"], "model_b": group[0]["model_b"], "feature_decisions": {str(row["feature_space"]): row["decision"] for row in group}})
            continue
        directions = {row.get("direction") for row in group if row.get("decision") in {"A_BETTER", "B_BETTER"}}
        unresolved_rows = [row for row in group if row.get("decision") not in {"A_BETTER", "B_BETTER"}]
        if len(directions) > 1:
            disagreements.append({"comparison_id": comparison_id, "model_a": group[0]["model_a"], "model_b": group[0]["model_b"], "feature_decisions": {str(row["feature_space"]): row["decision"] for row in group}})
            continue
        if unresolved_rows or not directions:
            unresolved.append({"comparison_id": comparison_id, "model_a": group[0]["model_a"], "model_b": group[0]["model_b"], "reason": "one_or_more_feature_spaces_undecided", "feature_decisions": {str(row["feature_space"]): row["decision"] for row in group}})
            continue
        direction = next(iter(directions))
        winner = group[0]["model_a"] if direction == "A" else group[0]["model_b"]
        loser = group[0]["model_b"] if direction == "A" else group[0]["model_a"]
        edges.append(
            {
                "comparison_id": comparison_id,
                "winner": winner,
                "loser": loser,
                "feature_spaces": sorted(str(row["feature_space"]) for row in group),
                "family_id": group[0]["family_id"],
                "family_membership": "frozen_primary_family",
                "study_hash": group[0]["configuration_hash"],
                "supporting_certificate_ids": [
                    str(row.get("certificate_hash") or row.get("hypothesis_id")) for row in group
                ],
                "certificate_artifacts": [
                    {"path": row["_certificate_artifact"], "sha256": row["_certificate_sha256"]}
                    for row in group
                ],
                "edge_status": "direct",
                "direct_or_transitive": "direct",
                "agreement_status": "all_registered_feature_lanes_same_direction",
                "certified": True,
            }
        )
    feature_graphs: dict[str, dict[str, Any]] = {}
    for feature_space in sorted({str(row["feature_space"]) for row in rows}):
        feature_rows = [row for row in rows if str(row["feature_space"]) == feature_space]
        feature_edges = []
        feature_unresolved = []
        for row in feature_rows:
            if row["decision"] in {"A_BETTER", "B_BETTER"}:
                winner = row["model_a"] if row["direction"] == "A" else row["model_b"]
                loser = row["model_b"] if row["direction"] == "A" else row["model_a"]
                feature_edges.append(
                    {
                        "comparison_id": row["comparison_id"],
                        "winner": winner,
                        "loser": loser,
                        "feature_space": feature_space,
                        "family_id": row["family_id"],
                        "study_hash": row["configuration_hash"],
                        "certificate_artifact": {
                            "path": row["_certificate_artifact"],
                            "sha256": row["_certificate_sha256"],
                        },
                        "edge_status": "direct",
                        "certified": True,
                    }
                )
            else:
                feature_unresolved.append({"comparison_id": row["comparison_id"], "model_a": row["model_a"], "model_b": row["model_b"], "decision": row["decision"]})
        feature_graphs[feature_space] = {"directed_certified_edges": feature_edges, "unresolved_pairs": feature_unresolved}
    expected_comparisons = set(map(str, family.get("model_pairs", []))) if family else set(grouped)
    excluded_comparisons = sorted(map(str, family.get("excluded_comparisons", []))) if family else []
    missing_comparisons = sorted(expected_comparisons - set(grouped) - set(excluded_comparisons))
    incomparable_pairs, incomparable_groups = _incomparability(nodes, edges)
    closure = _reachability(nodes, edges)
    direct_pairs = {(str(edge["winner"]), str(edge["loser"])) for edge in edges}
    transitive_implications = [
        {
            "winner": winner,
            "loser": loser,
            "family_id": rows[0]["family_id"],
            "family_membership": "frozen_primary_family",
            "study_hash": rows[0]["configuration_hash"],
            "supporting_certificate_ids": sorted(
                {
                    str(row.get("certificate_hash") or row.get("hypothesis_id"))
                    for row in rows
                }
            ),
            "supporting_certificate_artifacts": sorted(
                {
                    item["path"]
                    for edge in edges
                    for item in edge["certificate_artifacts"]
                }
            ),
            "edge_status": "transitive",
            "direct_or_transitive": "transitive",
            "agreement_status": "derived_from_acyclic_certified_direct_edges",
            "certified_by_transitivity": True,
        }
        for winner in sorted(nodes)
        for loser in sorted(closure[winner])
        if (winner, loser) not in direct_pairs
    ]
    contradiction_components = _contradiction_components(nodes, feature_graphs)
    graph = {
        "schema_version": "certgen.cvpr.ranking_graph.v1",
        "family_id": rows[0]["family_id"],
        "benchmark": rows[0]["benchmark"],
        "alpha_total": rows[0]["alpha_total"],
        "configuration_hash": rows[0]["configuration_hash"],
        "nodes": sorted(nodes),
        "directed_certified_edges": edges,
        "transitive_implications": transitive_implications,
        "unresolved_pairs": unresolved,
        "invalid_pairs": invalid_pairs,
        "feature_disagreements": disagreements,
        "missing_comparisons": missing_comparisons,
        "missing_hypotheses": [],
        "excluded_comparisons": excluded_comparisons,
        "incomparable_pairs": incomparable_pairs,
        "incomparable_groups": incomparable_groups,
        "contradiction_components": contradiction_components,
        "feature_space_graphs": feature_graphs,
        "aggregation_rule": aggregation_rule,
        "forced_total_order": False,
        "evidence_class": "pilot_only",
        "claim_allowed": False,
    }
    graph["ranking_hash"] = stable_hash_json(graph)
    target.parent.mkdir(parents=True, exist_ok=True)
    staged = Path(tempfile.mkdtemp(prefix=f".{target.name}.", dir=target.parent))
    try:
        atomic_write_json(graph, staged / "ranking_graph.json")
        atomic_write_json(
            {
                "schema_version": "certgen.cvpr.ranking_provenance.v1",
                "ranking_hash": graph["ranking_hash"],
                "study_hash": graph["configuration_hash"],
                "family_id": graph["family_id"],
                "supporting_certificate_ids": sorted(
                    {
                        str(row.get("certificate_hash") or row.get("hypothesis_id"))
                        for row in rows
                    }
                ),
                "feature_spaces": sorted({str(row["feature_space"]) for row in rows}),
                "forced_total_order": False,
                "claim_allowed": False,
            },
            staged / "ranking_provenance.json",
        )
        atomic_write_json({"nodes": len(nodes), "certified_edges": len(edges), "unresolved_pairs": len(unresolved), "feature_disagreements": len(disagreements), "missing_comparisons": len(missing_comparisons), "excluded_comparisons": len(excluded_comparisons), "incomparable_pairs": len(incomparable_pairs), "contradiction_components": len(contradiction_components), "claim_allowed": False}, staged / "ranking_summary.json")
        _write_csv(
            staged / "ranking_edges.csv",
            edges,
            [
                "comparison_id", "winner", "loser", "feature_spaces", "family_id",
                "study_hash", "supporting_certificate_ids", "certificate_artifacts",
                "direct_or_transitive", "agreement_status", "family_membership",
                "edge_status", "certified",
            ],
        )
        _write_csv(staged / "unresolved_pairs.csv", unresolved, ["comparison_id", "model_a", "model_b", "reason", "feature_decisions"])
        _write_csv(staged / "ranking_unresolved.csv", unresolved, ["comparison_id", "model_a", "model_b", "reason", "feature_decisions"])
        _write_csv(staged / "ranking_invalid.csv", invalid_pairs, ["comparison_id", "model_a", "model_b", "feature_decisions"])
        _write_csv(staged / "feature_disagreements.csv", disagreements, ["comparison_id", "model_a", "model_b", "feature_decisions"])
        os.replace(staged, target)
    finally:
        if staged.exists():
            import shutil

            shutil.rmtree(staged)
    return graph


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(row.get(key), sort_keys=True) if isinstance(row.get(key), (dict, list)) else row.get(key) for key in fields})
