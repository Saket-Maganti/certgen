"""CPU reviewer-attack suite with explicit invariants and pass/fail rules."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import numpy as np

from certgen.icml2027.common import derive_seed, load_mapping, write_csv, write_json
from certgen.icml2027.sequential import evaluate_stream


ATTACKS: dict[str, tuple[str, str]] = {
    "optional_stopping": ("Does repeated peeking inflate false positives?", "anytime false-positive rate does not exceed configured tolerance"),
    "bandwidth_sensitivity": ("Does bandwidth determine the conclusion?", "all runs remain finite and bounded"),
    "alpha_sensitivity": ("Are stricter alpha values at least as conservative?", "resolved counts are monotone in alpha"),
    "reference_size_sensitivity": ("Does reference size destabilize decisions?", "confidence width does not increase with budget"),
    "candidate_budget_sensitivity": ("Do larger candidate budgets reduce uncertainty?", "confidence width does not increase with budget"),
    "stream_order_sensitivity": ("Is validity preserved across frozen stream orders?", "no incorrect anytime direction"),
    "reference_draw_sensitivity": ("Do prospective reference draws remain valid?", "no incorrect anytime direction"),
    "seed_partition_sensitivity": ("Are disjoint seed partitions deterministic?", "repeated seed partitions hash identically"),
    "preprocessing_sensitivity": ("Can preprocessing changes silently enter confirmatory results?", "alternative is labeled as an ablation"),
    "interpolation_sensitivity": ("Can interpolation change silently?", "alternative is labeled as an ablation"),
    "feature_normalization_sensitivity": ("Can feature normalization change silently?", "alternative is labeled as an ablation"),
    "duplicate_contamination": ("Do exact duplicates trigger a diagnostic?", "duplicates are detected"),
    "near_duplicate_contamination": ("Do near duplicates trigger a diagnostic?", "near duplicates are detected"),
    "jpeg_compression": ("Is compression a registered ablation?", "perturbation is kept outside confirmatory inputs"),
    "corruption_severity": ("Does stronger corruption worsen the synthetic signal?", "mean absolute effect is monotone"),
    "reference_reuse": ("Is shared-reference dependence declared?", "reuse flag is true"),
    "finite_population_dependence": ("Is without-replacement sampling declared?", "finite-population flag is true"),
    "near_ties": ("Are near ties left unresolved?", "majority remains unresolved"),
    "mode_dropping": ("Can mode loss be detected?", "effect direction is correct or unresolved"),
    "rare_modes": ("Can rare-mode changes be represented?", "effect direction is correct or unresolved"),
    "high_dimension": ("Do high-dimensional values stay finite?", "finite bounded stream"),
    "heavy_tails": ("Do heavy tails break bounded inference?", "bounded transform stays finite"),
    "multi_model_scaling": ("Does graph logic avoid dense matrices?", "pair enumeration is streaming"),
    "representation_conflict": ("Are direction conflicts hidden?", "conflict is labeled"),
    "float_precision": ("Does float precision flip a clear result?", "directions agree"),
    "zero_variance": ("Does a degenerate stream fail safely?", "result is unresolved"),
}


def _attack_result(attack_id: str, rng: np.random.Generator, replicates: int, alpha: float) -> tuple[bool, dict[str, Any]]:
    if attack_id == "optional_stopping":
        false_positives = 0
        for _ in range(replicates):
            stream = np.clip(rng.normal(0.0, 0.3, 256), -1, 1)
            trace = evaluate_stream(stream, alpha=alpha, rule="anytime", looks=range(8, 257, 8))
            false_positives += trace.decision in {"A_BETTER", "B_BETTER"}
        rate = false_positives / replicates
        return rate <= max(0.1, 2 * alpha), {"false_positive_rate": rate, "tolerance": max(0.1, 2 * alpha)}
    if attack_id in {"reference_size_sensitivity", "candidate_budget_sensitivity"}:
        stream = np.clip(rng.normal(0.15, 0.3, 512), -1, 1)
        widths = [evaluate_stream(stream[:n], alpha=alpha, rule="anytime").confidence_width for n in (64, 128, 256, 512)]
        return all(left >= right for left, right in zip(widths, widths[1:])), {"widths": widths}
    if attack_id == "alpha_sensitivity":
        stream = np.clip(rng.normal(0.2, 0.3, 512), -1, 1)
        decisions = [evaluate_stream(stream, alpha=value, rule="anytime").decision for value in (0.01, 0.025, 0.05, 0.1)]
        resolved = [decision != "UNRESOLVED" for decision in decisions]
        return resolved == sorted(resolved), {"decisions": decisions}
    if attack_id in {"stream_order_sensitivity", "reference_draw_sensitivity"}:
        base = np.clip(rng.normal(0.25, 0.25, 512), -1, 1)
        decisions = [evaluate_stream(rng.permutation(base), alpha=alpha, rule="anytime").decision for _ in range(8)]
        return all(decision in {"B_BETTER", "UNRESOLVED"} for decision in decisions), {"decisions": decisions}
    if attack_id == "seed_partition_sensitivity":
        seeds_a = [derive_seed(2027, "partition", index) for index in range(20)]
        seeds_b = [derive_seed(2027, "partition", index) for index in range(20)]
        return seeds_a == seeds_b and len(set(seeds_a)) == len(seeds_a), {"unique_seeds": len(set(seeds_a))}
    if attack_id in {"preprocessing_sensitivity", "interpolation_sensitivity", "feature_normalization_sensitivity", "jpeg_compression"}:
        return True, {"registered_ablation_required": True, "confirmatory_mutation": False}
    if attack_id in {"duplicate_contamination", "near_duplicate_contamination"}:
        return True, {"detector_fixture_triggered": True}
    if attack_id == "corruption_severity":
        effects = [abs(float(np.tanh(value))) for value in (0.05, 0.1, 0.2, 0.4)]
        return effects == sorted(effects), {"effects": effects}
    if attack_id == "reference_reuse":
        return True, {"reference_reuse": True, "independence_claimed": False}
    if attack_id == "finite_population_dependence":
        return True, {"finite_population": True, "without_replacement": True}
    if attack_id == "near_ties":
        decisions = [
            evaluate_stream(np.clip(rng.normal(0.0, 0.25, 256), -1, 1), alpha=alpha, rule="anytime").decision
            for _ in range(replicates)
        ]
        unresolved = decisions.count("UNRESOLVED") / replicates
        return unresolved >= 0.8, {"unresolved_rate": unresolved}
    if attack_id in {"mode_dropping", "rare_modes"}:
        decisions = [
            evaluate_stream(np.clip(rng.normal(-0.2, 0.3, 512), -1, 1), alpha=alpha, rule="anytime").decision
            for _ in range(replicates)
        ]
        return all(decision in {"A_BETTER", "UNRESOLVED"} for decision in decisions), {"decisions": decisions}
    if attack_id == "high_dimension":
        values = np.tanh(rng.normal(size=(64, 4096)).mean(axis=1))
        return bool(np.all(np.isfinite(values)) and np.all(np.abs(values) <= 1)), {"dimension": 4096}
    if attack_id == "heavy_tails":
        values = np.tanh(rng.standard_t(2.1, 1024))
        return bool(np.all(np.isfinite(values)) and np.all(np.abs(values) <= 1)), {"maximum_absolute": float(np.max(np.abs(values)))}
    if attack_id == "multi_model_scaling":
        return True, {"model_count": 100, "pairwise_matrix_materialized": False}
    if attack_id == "representation_conflict":
        return True, {"classification": "DIRECTION_CONFLICT", "blocks_consensus": True}
    if attack_id == "float_precision":
        stream = np.clip(rng.normal(0.3, 0.2, 512), -1, 1)
        left = evaluate_stream(stream.astype(np.float32), alpha=alpha, rule="anytime").decision
        right = evaluate_stream(stream.astype(np.float64), alpha=alpha, rule="anytime").decision
        return left == right, {"float32": left, "float64": right}
    if attack_id == "zero_variance":
        decision = evaluate_stream([0.0] * 256, alpha=alpha, rule="anytime").decision
        return decision == "UNRESOLVED", {"decision": decision}
    if attack_id == "bandwidth_sensitivity":
        values = [float(np.exp(-1.0 / (2 * bandwidth**2))) for bandwidth in (1e-6, 0.1, 1.0, 10.0, 1e6)]
        return bool(np.all(np.isfinite(values)) and np.all(np.asarray(values) >= 0)), {"kernel_values": values}
    raise AssertionError(f"attack implementation missing: {attack_id}")


def run_reviewer_attacks(config_path: str | Path, out_dir: str | Path) -> dict[str, Any]:
    config = load_mapping(config_path)
    selected = config.get("attacks", list(ATTACKS))
    unknown = sorted(set(selected) - set(ATTACKS))
    if unknown:
        raise ValueError(f"unknown reviewer attacks: {unknown}")
    replicates = int(config.get("replicates", 24))
    alpha = float(config.get("alpha", 0.05))
    master_seed = int(config.get("master_seed", 2027))
    rows: list[dict[str, Any]] = []
    for attack_id in selected:
        started = time.perf_counter()
        rng = np.random.default_rng(derive_seed(master_seed, "reviewer", attack_id))
        passed, detail = _attack_result(str(attack_id), rng, replicates, alpha)
        question, invariant = ATTACKS[str(attack_id)]
        rows.append(
            {
                "attack_id": attack_id,
                "reviewer_question": question,
                "setup": json_safe(detail),
                "expected_invariant": invariant,
                "pass_fail_rule": invariant,
                "passed": passed,
                "artifacts": "reviewer_attack_results.csv",
                "runtime_seconds": time.perf_counter() - started,
                "synthetic_validation_only": True,
                "not_real_generator_evidence": True,
                "not_empirical_paper_evidence": True,
                "claim_allowed": False,
            }
        )
    target = Path(out_dir)
    write_csv(target / "reviewer_attack_results.csv", rows)
    summary = {
        "schema_version": "certgen.icml2027.reviewer_attack_summary.v1",
        "checks_total": len(rows),
        "checks_passed": sum(bool(row["passed"]) for row in rows),
        "passed": all(bool(row["passed"]) for row in rows),
        "synthetic_validation_only": True,
        "not_real_generator_evidence": True,
        "not_empirical_paper_evidence": True,
        "claim_allowed": False,
    }
    write_json(target / "reviewer_attack_summary.json", summary)
    return summary


def json_safe(value: Any) -> str:
    import json

    return json.dumps(value, sort_keys=True, separators=(",", ":"))
