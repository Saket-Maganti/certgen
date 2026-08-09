"""Deterministic CPU Monte Carlo studies for prospective ICML 2027 contracts."""

from __future__ import annotations

import itertools
import math
import os
import time
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np

from certgen.icml2027.common import derive_seed, load_mapping, stable_hash, write_csv, write_json, write_jsonl
from certgen.icml2027.sequential import evaluate_stream


RECORD_FIELDS = (
    "simulation_id",
    "scenario_id",
    "scenario_family",
    "replicate_id",
    "seed",
    "dimension",
    "sample_budget",
    "effect_size",
    "alpha",
    "kernel",
    "bandwidth",
    "stopping_rule",
    "multiplicity_rule",
    "representation_count",
    "model_count",
    "reference_reuse",
    "decision",
    "stopping_time",
    "coverage",
    "false_positive",
    "false_negative",
    "runtime_seconds",
    "true_mean",
    "confidence_width",
    "synthetic_validation_only",
    "not_real_generator_evidence",
    "not_empirical_paper_evidence",
    "claim_allowed",
)


def _scenario_mean(family: str, effect: float) -> float:
    direction = -1.0 if family in {"mode_dropping", "rare_mode_change", "tail_shift"} else 1.0
    return direction * effect


def _draw_stream(rng: np.random.Generator, scenario: dict[str, Any]) -> np.ndarray:
    n = int(scenario["sample_budget"])
    family = str(scenario["family"])
    effect = float(scenario.get("effect_size", 0.0))
    mean = _scenario_mean(family, effect)
    if family in {"null_calibration", "optional_stopping", "finite_reference_population", "reference_reuse"}:
        mean = 0.0
    if family == "heavy_tailed":
        raw = rng.standard_t(df=2.5, size=n) * 0.35 + mean
    elif family == "mixture_weight_shift":
        component = rng.random(n) < min(0.95, 0.5 + effect)
        raw = np.asarray(rng.normal(loc=np.where(component, 0.35, -0.35), scale=0.3, size=n), dtype=float)
        raw -= float(raw.mean()) - mean
    elif family == "mode_dropping":
        component = rng.random(n) < max(0.05, 0.5 - effect)
        raw = np.asarray(rng.normal(loc=np.where(component, 0.45, -0.45), scale=0.25, size=n), dtype=float)
        raw -= float(raw.mean()) - mean
    elif family == "rare_mode_change":
        rare = rng.random(n) < 0.03
        raw = rng.normal(mean, 0.3, n) + rare * rng.normal(-min(1.0, effect * 5), 0.1, n)
    elif family == "tail_shift":
        raw = rng.normal(mean, 0.25, n)
        raw += (rng.random(n) < 0.05) * rng.exponential(max(effect, 0.01), n)
        raw -= float(raw.mean()) - mean
    elif family == "multimodal_separation":
        raw = rng.normal(rng.choice([-0.4, 0.4], size=n) + mean, 0.2)
    elif family == "covariance_shift":
        raw = rng.normal(mean, min(0.7, 0.3 + effect), n)
    else:
        raw = rng.normal(mean, 0.35, n)
    if family == "finite_reference_population":
        population = np.tanh(rng.normal(0.0, 0.35, max(32, n // 2)))
        raw = rng.choice(population, size=n, replace=False if n <= len(population) else True)
    elif family == "reference_reuse":
        shared = rng.normal(0.0, 0.18, max(1, math.ceil(n / 8)))
        raw = raw + np.repeat(shared, 8)[:n]
    return np.clip(np.tanh(raw), -1.0, 1.0)


def _run_one(task: tuple[dict[str, Any], int, int]) -> dict[str, Any]:
    scenario, replicate_id, master_seed = task
    scenario_id = str(scenario["scenario_id"])
    seed = derive_seed(master_seed, scenario_id, replicate_id)
    rng = np.random.default_rng(seed)
    started = time.perf_counter()
    stream = _draw_stream(rng, scenario)
    family = str(scenario["family"])
    true_mean = 0.0 if family in {
        "null_calibration", "optional_stopping", "finite_reference_population", "reference_reuse"
    } else _scenario_mean(family, float(scenario.get("effect_size", 0.0)))
    rule = str(scenario.get("stopping_rule", "anytime"))
    looks = scenario.get("looks") or list(range(int(scenario.get("look_step", 10)), len(stream) + 1, int(scenario.get("look_step", 10))))
    trace = evaluate_stream(
        stream,
        alpha=float(scenario.get("alpha", 0.05)),
        rule=rule,
        looks=looks,
        true_mean=true_mean,
        equivalence_margin=scenario.get("equivalence_margin"),
    )
    positive = trace.decision in {"A_BETTER", "B_BETTER"}
    expected_direction = "B_BETTER" if true_mean > 0 else "A_BETTER" if true_mean < 0 else None
    false_positive = true_mean == 0.0 and positive
    false_negative = true_mean != 0.0 and trace.decision != expected_direction
    return {
        "simulation_id": stable_hash({"scenario": scenario_id, "replicate": replicate_id, "seed": seed})[:20],
        "scenario_id": scenario_id,
        "scenario_family": family,
        "replicate_id": replicate_id,
        "seed": seed,
        "dimension": int(scenario.get("dimension", 16)),
        "sample_budget": len(stream),
        "effect_size": float(scenario.get("effect_size", 0.0)),
        "alpha": float(scenario.get("alpha", 0.05)),
        "kernel": str(scenario.get("kernel", "rbf")),
        "bandwidth": scenario.get("bandwidth", "median"),
        "stopping_rule": rule,
        "multiplicity_rule": str(scenario.get("multiplicity_rule", "bonferroni")),
        "representation_count": int(scenario.get("representation_count", 1)),
        "model_count": int(scenario.get("model_count", 2)),
        "reference_reuse": bool(scenario.get("reference_reuse", family == "reference_reuse")),
        "decision": trace.decision,
        "stopping_time": trace.stopping_time,
        "coverage": trace.coverage,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "runtime_seconds": time.perf_counter() - started,
        "true_mean": true_mean,
        "confidence_width": trace.confidence_width,
        "synthetic_validation_only": True,
        "not_real_generator_evidence": True,
        "not_empirical_paper_evidence": True,
        "claim_allowed": False,
    }


def _scenario_grid(config: dict[str, Any]) -> list[dict[str, Any]]:
    tier = str(config.get("tier", "quick"))
    defaults = dict(config.get("defaults", {}))
    scenarios: list[dict[str, Any]] = []
    for raw in config.get("scenarios", []):
        if not isinstance(raw, dict):
            raise ValueError("each synthetic scenario must be a mapping")
        scenario = {**defaults, **raw}
        enabled_tiers = scenario.pop("tiers", ["quick", "medium", "overnight"])
        if tier not in enabled_tiers:
            continue
        expand = scenario.pop("expand", {})
        keys = sorted(expand)
        values = [expand[key] for key in keys]
        for combination in itertools.product(*values) if keys else [()]:
            resolved = {**scenario, **dict(zip(keys, combination, strict=True))}
            suffix = "__".join(f"{key}-{resolved[key]}" for key in keys)
            resolved["scenario_id"] = str(resolved["scenario_id"]) + (f"__{suffix}" if suffix else "")
            scenarios.append(resolved)
    identifiers = [str(scenario["scenario_id"]) for scenario in scenarios]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("expanded scenario IDs must be unique")
    return scenarios


def _summary(records: list[dict[str, Any]], *, config_hash: str, elapsed: float, tier: str) -> dict[str, Any]:
    families: dict[str, dict[str, Any]] = {}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[str(record["scenario_family"])].append(record)
    for family, rows in sorted(grouped.items()):
        families[family] = {
            "records": len(rows),
            "false_positive_rate": sum(bool(row["false_positive"]) for row in rows) / len(rows),
            "false_negative_rate": sum(bool(row["false_negative"]) for row in rows) / len(rows),
            "coverage_rate": sum(bool(row["coverage"]) for row in rows) / len(rows),
            "decision_counts": dict(sorted(Counter(str(row["decision"]) for row in rows).items())),
            "mean_stopping_time": float(np.mean([int(row["stopping_time"]) for row in rows])),
        }
    return {
        "schema_version": "certgen.icml2027.synthetic_summary.v1",
        "tier": tier,
        "config_hash": config_hash,
        "records": len(records),
        "scenarios": len({record["scenario_id"] for record in records}),
        "families": families,
        "elapsed_seconds": elapsed,
        "synthetic_validation_only": True,
        "not_real_generator_evidence": True,
        "not_empirical_paper_evidence": True,
        "claim_allowed": False,
    }


def _write_tidy_reports(records: list[dict[str, Any]], report_root: Path) -> None:
    routes = {
        "SYNTHETIC_NULL_CALIBRATION.csv": {"null_calibration"},
        "SYNTHETIC_POWER_CURVES.csv": {
            "mean_shift", "covariance_shift", "mixture_weight_shift", "mode_dropping",
            "rare_mode_change", "tail_shift", "multimodal_separation", "heavy_tailed",
        },
        "SYNTHETIC_STOPPING_TIME.csv": {"optional_stopping", "null_calibration", "mean_shift"},
        "SYNTHETIC_MULTIPLICITY.csv": {"multiplicity"},
        "SYNTHETIC_REFERENCE_REUSE.csv": {"reference_reuse", "finite_reference_population"},
        "SYNTHETIC_REPRESENTATION_DISAGREEMENT.csv": {"representation_disagreement"},
        "SYNTHETIC_MULTI_MODEL_RANKING.csv": {"multi_model_ranking"},
        "SYNTHETIC_ADAPTIVE_ALLOCATION.csv": {"adaptive_allocation"},
    }
    for name, families in routes.items():
        write_csv(report_root / name, [row for row in records if row["scenario_family"] in families], RECORD_FIELDS)


def run_synthetic_suite(config_path: str | Path, out_dir: str | Path) -> dict[str, Any]:
    config = load_mapping(config_path)
    if config.get("claim_allowed") is not False:
        raise ValueError("synthetic config must set claim_allowed=false")
    master_seed = int(config.get("master_seed", 20270809))
    scenarios = _scenario_grid(config)
    tier = str(config.get("tier", "quick"))
    replicates_default = int(config.get("replicates", 32))
    tasks = [
        (scenario, replicate_id, master_seed)
        for scenario in scenarios
        for replicate_id in range(int(scenario.get("replicates", replicates_default)))
    ]
    started = time.perf_counter()
    workers = max(1, min(int(config.get("workers", os.cpu_count() or 1)), len(tasks) or 1))
    if workers == 1:
        records = [_run_one(task) for task in tasks]
    else:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            records = list(executor.map(_run_one, tasks, chunksize=max(1, len(tasks) // (workers * 8))))
    records.sort(key=lambda row: (str(row["scenario_id"]), int(row["replicate_id"])))
    elapsed = time.perf_counter() - started
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    config_hash = stable_hash(config)
    write_jsonl(output / "simulation_records.jsonl", records)
    summary = _summary(records, config_hash=config_hash, elapsed=elapsed, tier=tier)
    write_json(output / "summary.json", summary)
    report_root = Path(config.get("report_root", "reports/icml2027"))
    write_json(report_root / "SYNTHETIC_VALIDATION_SUMMARY.json", summary)
    _write_tidy_reports(records, report_root)
    return summary
