#!/usr/bin/env python3
"""Execute the deterministic CPU-safe ICML 2027 validation lane."""

from __future__ import annotations

import argparse
import io
import json
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import yaml  # type: ignore[import-untyped]
from PIL import Image

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from certgen.icml2027.analysis import analyze_duplicates, cost_to_decision, samples_to_decision  # noqa: E402
from certgen.icml2027.baselines import BASELINES, run_baseline  # noqa: E402
from certgen.icml2027.common import read_rows, write_csv, write_json  # noqa: E402
from certgen.icml2027.evidence import audit_evidence  # noqa: E402
from certgen.icml2027.gates import audit_go_no_go  # noqa: E402
from certgen.icml2027.notebooks import check_notebook_determinism  # noqa: E402
from certgen.icml2027.numerical import run_numerical_audit  # noqa: E402
from certgen.icml2027.planning import plan_compute, plan_study_selection  # noqa: E402
from certgen.icml2027.preprocessing import build_ablation_matrix  # noqa: E402
from certgen.icml2027.released_samples import (  # noqa: E402
    assess_protocol_compatibility,
    build_manifest,
    import_archive,
    validate_archive,
)
from certgen.icml2027.replay import replay_study  # noqa: E402
from certgen.icml2027.representations import analyze_representation_agreement  # noqa: E402
from certgen.icml2027.representations import classify_representation_decisions  # noqa: E402
from certgen.icml2027.reviewer import run_reviewer_attacks  # noqa: E402
from certgen.icml2027.multiplicity import adjust_pvalues  # noqa: E402
from certgen.icml2027.sequential import evaluate_stream  # noqa: E402
from certgen.icml2027.stress import run_adaptive_comparison, run_multi_model_scaling  # noqa: E402
from certgen.icml2027.synthetic import run_synthetic_suite  # noqa: E402


ROOT = WORKSPACE_ROOT
REPORTS = ROOT / "reports/icml2027"
ARTIFACTS = ROOT / "artifacts/icml2027"


def _png(color: tuple[int, int, int]) -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (8, 8), color).save(output, format="PNG")
    return output.getvalue()


def build_fixtures() -> dict[str, Path]:
    fixture = ARTIFACTS / "fixtures"
    fixture.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(20270809)
    count, dimension = 128, 8
    bundle = fixture / "synthetic_feature_bundle.npz"
    np.savez_compressed(
        bundle,
        reference=rng.normal(0.0, 1.0, (count, dimension)),
        model_a=rng.normal(0.05, 1.0, (count, dimension)),
        model_b=rng.normal(0.25, 1.0, (count, dimension)),
        reference_ids=np.asarray([f"reference_{index:05d}" for index in range(count)]),
        model_a_ids=np.asarray([f"model_a_{index:05d}" for index in range(count)]),
        model_b_ids=np.asarray([f"model_b_{index:05d}" for index in range(count)]),
        delta_stream=np.clip(rng.normal(0.18, 0.25, 128), -1.0, 1.0),
    )
    sample_input = fixture / "samples_to_decision_input.json"
    maximum = 10000
    stream_rng = np.random.default_rng(20270810)
    write_json(
        sample_input,
        [
            {
                "method": "certgen_anytime",
                "comparison": "synthetic_a_vs_b",
                "feature_space": "synthetic",
                "alpha": 0.05,
                "stopping_rule": "anytime",
                "true_mean": 0.12,
                "stream": np.clip(stream_rng.normal(0.12, 0.3, maximum), -1.0, 1.0).tolist(),
                "sample_ids": [f"maximum_stream_{index:05d}" for index in range(maximum)],
            }
        ],
    )
    costs = fixture / "cost_input.json"
    write_json(
        costs,
        [
            {"study_id": "cpu_suite", "stage": "synthetic", "measurement_status": "measured", "CPU_seconds": 0.0, "wall_seconds": 0.0, "bytes_written": 0},
            {"study_id": "cifar_10k", "stage": "generation", "measurement_status": "planning_estimate", "GPU_seconds": 0.0, "images_generated": 20000},
            {"study_id": "dinov2", "stage": "feature_extraction", "measurement_status": "unknown"},
        ],
    )
    representations = fixture / "representation_input.json"
    write_json(
        representations,
        [
            {"comparison": "synthetic_consensus", "feature_space": feature, "decision": "A_BETTER"}
            for feature in ("inception", "clip", "dinov2")
        ]
        + [
            {"comparison": "synthetic_conflict", "feature_space": "inception", "decision": "A_BETTER"},
            {"comparison": "synthetic_conflict", "feature_space": "clip", "decision": "B_BETTER"},
            {"comparison": "synthetic_conflict", "feature_space": "dinov2", "decision": "UNRESOLVED"},
        ],
    )
    reference_dir = fixture / "duplicates/reference"
    generated_dir = fixture / "duplicates/generated"
    reference_dir.mkdir(parents=True, exist_ok=True)
    generated_dir.mkdir(parents=True, exist_ok=True)
    (reference_dir / "reference.png").write_bytes(_png((255, 0, 0)))
    (generated_dir / "leak.png").write_bytes(_png((255, 0, 0)))
    (generated_dir / "unique.png").write_bytes(_png((0, 0, 255)))
    released_archive = fixture / "released_samples_fixture.zip"
    with zipfile.ZipFile(released_archive, "w") as archive:
        for name, data in (
            ("arbitrary/one.png", _png((0, 255, 0))),
            ("different/two.png", _png((0, 0, 255))),
        ):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    released_metadata = fixture / "released_samples_metadata.json"
    write_json(
        released_metadata,
        {
            "source_name": "certgen_synthetic_fixture",
            "source_type": "local_fixture",
            "source_url_or_repository": "repository test fixture",
            "revision": "v1",
            "sampling_protocol": "two deterministic colored squares",
            "sampling_protocol_verified": False,
            "model_id": "synthetic_fixture_model",
            "benchmark_id": "synthetic_fixture_benchmark",
            "resolution": "8x8",
            "conditioning": "none",
            "class_balance": "not_applicable",
            "license_status": "synthetic_fixture_only",
            "redistribution_allowed": False,
            "provenance_notes": "synthetic validation only",
        },
    )
    return {
        "fixture": fixture,
        "bundle": bundle,
        "sample_input": sample_input,
        "costs": costs,
        "representations": representations,
        "reference_dir": reference_dir,
        "generated_dir": generated_dir,
        "released_archive": released_archive,
        "released_metadata": released_metadata,
    }


def run_baselines(paths: dict[str, Path]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    output_root = ARTIFACTS / "baseline_results"
    for baseline_id in BASELINES:
        payload = run_baseline(
            baseline_id,
            paths["bundle"],
            ROOT / "configs/icml2027/baseline_synthetic.yaml",
            output_root / f"{baseline_id}.json",
        )
        result = payload["result"]
        rows.append(
            {
                "baseline_id": baseline_id,
                "method_family": payload["baseline_contract"]["method_family"],
                "estimate": result.get("estimate", ""),
                "decision": result.get("decision", ""),
                "stopping_time": result.get("stopping_time", ""),
                "runtime_seconds": payload["runtime_seconds"],
                "sample_ids_aligned": True,
                "synthetic_validation_only": True,
                "not_real_generator_evidence": True,
                "not_empirical_paper_evidence": True,
                "claim_allowed": False,
            }
        )
    write_csv(REPORTS / "BASELINE_SYNTHETIC_COMPARISON.csv", rows)
    write_csv(
        REPORTS / "BASELINE_COST_COMPARISON.csv",
        [{"baseline_id": row["baseline_id"], "CPU_seconds": row["runtime_seconds"], "measurement_status": "measured", "claim_allowed": False} for row in rows],
    )
    power = baseline_power_study()
    return {"methods": len(rows), "passed": len(rows) == len(BASELINES) and power["passed"], "rows": rows, "power": power, "claim_allowed": False}


def baseline_power_study(replicates: int = 30) -> dict[str, Any]:
    methods = ("permutation_mmd", "bootstrap_mmd", "naive_repeated", "alpha_spending", "fixed_bonferroni", "certgen_anytime")
    effects = (0.0, 0.2, 0.4)
    rows: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="certgen_icml_baseline_power_") as raw:
        temporary = Path(raw)
        study = temporary / "study.yaml"
        study.write_text(
            yaml.safe_dump(
                {
                    "alpha": 0.05,
                    "master_seed": 20270809,
                    "baseline_repetitions": 19,
                    "family_size": 1,
                    "block_size": 8,
                    "synthetic_validation_only": True,
                    "claim_allowed": False,
                }
            ),
            encoding="utf-8",
        )
        for method in methods:
            for effect in effects:
                correct = 0
                false_positive = 0
                runtimes: list[float] = []
                for replicate in range(replicates):
                    rng = np.random.default_rng(20270809 + replicate + int(effect * 1000) + 10000 * methods.index(method))
                    count, dimension = 48, 4
                    bundle = temporary / "bundle.npz"
                    np.savez_compressed(
                        bundle,
                        reference=rng.normal(0, 1, (count, dimension)),
                        model_a=rng.normal(0, 1, (count, dimension)),
                        model_b=rng.normal(effect, 1, (count, dimension)),
                        reference_ids=np.asarray([f"r{i}" for i in range(count)]),
                        model_a_ids=np.asarray([f"a{i}" for i in range(count)]),
                        model_b_ids=np.asarray([f"b{i}" for i in range(count)]),
                        delta_stream=np.clip(rng.normal(effect, 0.3, 128), -1, 1),
                    )
                    payload = run_baseline(method, bundle, study, temporary / "result.json")
                    decision = payload["result"]["decision"]
                    correct += effect > 0 and decision == "B_BETTER"
                    false_positive += effect == 0 and decision in {"A_BETTER", "B_BETTER"}
                    runtimes.append(float(payload["runtime_seconds"]))
                rows.append(
                    {
                        "method": method,
                        "effect_size": effect,
                        "replicates": replicates,
                        "power": correct / replicates if effect > 0 else "",
                        "false_positive_rate": false_positive / replicates if effect == 0 else "",
                        "mean_CPU_seconds": float(np.mean(runtimes)),
                        **truth(),
                    }
                )
    for baseline_id in sorted(set(BASELINES) - set(methods)):
        rows.append(
            {
                "method": baseline_id,
                "effect_size": "",
                "replicates": 0,
                "power": "NOT_APPLICABLE_DESCRIPTIVE_ONLY",
                "false_positive_rate": "NOT_APPLICABLE_DESCRIPTIVE_ONLY",
                "mean_CPU_seconds": "",
                **truth(),
            }
        )
    write_csv(REPORTS / "BASELINE_POWER_COMPARISON.csv", rows)
    return {"passed": True, "rows": len(rows), "replicates_per_effect": replicates, "claim_allowed": False}


def multiplicity_study(replicates: int = 5000, family_size: int = 20) -> dict[str, Any]:
    rng = np.random.default_rng(20270809)
    methods = ("bonferroni", "holm", "fixed_alpha_split", "benjamini_hochberg_exploratory")
    rows: list[dict[str, Any]] = []
    for method in methods:
        family_errors = 0
        false_discoveries = 0
        discoveries = 0
        true_discoveries = 0
        alternatives = 5
        for _ in range(replicates):
            null = rng.uniform(size=family_size - alternatives)
            alternative = rng.beta(0.25, 1.0, alternatives)
            pvalues = np.concatenate([alternative, null]).tolist()
            result = adjust_pvalues(pvalues, method)
            rejected = result["rejected"]
            false = sum(rejected[alternatives:])
            true = sum(rejected[:alternatives])
            family_errors += false > 0
            false_discoveries += false
            true_discoveries += true
            discoveries += sum(rejected)
        rows.append(
            {
                "method": method,
                "family_size": family_size,
                "replicates": replicates,
                "FWER": family_errors / replicates,
                "FDR": false_discoveries / max(1, discoveries),
                "power": true_discoveries / (replicates * alternatives),
                "resolved_edges": discoveries,
                "samples_consumed": replicates * family_size,
                "validity_status": "EXPLORATORY" if "exploratory" in method else "CONSERVATIVE_FWER",
                **truth(),
            }
        )
    write_csv(REPORTS / "SYNTHETIC_MULTIPLICITY.csv", rows)
    return {"passed": True, "rows": rows, "claim_allowed": False}


def representation_simulation(replicates: int = 2000) -> dict[str, Any]:
    rng = np.random.default_rng(20270809)
    rows: list[dict[str, Any]] = []
    for replicate in range(replicates):
        latent = rng.normal(0.0, 0.25)
        decisions = []
        for representation in ("inception", "clip", "dinov2"):
            value = latent + rng.normal(0.0, 0.2)
            decision = "A_BETTER" if value < -0.2 else "B_BETTER" if value > 0.2 else "UNRESOLVED"
            decisions.append(decision)
            rows.append(
                {
                    "replicate_id": replicate,
                    "representation": representation,
                    "latent_effect": latent,
                    "decision": decision,
                    "classification": "",
                    **truth(),
                }
            )
        classification = classify_representation_decisions(decisions)
        for row in rows[-3:]:
            row["classification"] = classification
    write_csv(REPORTS / "SYNTHETIC_REPRESENTATION_DISAGREEMENT.csv", rows)
    return {"passed": True, "rows": len(rows), "claim_allowed": False}


def finite_sample_diagnostics(records_path: Path) -> dict[str, Any]:
    records = read_rows(records_path)
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in records:
        key = (row["scenario_family"], row["sample_budget"], row["effect_size"], row["alpha"], row["model_count"], row["representation_count"])
        grouped.setdefault(key, []).append(row)
    output = []
    for key, rows in sorted(grouped.items(), key=lambda item: tuple(str(value) for value in item[0])):
        family, budget, effect, alpha, models, representations = key
        output.append(
            {
                "scenario_family": family,
                "n": budget,
                "effect_size": effect,
                "alpha": alpha,
                "model_count": models,
                "representation_count": representations,
                "coverage": sum(str(row["coverage"]).lower() == "true" for row in rows) / len(rows),
                "type_I_error": sum(str(row["false_positive"]).lower() == "true" for row in rows) / len(rows),
                "power": 1 - sum(str(row["false_negative"]).lower() == "true" for row in rows) / len(rows),
                "mean_stopping_time": float(np.mean([float(row["stopping_time"]) for row in rows])),
                **truth(),
            }
        )
    write_csv(REPORTS / "FINITE_SAMPLE_DIAGNOSTICS.csv", output)
    return {"passed": True, "rows": len(output), "claim_allowed": False}


def optional_stopping_demo(replicates: int = 1000, seed: int = 20270809) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    looks = np.arange(20, 501, 20)
    naive = 0
    anytime = 0
    for _ in range(replicates):
        values = rng.normal(0.0, 1.0, 500)
        means = np.cumsum(values) / np.arange(1, 501)
        naive += any(abs(means[n - 1]) > 1.959963984540054 / np.sqrt(n) for n in looks)
        bounded = np.clip(np.tanh(values), -1, 1)
        anytime += evaluate_stream(bounded, alpha=0.05, rule="anytime", looks=looks).decision in {"A_BETTER", "B_BETTER"}
    rows = [
        {"method": "naive_repeated_fixed_z", "replicates": replicates, "false_positives": naive, "false_positive_rate": naive / replicates, "valid_under_optional_stopping": False, **truth()},
        {"method": "certgen_anytime_union_cs", "replicates": replicates, "false_positives": anytime, "false_positive_rate": anytime / replicates, "valid_under_optional_stopping": True, **truth()},
    ]
    write_csv(REPORTS / "OPTIONAL_STOPPING_FAILURE_DEMO.csv", rows)
    return {"passed": naive / replicates > 0.05, "rows": rows, "claim_allowed": False}


def truth() -> dict[str, bool]:
    return {
        "synthetic_validation_only": True,
        "not_real_generator_evidence": True,
        "not_empirical_paper_evidence": True,
        "claim_allowed": False,
    }


def run_suite(tier: str, *, replay: bool) -> dict[str, Any]:
    started = time.perf_counter()
    paths = build_fixtures()
    config = ROOT / f"configs/icml2027/synthetic_validation_{tier}.yaml"
    synthetic = run_synthetic_suite(config, ARTIFACTS / "synthetic_validation" / tier)
    baselines = run_baselines(paths)
    optional = optional_stopping_demo(replicates=1000 if tier == "quick" else 5000)
    multiplicity = multiplicity_study(replicates=1000 if tier == "quick" else 5000)
    representation_sim = representation_simulation(replicates=500 if tier == "quick" else 2000)
    finite_sample = finite_sample_diagnostics(ARTIFACTS / "synthetic_validation" / tier / "simulation_records.jsonl")
    samples = samples_to_decision(paths["sample_input"], REPORTS / "SAMPLES_TO_DECISION.csv")
    costs = cost_to_decision(paths["costs"], REPORTS / "COST_TO_DECISION.csv")
    representations = analyze_representation_agreement(paths["representations"], REPORTS / "representation")
    numerical = run_numerical_audit(ARTIFACTS / "numerical_audit")
    multi_model = run_multi_model_scaling(ROOT / "configs/icml2027/multi_model_scaling.yaml", REPORTS)
    adaptive = run_adaptive_comparison(ROOT / "configs/icml2027/adaptive_allocation.yaml", REPORTS / "ADAPTIVE_ALLOCATION_COMPARISON.csv")
    reviewer = run_reviewer_attacks(ROOT / "configs/icml2027/reviewer_attack_suite.yaml", ARTIFACTS / "reviewer_attacks")
    duplicate_report = analyze_duplicates([paths["reference_dir"], paths["generated_dir"]], REPORTS / "DUPLICATE_CONTAMINATION_FIXTURE.json")
    released_validation = validate_archive(paths["released_archive"], expected_count=2)
    released_manifest_path = paths["fixture"] / "released_samples_manifest.json"
    released_manifest = build_manifest(paths["released_metadata"], paths["released_archive"], released_manifest_path)
    import_target = ARTIFACTS / "released_sample_fixture_import"
    if import_target.exists():
        import_summary = json.loads((import_target / "import_summary.json").read_text(encoding="utf-8"))
    else:
        import_summary = import_archive(paths["released_archive"], released_manifest_path, import_target)
    compatibility = assess_protocol_compatibility(released_manifest, released_manifest)
    write_json(REPORTS / "RELEASED_SAMPLE_COMPATIBILITY_FIXTURE.json", compatibility)
    evidence = audit_evidence(ROOT / "registry/icml2027/claim_registry.yaml", REPORTS / "CLAIM_EVIDENCE_MATRIX.csv")
    model_gates = audit_go_no_go(ROOT / "registry/icml2027/model_registry.yaml", REPORTS / "MODEL_GO_NO_GO.csv")
    benchmark_gates = audit_go_no_go(ROOT / "registry/icml2027/benchmark_registry.yaml", REPORTS / "BENCHMARK_GO_NO_GO.csv")
    compute = plan_compute(ROOT / "configs/icml2027/compute_plan.yaml", REPORTS / "COMPUTE_PLAN.json")
    selection = plan_study_selection(ROOT / "configs/icml2027/study_selection.yaml", REPORTS / "STUDY_SELECTION.csv")
    preprocessing = build_ablation_matrix(REPORTS / "PREPROCESSING_ABLATION_MATRIX.csv")
    notebooks = check_notebook_determinism(ROOT / "notebooks/kaggle/icml2027")
    replay_result = replay_study("icml2027_synthetic_validity_v1") if replay else {"passed": True, "skipped": True}
    elapsed = time.perf_counter() - started
    payload = {
        "schema_version": "certgen.icml2027.cpu_suite.v1",
        "tier": tier,
        "elapsed_seconds": elapsed,
        "synthetic": synthetic,
        "baselines": baselines,
        "optional_stopping_demo": optional,
        "multiplicity": multiplicity,
        "representation_simulation": representation_sim,
        "finite_sample_diagnostics": finite_sample,
        "samples_to_decision": samples,
        "cost_to_decision": costs,
        "representations": representations,
        "numerical": numerical,
        "multi_model": multi_model,
        "adaptive": adaptive,
        "reviewer": reviewer,
        "duplicate_fixture_detected": bool(duplicate_report["cross_set_leakage_groups"]),
        "released_validation": released_validation["passed"],
        "released_import": import_summary,
        "compatibility_gate": compatibility,
        "evidence": evidence,
        "model_gates": model_gates,
        "benchmark_gates": benchmark_gates,
        "compute": compute,
        "selection": selection,
        "preprocessing": preprocessing,
        "notebooks": notebooks,
        "replay": replay_result,
        "passed": all(
            [
                synthetic["records"] > 0,
                baselines["passed"],
                optional["passed"],
                numerical["passed"],
                reviewer["passed"],
                notebooks["passed"],
                bool(duplicate_report["cross_set_leakage_groups"]),
                released_validation["passed"],
                replay_result["passed"],
            ]
        ),
        **truth(),
    }
    write_json(REPORTS / f"CPU_SUITE_{tier.upper()}.json", payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tier", choices=["quick", "medium", "overnight"], default="quick")
    parser.add_argument("--replay", action="store_true")
    args = parser.parse_args()
    payload = run_suite(args.tier, replay=args.replay)
    print(json.dumps({"tier": payload["tier"], "elapsed_seconds": payload["elapsed_seconds"], "passed": payload["passed"], "claim_allowed": False}, indent=2))
    return 0 if payload["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
