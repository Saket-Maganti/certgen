"""Synthetic graph-scaling and exploratory adaptive-allocation studies."""

from __future__ import annotations

import itertools
import resource
import time
from pathlib import Path
from typing import Any

import numpy as np

from certgen.icml2027.adaptive import POLICY_VALIDITY, select_edge
from certgen.icml2027.common import derive_seed, load_mapping, write_csv, write_json
from certgen.icml2027.ranking import connected_components, strongly_connected_components, transitive_reduction
from certgen.icml2027.sequential import evaluate_stream


def _edge_stream(
    rng: np.random.Generator, difference: float, budget: int, *, noise_scale: float = 0.35
) -> np.ndarray:
    return np.clip(np.tanh(rng.normal(difference, noise_scale, budget)), -1.0, 1.0)


def _reachability(edges: list[tuple[str, str]], nodes: list[str]) -> set[tuple[str, str]]:
    adjacency: dict[str, set[str]] = {node: set() for node in nodes}
    for source, target in edges:
        adjacency[source].add(target)
    closure: set[tuple[str, str]] = set()
    for source in nodes:
        stack = list(adjacency[source])
        while stack:
            target = stack.pop()
            if (source, target) in closure:
                continue
            closure.add((source, target))
            stack.extend(adjacency[target])
    return closure


def run_multi_model_scaling(config_path: str | Path, out_dir: str | Path) -> dict[str, Any]:
    config = load_mapping(config_path)
    master_seed = int(config.get("master_seed", 2027))
    model_counts = [int(value) for value in config.get("model_counts", [2, 5, 10, 20, 50, 100])]
    replicates = int(config.get("replicates", 2))
    budget = int(config.get("sample_budget", 128))
    alpha = float(config.get("alpha", 0.05))
    effect_spacing = float(config.get("effect_spacing", 0.08))
    scenarios = [str(value) for value in config.get("scenarios", ["ordered_homoskedastic"])]
    rows: list[dict[str, Any]] = []
    for scenario, model_count in itertools.product(scenarios, model_counts):
        node_ids = [f"model_{index:03d}" for index in range(model_count)]
        comparisons = list(itertools.combinations(range(model_count), 2))
        edge_alpha = alpha / max(1, len(comparisons))
        for replicate in range(replicates):
            started = time.perf_counter()
            rng = np.random.default_rng(derive_seed(master_seed, "multi_model", scenario, model_count, replicate))
            if scenario in {"ordered_homoskedastic", "uniformly_spaced"}:
                true_scores = np.arange(model_count, dtype=float) * effect_spacing
                noise_scale = 0.35
            elif scenario in {"near_tie_clusters", "clustered_quality_tiers", "partial_incomparability"}:
                true_scores = (np.arange(model_count, dtype=float) // 5) * effect_spacing
                noise_scale = 0.35
            elif scenario in {"many_near_ties", "representation_specific_ordering", "representation_conflicts", "adversarial_local_cycles"}:
                true_scores = np.arange(model_count, dtype=float) * (effect_spacing * 0.1)
                noise_scale = 0.45
            elif scenario == "one_dominant_dense_middle":
                true_scores = np.arange(model_count, dtype=float) * (effect_spacing * 0.08)
                true_scores[-1] = effect_spacing * max(10.0, model_count / 2.0)
                noise_scale = 0.45
            elif scenario == "few_easy_many_hard_edges":
                true_scores = np.arange(model_count, dtype=float) * (effect_spacing * 0.03)
                if model_count >= 2:
                    true_scores[-1] = effect_spacing * 8.0
                    true_scores[-2] = effect_spacing * 4.0
                noise_scale = 0.5
            elif scenario in {"heteroskedastic_edges", "heterogeneous_variance"}:
                true_scores = np.arange(model_count, dtype=float) * effect_spacing
                noise_scale = 0.65
            elif scenario in {"difficult_covariance", "shared_reference_dependence"}:
                true_scores = np.arange(model_count, dtype=float) * (effect_spacing * 0.5)
                noise_scale = 0.8
            elif scenario in {"heterogeneous_sample_cost", "mixed_easy_hard_edges"}:
                true_scores = np.arange(model_count, dtype=float) * effect_spacing
                noise_scale = 0.45
            else:
                raise ValueError(f"unknown multi-model scenario: {scenario}")
            certified: list[tuple[str, str]] = []
            incorrect = 0
            resolved = 0
            samples = 0
            sample_cost = 0.0
            shared_reference_noise = (
                rng.normal(0.0, 0.35, budget) if scenario == "shared_reference_dependence" else None
            )
            for left, right in comparisons:
                difference = float(true_scores[right] - true_scores[left])
                if scenario == "representation_specific_ordering" and (left + right) % 5 == 0:
                    difference *= -1.0
                if scenario == "representation_conflicts" and (left + right) % 3 == 0:
                    difference *= -1.0
                if scenario == "adversarial_local_cycles" and left == 0 and right == 2:
                    difference = -max(effect_spacing, abs(difference))
                if scenario == "mixed_easy_hard_edges" and (left + right) % 2:
                    difference *= 0.05
                edge_noise = noise_scale
                if scenario in {"heteroskedastic_edges", "heterogeneous_variance"}:
                    edge_noise *= 0.5 + 1.5 * ((left + right) % 5) / 4.0
                if scenario == "partial_incomparability" and left // 5 == right // 5:
                    difference = 0.0
                edge_values = _edge_stream(rng, difference, budget, noise_scale=edge_noise)
                if shared_reference_noise is not None:
                    edge_values = np.clip(np.tanh(np.arctanh(np.clip(edge_values, -0.999999, 0.999999)) + shared_reference_noise), -1.0, 1.0)
                trace = evaluate_stream(
                    edge_values,
                    alpha=edge_alpha,
                    rule="anytime",
                    looks=range(16, budget + 1, 16),
                    true_mean=float(np.tanh(difference)),
                )
                samples += trace.stopping_time
                cost_multiplier = 1.0 + ((left + right) % 4) if scenario == "heterogeneous_sample_cost" else 1.0
                sample_cost += trace.stopping_time * cost_multiplier
                if trace.decision in {"A_BETTER", "B_BETTER"}:
                    resolved += 1
                    expected = "UNRESOLVED" if abs(difference) < 1e-12 else (
                        "B_BETTER" if difference > 0.0 else "A_BETTER"
                    )
                    if trace.decision != expected:
                        incorrect += 1
                        if trace.decision == "A_BETTER":
                            certified.append((node_ids[right], node_ids[left]))
                        else:
                            certified.append((node_ids[left], node_ids[right]))
                    else:
                        certified.append((node_ids[left], node_ids[right]))
            cycles = [component for component in strongly_connected_components(certified, node_ids) if len(component) > 1]
            reduction = [] if cycles else transitive_reduction(certified, node_ids)
            reduction_edges = len(reduction)
            reduction_correct = not cycles and _reachability(certified, node_ids) == _reachability(reduction, node_ids)
            components = connected_components(certified, node_ids)
            elapsed = time.perf_counter() - started
            peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
            rows.append(
                {
                    "scenario": scenario,
                    "model_count": model_count,
                    "replicate_id": replicate,
                    "number_of_comparisons": len(comparisons),
                    "resolved_edges": resolved,
                    "unresolved_edges": len(comparisons) - resolved,
                    "incorrect_edges": incorrect,
                    "graph_density": resolved / max(1, len(comparisons)),
                    "transitive_reduction_edges": reduction_edges,
                    "transitive_reduction_correct": reduction_correct,
                    "cycles": len(cycles),
                    "connected_components": len(components),
                    "FWER_event": incorrect > 0,
                    "samples_consumed": samples,
                    "sample_cost_units": sample_cost,
                    "cost_per_certified_edge": sample_cost / max(1, resolved),
                    "CPU_seconds": elapsed,
                    "memory_peak_platform_units": peak,
                    "pairwise_matrix_materialized": False,
                    "synthetic_validation_only": True,
                    "not_real_generator_evidence": True,
                    "not_empirical_paper_evidence": True,
                    "claim_allowed": False,
                }
            )
    target = Path(out_dir)
    write_csv(target / "MULTI_MODEL_SCALING.csv", rows)
    summary = {
        "schema_version": "certgen.icml2027.multi_model_scaling.v1",
        "rows": len(rows),
        "model_counts": model_counts,
        "scenarios": scenarios,
        "FWER": sum(bool(row["FWER_event"]) for row in rows) / max(1, len(rows)),
        "incorrect_edges": sum(int(row["incorrect_edges"]) for row in rows),
        "maximum_models": max(model_counts),
        "transitive_reduction_failures": sum(not bool(row["transitive_reduction_correct"]) for row in rows),
        "synthetic_validation_only": True,
        "not_real_generator_evidence": True,
        "not_empirical_paper_evidence": True,
        "claim_allowed": False,
    }
    write_json(target / "MULTI_MODEL_SCALING_SUMMARY.json", summary)
    return summary


def _adaptive_once(
    policy: str,
    *,
    model_count: int,
    chunk_size: int,
    maximum_samples: int,
    alpha: float,
    seed: int,
) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    scores = np.linspace(0.0, 0.5, model_count)
    pairs = list(itertools.combinations(range(model_count), 2))
    edge_alpha = alpha / len(pairs)
    states: list[dict[str, Any]] = [
        {
            "source": f"model_{left}",
            "target": f"model_{right}",
            "left": left,
            "right": right,
            "samples": 0,
            "values": [],
            "estimate": 0.0,
            "width": float("inf"),
            "resolved": False,
            "decision": "UNRESOLVED",
            "cost": 1.0 + ((left + right) % 4),
        }
        for left, right in pairs
    ]
    total = 0
    total_cost = 0.0
    step = 0
    while total < maximum_samples and any(not state["resolved"] for state in states):
        index = select_edge(states, policy, step=step)
        state = states[index]
        remaining = maximum_samples - total
        amount = min(chunk_size, remaining)
        difference = float(scores[int(state["right"])] - scores[int(state["left"])])
        values = _edge_stream(rng, difference, amount).tolist()
        state["values"].extend(values)
        state["samples"] = len(state["values"])
        trace = evaluate_stream(
            state["values"],
            alpha=edge_alpha,
            rule="anytime",
            true_mean=float(np.tanh(difference)),
        )
        state["estimate"] = trace.mean
        state["width"] = trace.confidence_width
        state["decision"] = trace.decision
        state["resolved"] = trace.decision in {"A_BETTER", "B_BETTER"}
        total += amount
        total_cost += amount * float(state["cost"])
        step += 1
    resolved = [state for state in states if state["resolved"]]
    incorrect = sum(str(state["decision"]) != "B_BETTER" for state in resolved)
    resolved_models = {
        node for state in resolved for node in (str(state["source"]), str(state["target"]))
    }
    return {
        "policy": policy,
        "validity_status": POLICY_VALIDITY[policy],
        "model_count": model_count,
        "edge_count": len(states),
        "resolved_edges": len(resolved),
        "unresolved_edges": len(states) - len(resolved),
        "incorrect_edges": incorrect,
        "samples_consumed": total,
        "sample_cost_units": total_cost,
        "cost_per_certified_edge": total_cost / max(1, len(resolved)),
        "cost_per_resolved_model": total_cost / max(1, len(resolved_models)),
        "graph_coverage": len(resolved) / len(states),
        "confirmatory_eligible": POLICY_VALIDITY[policy] in {"VALIDITY_PROVEN", "VALIDITY_INHERITED"},
        "synthetic_validation_only": True,
        "not_real_generator_evidence": True,
        "not_empirical_paper_evidence": True,
        "claim_allowed": False,
    }


def run_adaptive_comparison(config_path: str | Path, out_path: str | Path) -> dict[str, Any]:
    config = load_mapping(config_path)
    policies = list(config.get("policies", POLICY_VALIDITY))
    replicates = int(config.get("replicates", 4))
    master_seed = int(config.get("master_seed", 2027))
    rows: list[dict[str, Any]] = []
    for policy in policies:
        for replicate in range(replicates):
            result = _adaptive_once(
                str(policy),
                model_count=int(config.get("model_count", 8)),
                chunk_size=int(config.get("chunk_size", 16)),
                maximum_samples=int(config.get("maximum_samples", 20_000)),
                alpha=float(config.get("alpha", 0.05)),
                seed=derive_seed(master_seed, "adaptive", policy, replicate),
            )
            result["replicate_id"] = replicate
            rows.append(result)
    target = Path(out_path)
    write_csv(target, rows)
    summary = {
        "schema_version": "certgen.icml2027.adaptive_comparison.v1",
        "rows": len(rows),
        "policies": policies,
        "invalid_confirmatory_promotions": sum(
            row["validity_status"] == "EXPLORATORY_NOT_PROVEN" and row["confirmatory_eligible"] for row in rows
        ),
        "synthetic_validation_only": True,
        "not_real_generator_evidence": True,
        "not_empirical_paper_evidence": True,
        "claim_allowed": False,
    }
    write_json(target.with_suffix(".summary.json"), summary)
    return summary
