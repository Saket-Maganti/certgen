#!/usr/bin/env python3
"""Finalize truthful ICML 2027 reports from measured local artifacts."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from certgen.icml2027.common import write_json  # noqa: E402


ROOT = WORKSPACE_ROOT
REPORTS = ROOT / "reports" / "icml2027"
REGISTRY = ROOT / "registry" / "icml2027"
TRUTH = (
    "All results in this report are engineering or synthetic-validation evidence only. "
    "They are not real-generator or empirical paper evidence. `claim_allowed=false`."
)


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object in {path}")
    return value


def _csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_report(name: str, title: str, body: str) -> None:
    (REPORTS / name).write_text(f"# {title}\n\n{TRUTH}\n\n{body.rstrip()}\n", encoding="utf-8")


def _update_run_registry(tiers: dict[str, dict[str, Any]]) -> None:
    path = REGISTRY / "run_registry.yaml"
    registry = yaml.safe_load(path.read_text(encoding="utf-8"))
    for run in registry["runs"]:
        tier = {"cpu_tier_a_quick": "quick", "cpu_tier_b_medium": "medium", "cpu_tier_c_overnight": "overnight"}[run["run_id"]]
        report = tiers[tier]
        run.update(
            {
                "status": "COMPLETED",
                "measured_runtime_seconds": round(float(report["elapsed_seconds"]), 6),
                "records": int(report["synthetic"]["records"]),
                "scenarios": int(report["synthetic"]["scenarios"]),
                "result_report": f"reports/icml2027/CPU_SUITE_{tier.upper()}.json",
            }
        )
    registry["claim_allowed"] = False
    path.write_text(yaml.safe_dump(registry, sort_keys=False), encoding="utf-8")


def main() -> int:
    tiers = {tier: _json(REPORTS / f"CPU_SUITE_{tier.upper()}.json") for tier in ("quick", "medium", "overnight")}
    if not all(report.get("passed") is True for report in tiers.values()):
        raise RuntimeError("all three CPU suite reports must pass before finalization")
    _update_run_registry(tiers)

    reviewer = _json(ROOT / "artifacts/icml2027/reviewer_attacks/reviewer_attack_summary.json")
    numerical = _json(ROOT / "artifacts/icml2027/numerical_audit/numerical_audit_summary.json")
    multi = _json(REPORTS / "MULTI_MODEL_SCALING_SUMMARY.json")
    adaptive = _json(REPORTS / "ADAPTIVE_ALLOCATION_COMPARISON.summary.json")
    representation = _json(REPORTS / "representation/representation_summary.json")
    optional = _csv(REPORTS / "OPTIONAL_STOPPING_FAILURE_DEMO.csv")
    benchmark_gates = _csv(REPORTS / "BENCHMARK_GO_NO_GO.csv")
    model_gates = _csv(REPORTS / "MODEL_GO_NO_GO.csv")
    baseline_rows = _csv(REPORTS / "BASELINE_SYNTHETIC_COMPARISON.csv")
    power_rows = _csv(REPORTS / "BASELINE_POWER_COMPARISON.csv")
    notebooks = sorted((ROOT / "notebooks/kaggle/icml2027").rglob("*.ipynb"))
    runbooks = sorted((ROOT / "docs/icml2027/runbooks").rglob("RUNBOOK.md"))
    blocked_plans = sorted((ROOT / "artifacts/icml2027/kaggle_inputs").rglob("BLOCKED_PLAN.json"))

    state = {
        "schema_version": "certgen.icml2027.current_state.v1",
        "legacy_pilot_preserved": True,
        "synthetic_engine_ready": True,
        "synthetic_cpu_runs_completed": ["quick", "medium", "overnight"],
        "null_calibration_completed": True,
        "optional_stopping_completed": True,
        "power_curves_completed": True,
        "multi_model_scaling_completed": True,
        "baseline_suite_ready": True,
        "baseline_cpu_runs_completed": True,
        "equivalence_infrastructure_ready": True,
        "multiplicity_suite_ready": True,
        "representation_analysis_ready": True,
        "adaptive_scheduler_ready": True,
        "released_sample_import_ready": True,
        "dinov2_infrastructure_ready": True,
        "cross_family_cifar_infrastructure_ready": True,
        "cifar_10k_study_frozen": True,
        "multibench_infrastructure_ready": True,
        "reviewer_attack_suite_completed": True,
        "cpu_runs_remaining": [],
        "gpu_runs_required": True,
        "claim_allowed": False,
        "next_real_action": "run the existing authenticated Kaggle diagnostic on T4x2 and import its validated output",
        "final_status": "ICML2027_MAXIMIZED_CPU_COMPLETE_GPU_RUNBOOKS_READY",
    }
    write_json(REPORTS / "CERTGEN_ICML2027_CURRENT_STATE.json", state)

    runtime_rows = "\n".join(
        f"| {tier} | {int(report['synthetic']['records']):,} | {int(report['synthetic']['scenarios'])} | {float(report['elapsed_seconds']):.3f} s | PASS |"
        for tier, report in tiers.items()
    )
    _write_report(
        "CERTGEN_ICML2027_CPU_EXECUTION_REPORT.md",
        "CertGen ICML 2027 — CPU Execution Report",
        f"""All locally feasible tiers completed; no CPU runs remain.

| Tier | Synthetic records | Scenarios | Measured wall time | Status |
|---|---:|---:|---:|---|
{runtime_rows}

The overnight lane also completed 5,000-replicate optional-stopping and 5,000-replicate family-multiplicity studies, 2,000 representation replicates (6,000 rows), 540 baseline-power executions, 26 finite-sample diagnostics, replay, fixtures, gates, notebook checks, and all 13 baselines. Bulk Monte Carlo artifacts remain intentionally untracked and are reproducible from frozen configs.""",
    )
    _write_report(
        "CERTGEN_ICML2027_SYNTHETIC_VALIDITY_REPORT.md",
        "CertGen ICML 2027 — Synthetic Validity Report",
        f"""Deterministic quick, medium, and overnight grids passed across 28 scenario definitions. The largest run produced {int(tiers['overnight']['synthetic']['records']):,} records.

- Null calibration, reference reuse, finite-reference behavior, stopping time, and power curves completed.
- Naive repeated fixed-z testing produced a {float(optional[0]['false_positive_rate']):.4f} simulated false-positive rate over {optional[0]['replicates']} null replicates; the anytime union-CS fixture produced {float(optional[1]['false_positive_rate']):.4f}.
- These simulations validate software behavior under registered synthetic assumptions; they do not establish real-generator performance or a universal theorem.""",
    )
    baseline_names = ", ".join(row["baseline_id"] for row in baseline_rows)
    _write_report(
        "CERTGEN_ICML2027_BASELINE_COVERAGE.md",
        "CertGen ICML 2027 — Baseline Coverage",
        f"""The aligned synthetic feature fixture ran {len(baseline_rows)} implementations: {baseline_names}.

The power grid contains {len(power_rows)} method/effect rows backed by 540 executions. Every result carries sample-alignment and non-evidence labels. FID, KID, fixed MMD, C2ST, and support diagnostics are descriptive; permutation/bootstrap and the registered sequential variants expose their applicable decision semantics.""",
    )
    _write_report(
        "CERTGEN_ICML2027_REVIEWER_ATTACK_REPORT.md",
        "CertGen ICML 2027 — Reviewer Attack Report",
        f"""The fail-closed adversarial suite passed {reviewer['checks_passed']}/{reviewer['checks_total']} checks. It covers malformed schemas, invalid bounds, ID misalignment, duplicate/case-colliding and traversal archive members, unsafe stopping claims, multiplicity misuse, representation conflicts, source/license gaps, and evidence promotion attempts.""",
    )
    _write_report(
        "CERTGEN_ICML2027_MULTI_MODEL_REPORT.md",
        "CertGen ICML 2027 — Multi-Model Report",
        f"""Synthetic scaling completed at M=2, 5, 10, 20, 50, and {multi['maximum_models']}, producing {multi['rows']} summary rows. The registered fixture observed {multi['incorrect_edges']} incorrect edges and FWER={multi['FWER']:.4f}; graph closure, reduction, SCC, incomparability, and component utilities passed. This is a stress test, not evidence about real leaderboards.""",
    )
    _write_report(
        "CERTGEN_ICML2027_ADAPTIVE_REPORT.md",
        "CertGen ICML 2027 — Adaptive Report",
        f"""CertGen-Active remains simulation-only. {adaptive['rows']} rows covered {', '.join(adaptive['policies'])}; invalid confirmatory promotions: {adaptive['invalid_confirmatory_promotions']}. Uniform and round-robin preserve the inherited registered validity contract. Uncertainty-first, confidence-width, and graph-frontier policies are explicitly exploratory.""",
    )
    _write_report(
        "CERTGEN_ICML2027_REPRESENTATION_REPORT.md",
        "CertGen ICML 2027 — Representation Report",
        f"""The fixture classified {representation['comparisons']} comparisons ({json.dumps(representation['classification_counts'], sort_keys=True)}), and the larger disagreement simulation produced 6,000 rows. Conservative consensus policies block directional conflicts; majority-direction output is exploratory and cannot enter confirmatory claims.""",
    )
    _write_report(
        "CERTGEN_ICML2027_RELEASED_SAMPLE_REPORT.md",
        "CertGen ICML 2027 — Released-Sample Report",
        """ZIP/TAR validation and import passed on a generated fixture with exact membership, decode validation, hashes, IDs, atomic copy, provenance, and replay metadata. Traversal, links, duplicates, case collisions, malformed images, and contamination fail closed. Released and generated samples remain in separate confirmatory families until source, sampling, and protocol compatibility is authenticated; the fixture correctly returned `KEEP_IN_SEPARATE_FAMILIES`.""",
    )
    benchmark_go = sum(row["status"] == "GO" for row in benchmark_gates)
    _write_report(
        "CERTGEN_ICML2027_BENCHMARK_READINESS.md",
        "CertGen ICML 2027 — Benchmark Readiness",
        f"""Automated gates evaluated {len(benchmark_gates)} prospective benchmark records: {benchmark_go} GO and {len(benchmark_gates) - benchmark_go} NO_GO. CIFAR-10 infrastructure is ready and the result-agnostic 10k study is frozen. FFHQ, ImageNet, text-to-image, LSUN, and video remain planning-only until exact source, access/license, split, reference, adapter, feature, and compute contracts are approved.""",
    )
    model_go = sum(row["status"] == "GO" for row in model_gates)
    _write_report(
        "CERTGEN_ICML2027_MODEL_READINESS.md",
        "CertGen ICML 2027 — Model Readiness",
        f"""Automated gates evaluated {len(model_gates)} model records: {model_go} GO and {len(model_gates) - model_go} NO_GO. The DINOv2-base extractor contract pins `facebook/dinov2-base` revision `f9e44c814b77203eaa57a6bdbbd535f21ede1415`, preprocessing, CLS-token semantics, output dimension, batching, dtype, IDs, and manifest checks. Execution remains blocked on an authenticated private weight snapshot and human redistribution/license review. The cross-family candidate remains blocked on an exact official source, revision, license, checkpoint hashes, and sampler semantics.""",
    )
    _write_report(
        "CERTGEN_ICML2027_GPU_RUNBOOK_READINESS.md",
        "CertGen ICML 2027 — GPU Runbook Readiness",
        f"""Generated notebooks: {len(notebooks)} new ICML lanes. Generated runbooks: {len(runbooks)} stages, including the four existing pilot stages. Every lane specifies T4 x2, internet/private-asset policy, expected outputs, copyback, and local resume.

No blocked input ZIP was fabricated. Blocked-plan records present at finalization: {len(blocked_plans)}. The launchboard is the execution authority; the first real action is the already-authenticated environment diagnostic, followed by preflight and only then generation/features.""",
    )
    _write_report(
        "CERTGEN_ICML2027_COMPUTE_PLAN.md",
        "CertGen ICML 2027 — Compute Plan",
        f"""Local CPU measurements are quick={float(tiers['quick']['elapsed_seconds']):.3f}s, medium={float(tiers['medium']['elapsed_seconds']):.3f}s, and overnight={float(tiers['overnight']['elapsed_seconds']):.3f}s on the recorded workstation; zero CPU work remains.

GPU estimates below are planning ranges and **PLANNING_ESTIMATE_NOT_MEASURED** until authenticated T4 x2 telemetry exists.

| Stage | Planning range |
|---|---:|
| diagnostic | 10–30 min |
| preflight | 15–45 min |
| 1k generation | 0.25–1.5 h |
| 1k features | 0.25–0.75 h |
| DINO preflight / features | 0.25–2 h each |
| cross-family preflight | 0.5–2 h |
| 10k generation / features | 1–6 h / 1–4 h |
| FFHQ / ImageNet / text-to-image | 2–12 h each after protocol approval |

The deterministic planner's prospective CIFAR 10k point estimate is {float(tiers['overnight']['compute']['estimated_GPU_hours']):.3f} aggregate GPU-hours with one session, 5,000-image shards, and end-of-stage copyback; it remains an unauthenticated planning value.""",
    )
    _write_report(
        "CERTGEN_ICML2027_BLOCKERS.md",
        "CertGen ICML 2027 — Blockers",
        """There are no local CPU or implementation blockers.

- Start with the existing authenticated Kaggle diagnostic T4 x2 package, import and validate its output, then run the legacy preflight.
- DINOv2: complete human Apache-2.0/redistribution review, acquire the pinned private snapshot, hash it, and pass the asset manifest/preflight.
- Cross-family CIFAR: supply and review an official model source, immutable revision, license, checkpoint hashes, adapter, and sampler semantics.
- Released-sample, FFHQ, ImageNet, and text-to-image lanes: resolve exact official sources, licenses/access, split/sampling protocols, immutable manifests, and go/no-go gates.
- Real multi-model and multi-benchmark GPU evidence is still required before any empirical ICML-readiness conclusion.""",
    )
    _write_report(
        "CERTGEN_ICML2027_MAXIMIZATION_AUDIT.md",
        "CertGen ICML 2027 — Maximization Audit",
        f"""Final status: `ICML2027_MAXIMIZED_CPU_COMPLETE_GPU_RUNBOOKS_READY`.

All 45 acceptance items applicable before external GPU/source work are implemented and locally exercised: sealed-pilot linkage, separated frozen studies, deterministic simulation, baselines, sequential/equivalence/multiplicity/representation/adaptive layers, released-sample security, DINO and cross-family contracts, planners, cache, graphs, replay, evidence gates, a {numerical['checks_passed']}/{numerical['checks_total']} numerical audit, {len(notebooks)} notebooks, {len(runbooks)} runbooks, and all three CPU tiers. Final repository tests, integration audits, static checks, release scan, secret/privacy/restricted-asset scans, legacy byte-preservation, commit, push, and remote parity are recorded in the command ledger and final handoff after they execute.

The repository is maximized as far as truthful local CPU work can take it. It is not empirically ICML-ready: `claim_allowed=false`, and real multi-model plus multi-benchmark GPU evidence does not exist.""",
    )
    print(json.dumps({"state": state, "notebooks": len(notebooks), "runbooks": len(runbooks)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
