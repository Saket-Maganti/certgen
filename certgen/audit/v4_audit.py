"""CertGen V4 final audit and handoff checks."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np

from certgen.analysis.decidedness import build_decidedness_audit
from certgen.analysis.ranking_stability import build_ranking_stability
from certgen.audit.metric_reproduction import run_metric_reproduction_audit
from certgen.audit.preprocessing_lock_audit import audit_preprocessing_lock
from certgen.audit.v4_state_intake import write_v4_state_intake
from certgen.certs.batch_certificate import run_batch_from_file
from certgen.certs.fid_policy import assert_no_rigorous_fid_claim
from certgen.certs.multiple_comparisons import allocate_alpha
from certgen.cli.build_paper_artifacts import build_paper_artifacts
from certgen.cli.run_release_safety_scan import run_scan as run_release_safety_scan
from certgen.core.hashing import file_sha256
from certgen.core.io import write_json
from certgen.fixtures.make_v2_feature_fixtures import make_v2_feature_fixtures
from certgen.gates.claim_gate import scan_report_for_overclaims
from certgen.literature.claim_ingest import read_claims, validate_claims
from certgen.literature.claim_trace import build_claim_trace
from certgen.notebooks.generate_feature_notebook import generate_feature_notebook
from certgen.pipeline.first_real_pilot import run_first_real_pilot_controller
from certgen.preprocess.locks import make_preprocessing_lock
from certgen.provenance.ledger import V4_LEDGER_FIELDS
from certgen.provenance.real_run_plan import build_real_run_plan
from certgen.release.capsule import validate_capsule, write_capsule_manifest
from certgen.review.attacks import attack_cards
from certgen.review.score_simulator import simulate_scorecard
from certgen.stats.dependence_diagnostics import dependence_warnings


NEXT_V5_ACTION = (
    "populate one real provenance ledger with verified released sample/model-pair rows, "
    "materialize or validate real feature caches, reproduce one reported metric point estimate, "
    "and run the first real clean-core pilot in non-claim mode to measure the first-benchmark "
    "undecided fraction"
)


def _module_exists(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _md(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _write_v4_plan_ledger(path: Path) -> None:
    row = {
        "comparison_id": "v4_template_pair",
        "benchmark_id": "template_benchmark",
        "dataset_name": "template_free_dataset",
        "dataset_split": "declared_split",
        "reference_set_source": "TBD_manual_manifest",
        "model_a_name": "template_model_a",
        "model_b_name": "template_model_b",
        "model_a_sample_source": "TBD_manual_manifest",
        "model_b_sample_source": "TBD_manual_manifest",
        "sample_source_type": "released_samples",
        "sample_license_status": "unknown",
        "sample_count_available_a": "0",
        "sample_count_available_b": "0",
        "reported_metric_name": "mmd_rbf",
        "reported_metric_value_a": "",
        "reported_metric_value_b": "",
        "reported_sample_size": "32",
        "reported_preprocessing": "TBD",
        "paper_or_source_citation": "template_only",
        "download_required": "no",
        "external_data_required": "yes",
        "provenance_status": "planned",
        "claim_allowed": "false",
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=V4_LEDGER_FIELDS)
        writer.writeheader()
        writer.writerow(row)


def _write_v4_claim_rows(path: Path) -> None:
    from certgen.literature.claim_schema import CLAIM_FIELDS

    row = {
        "claim_id": "template_claim_001",
        "paper_title": "Template Source For V4 Claim Trace",
        "paper_year": "2026",
        "venue_or_source": "template",
        "citation_key": "template2026",
        "benchmark": "template_benchmark",
        "dataset_split": "declared_split",
        "metric_name": "mmd_rbf",
        "reported_model_a": "template_model_a",
        "reported_model_b": "template_model_b",
        "reported_score_a": "",
        "reported_score_b": "",
        "reported_direction": "A",
        "reported_sample_size": "32",
        "reported_preprocessing": "v4_smoke_inception_lock",
        "released_samples_available": "unknown",
        "checkpoint_available": "unknown",
        "feature_stats_available": "unknown",
        "license_status": "unknown",
        "reproduction_status": "not_run",
        "certgen_status": "not_run",
        "evidence_status": "planned_only",
        "claim_allowed": "false",
        "notes": "template row; no benchmark evidence",
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CLAIM_FIELDS)
        writer.writeheader()
        writer.writerow(row)


def _build_smoke_batch_config(config_path: Path) -> dict[str, Any]:
    feature_paths = make_v2_feature_fixtures("data/smoke/v4/audit/features", seed=41, n=80, d=6)
    config = {
        "alpha": 0.05,
        "alpha_policy": "bonferroni",
        "budget_units": 24,
        "method": "betting",
        "seed": 41,
        "evidence_status": "synthetic_only",
        "metrics": ["mmd_rbf"],
        "comparisons": [
            {
                "comparison_id": "v4_smoke_a_close_vs_b_far",
                "features_a": feature_paths["model_a_close"],
                "features_b": feature_paths["model_b_far"],
                "features_r": feature_paths["reference"],
                "shared_reference_id": "v4_smoke_reference",
                "seed": 41,
            },
            {
                "comparison_id": "v4_smoke_equal_models",
                "features_a": feature_paths["model_equal_1"],
                "features_b": feature_paths["model_equal_2"],
                "features_r": feature_paths["reference"],
                "shared_reference_id": "v4_smoke_reference",
                "seed": 42,
            },
        ],
    }
    write_json(config, config_path)
    return config


def _write_v4_feature_sidecar(feature_path: str | Path, sidecar_path: str | Path, *, cache_id: str, model_id: str) -> None:
    feature_path = Path(feature_path)
    sidecar_path = Path(sidecar_path)
    with np.load(feature_path, allow_pickle=False) as loaded:
        shape = loaded["features"].shape
    write_json(
        {
            "cache_id": cache_id,
            "benchmark_id": "v4_smoke_benchmark",
            "model_id": model_id,
            "split": "smoke",
            "feature_extractor": "custom",
            "feature_dim": int(shape[1]),
            "n_samples": int(shape[0]),
            "preprocessing": {"resize": "none", "interpolation": "none", "crop": "none", "normalization": "none"},
            "source": {"type": "precomputed_features", "uri_or_path": str(feature_path), "license_status": "verified_free"},
            "hashes": {"features_sha256": file_sha256(feature_path), "source_manifest_sha256": "v4_smoke"},
            "created_by": "certgen_v4_audit",
            "created_at": "2026-06-23T00:00:00Z",
            "certgen_version": "0.4.0",
        },
        sidecar_path,
    )


def _write_metric_repro_config(config_path: Path, feature_paths: dict[str, str]) -> None:
    ref_sidecar = Path(feature_paths["reference"]).with_name("reference.v4_sidecar.json")
    model_sidecar = Path(feature_paths["model_a_close"]).with_name("model_a_close.v4_sidecar.json")
    _write_v4_feature_sidecar(feature_paths["reference"], ref_sidecar, cache_id="v4_reference_cache", model_id="reference")
    _write_v4_feature_sidecar(feature_paths["model_a_close"], model_sidecar, cache_id="v4_model_a_close_cache", model_id="model_a")
    write_json(
        {
            "audit_id": "v4_metric_repro_smoke",
            "metric": "kid",
            "reference_features": {"npz": feature_paths["reference"], "sidecar": str(ref_sidecar)},
            "model_features": {"npz": feature_paths["model_a_close"], "sidecar": str(model_sidecar)},
            "expected": {"source": "none"},
            "sample_count": 20,
            "seed": 0,
            "evidence_status": "synthetic_only",
        },
        config_path,
    )


def _scan_selected_docs_for_claims(paths: list[Path]) -> list[str]:
    offenders: list[str] = []
    for path in paths:
        if not path.exists():
            continue
        decision = scan_report_for_overclaims(path.read_text(encoding="utf-8", errors="ignore"), claim_allowed=False)
        offenders.extend(f"{path}:{violation}" for violation in decision.violations)
    return offenders


def run_v4_final_audit(*, out: str | Path, json_out: str | Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    blockers: list[str] = []
    warnings: list[str] = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})
        if not passed:
            blockers.append(f"{name}: {detail}")

    try:
        import certgen

        version_parts = tuple(int(part) for part in certgen.__version__.split(".")[:2])
        add("package_imports_as_v4", version_parts >= (0, 4), certgen.__version__)
    except Exception as exc:  # pragma: no cover - defensive audit path
        add("package_imports_as_v4", False, exc)

    try:
        state = write_v4_state_intake("docs/V4_STATE_INTAKE_AUDIT.md", "data/results/v4_state_intake_audit.json")
        add("v4_state_intake_audit_exists", state["passed"], f"{state['num_passed']}/{state['num_checks']} checks")
    except Exception as exc:
        add("v4_state_intake_audit_exists", False, exc)

    ledger_path = Path("registry/provenance/v4_plan_ledger_template.csv")
    plan_path = Path("data/results/v4/real_run_plan.json")
    try:
        _write_v4_plan_ledger(ledger_path)
        plan = build_real_run_plan(ledger_path, "v4_template_pair", plan_path, "docs/V4_REAL_RUN_PLAN.md", requested_budget=32)
        add("provenance_to_real_run_planner_exists", plan["evidence_status"] == "planned_only" and not plan["claim_allowed"], plan["blockers"])
    except Exception as exc:
        add("provenance_to_real_run_planner_exists", False, exc)

    try:
        script = generate_feature_notebook(plan_path, "kaggle", "inception_v3_pool3", "notebooks/generated/kaggle_inception_features.py")
        add("feature_notebook_generator_exists", "CERTGEN_SAMPLE_MANIFEST" in script and "CLAIM_ALLOWED = False" in script, "generated Kaggle script")
    except Exception as exc:
        add("feature_notebook_generator_exists", False, exc)

    try:
        lock_path = Path("configs/preprocessing_locks/v4_smoke_inception_lock.json")
        make_preprocessing_lock("v4_smoke_inception_lock", lock_path, feature_extractor="inception_v3_pool3")
        lock_audit = audit_preprocessing_lock(str(lock_path), strict=True)
        add("preprocessing_lock_validator_exists", lock_audit["passed"], lock_audit["errors"] or "strict lock valid")
    except Exception as exc:
        add("preprocessing_lock_validator_exists", False, exc)

    try:
        feature_paths = make_v2_feature_fixtures("data/smoke/v4/metric_repro/features", seed=43, n=80, d=6)
        metric_config = Path("configs/metric_reproduction_v4_smoke.json")
        _write_metric_repro_config(metric_config, feature_paths)
        metric = run_metric_reproduction_audit(metric_config, "docs/V4_METRIC_REPRODUCTION_AUDIT.md", "data/results/v4_metric_reproduction_audit.json")
        add("metric_reproduction_gate_exists", metric["claim_allowed"] is False and not metric["errors"], metric["reproduction_status"])
    except Exception as exc:
        add("metric_reproduction_gate_exists", False, exc)

    batch_payload: dict[str, Any] | None = None
    try:
        batch_config_path = Path("configs/v4_batch_certificates_smoke.json")
        batch_config = _build_smoke_batch_config(batch_config_path)
        batch_payload = run_batch_from_file(batch_config_path, "data/results/v4/batch_certificates.json", "docs/V4_BATCH_CERTIFICATE_REPORT.md")
        add("batch_certificate_runner_exists", len(batch_payload["rows"]) == len(batch_config["comparisons"]), f"{len(batch_payload['rows'])} rows")
    except Exception as exc:
        add("batch_certificate_runner_exists", False, exc)

    try:
        policy = allocate_alpha(0.05, 5, "bonferroni")
        add("multiple_comparison_policy_exists", policy["adjusted_for_multiplicity"] and policy["alpha_used"] == 0.01, policy)
    except Exception as exc:
        add("multiple_comparison_policy_exists", False, exc)

    try:
        warnings_map = dependence_warnings(_build_smoke_batch_config(Path("configs/v4_dependence_smoke.json"))["comparisons"])
        add("dependence_diagnostics_exist", bool(warnings_map), warnings_map)
    except Exception as exc:
        add("dependence_diagnostics_exist", False, exc)

    try:
        decided = build_decidedness_audit("data/results/v4/batch_certificates.json", "data/results/v4/decidedness_audit.csv", "data/results/v4/decidedness_audit.json", "docs/V4_DECIDEDNESS_AUDIT.md")
        add("decidedness_audit_exists", decided["claim_allowed"] is False and bool(decided["counts"]), decided["counts"])
    except Exception as exc:
        add("decidedness_audit_exists", False, exc)

    try:
        ranking = build_ranking_stability("data/results/v4/batch_certificates.json", "docs/V4_RANKING_STABILITY_REPORT.md", "data/results/v4/ranking_stability.json")
        add("ranking_stability_report_exists", ranking["claim_allowed"] is False and "undecided_edges" in ranking, f"{len(ranking['undecided_edges'])} undecided")
    except Exception as exc:
        add("ranking_stability_report_exists", False, exc)

    try:
        pilot = run_first_real_pilot_controller(plan_path, "data/results/v4/first_real_pilot", "docs/V4_FIRST_REAL_PILOT_REPORT.md", dry_run=True)
        add("first_real_pilot_controller_exists", pilot["pilot_status"] == "NONCLAIM_DRY_RUN" and not pilot["claim_allowed"], pilot["next_action"])
    except Exception as exc:
        add("first_real_pilot_controller_exists", False, exc)

    try:
        claims_path = Path("registry/reported_metric_claims_v4_smoke.csv")
        _write_v4_claim_rows(claims_path)
        claims = validate_claims(claims_path, strict=False)
        traces = [build_claim_trace(row) for row in read_claims(claims_path)]
        write_json({"validation": claims, "traces": traces, "claim_allowed": False}, "data/results/v4/reported_claim_traces.json")
        add("literature_claim_ingestion_exists", claims["passed"] and len(traces) == 1 and not traces[0]["claim_allowed"], "1 template trace")
    except Exception as exc:
        add("literature_claim_ingestion_exists", False, exc)

    try:
        paper_artifacts = build_paper_artifacts("data/results/v4/paper_artifacts", "docs/V4_PAPER_ARTIFACTS_REPORT.md")
        add("paper_figure_table_scaffold_exists", len(paper_artifacts["figures"]) >= 5 and len(paper_artifacts["tables"]) >= 6, "figures/tables spec generated")
    except Exception as exc:
        add("paper_figure_table_scaffold_exists", False, exc)

    paper_paths = ["paper/main.tex", "paper/sections/introduction.tex", "docs/CVPR_PAPER_SCAFFOLD_V4.md", "docs/RELATED_WORK_TASK_BOARD_V4.md"]
    add("cvpr_paper_scaffold_exists", all(Path(p).exists() for p in paper_paths), ", ".join(paper_paths))

    claim_offenders = _scan_selected_docs_for_claims(
        [
            Path("docs/V4_SINGLE_FILE_HANDOFF.md"),
            Path("docs/CVPR_PAPER_SCAFFOLD_V4.md"),
            Path("docs/PAPER_ARTIFACTS_V4.md"),
            Path("paper/README.md"),
        ]
    )
    add("claim_language_audit_exists", not claim_offenders, claim_offenders or "selected V4 docs are claim-safe")

    try:
        cards = attack_cards()
        score = simulate_scorecard()
        write_json({"attacks": cards, "scorecard": score, "claim_allowed": False}, "data/results/v4/reviewer_attack_harness.json")
        add("reviewer_attack_harness_exists", len(cards) >= 15 and sum(1 for c in cards if c["blocker"]) >= 5, f"{len(cards)} attacks")
    except Exception as exc:
        add("reviewer_attack_harness_exists", False, exc)

    try:
        write_capsule_manifest("release/capsule_manifest_v4.json")
        capsule = validate_capsule(".")
        add("reproducibility_capsule_validator_exists", capsule["passed"], capsule["missing"] or "capsule requirements present")
    except Exception as exc:
        add("reproducibility_capsule_validator_exists", False, exc)

    try:
        release = run_release_safety_scan("docs/V4_RELEASE_SAFETY_REPORT.md", "data/results/v4_release_safety.json")
        add("release_safety_scan_exists", release["passed"] and not release["privacy_issues"], release["issues"] or "passed")
        if release["license_warnings"]:
            warnings.extend(release["license_warnings"])
    except Exception as exc:
        add("release_safety_scan_exists", False, exc)

    try:
        try:
            assert_no_rigorous_fid_claim({"metric_name": "fid_inception", "rigorous_anytime_certificate": True})
            fid_blocked = False
        except ValueError:
            fid_blocked = True
        add("fid_policy_remains_descriptive", fid_blocked and "descriptive" in Path("docs/FID_POLICY_V3.md").read_text(encoding="utf-8").lower(), "rigorous FID claim rejected")
    except Exception as exc:
        add("fid_policy_remains_descriptive", False, exc)

    try:
        promoted = []
        for path in Path("data").glob("**/*.json"):
            if "/smoke/" in str(path) or "/v4/" in str(path):
                text = path.read_text(encoding="utf-8", errors="ignore").lower()
                if '"claim_allowed": true' in text or '"evidence_status": "claim_allowed"' in text:
                    promoted.append(str(path))
        add("smoke_synthetic_artifacts_non_claim", not promoted, promoted or "no claim promotion found")
    except Exception as exc:
        add("smoke_synthetic_artifacts_non_claim", False, exc)

    result_claim_offenders = _scan_selected_docs_for_claims(
        [
            Path("docs/V4_FINAL_AUDIT.md"),
            Path("docs/V4_BATCH_CERTIFICATE_REPORT.md"),
            Path("docs/V4_DECIDEDNESS_AUDIT.md"),
            Path("docs/V4_RANKING_STABILITY_REPORT.md"),
            Path("docs/V4_FIRST_REAL_PILOT_REPORT.md"),
        ]
    )
    add("no_result_claims_without_real_evidence", not result_claim_offenders, result_claim_offenders or "no unguarded result claims")

    try:
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["CERTGEN_SKIP_V2_AUDIT_TEST"] = "1"
        env["CERTGEN_SKIP_V3_AUDIT_TEST"] = "1"
        env["CERTGEN_SKIP_V4_AUDIT_TEST"] = "1"
        env["CERTGEN_SKIP_V5_AUDIT_TEST"] = "1"
        pytest_result = subprocess.run([sys.executable, "-m", "pytest", "-q"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env, timeout=300)
        detail = pytest_result.stdout.strip().splitlines()[-1] if pytest_result.stdout.strip() else "no pytest output"
        add("pytest_passes_or_failure_recorded", pytest_result.returncode == 0, detail)
    except Exception as exc:
        add("pytest_passes_or_failure_recorded", False, exc)

    command_index = Path("docs/COMMAND_INDEX_V4.md")
    add("command_index_updated", command_index.exists() and "certgen.audit.v4_audit" in command_index.read_text(encoding="utf-8"), str(command_index))

    handoff = Path("docs/V4_SINGLE_FILE_HANDOFF.md")
    handoff_text = handoff.read_text(encoding="utf-8") if handoff.exists() else ""
    add("handoff_summarizes_blockers", handoff.exists() and "Current blockers" in handoff_text and "no real benchmark audit" in handoff_text.lower(), str(handoff))
    add("next_v5_action_concrete", NEXT_V5_ACTION in handoff_text, NEXT_V5_ACTION)
    add("audit_has_at_least_25_checks", len(checks) + 1 >= 25, f"{len(checks) + 1} checks")

    passed = not blockers
    payload = {
        "audit_name": "v4_final_audit",
        "passed": passed,
        "checks_passed": sum(1 for c in checks if c["passed"]),
        "checks_total": len(checks),
        "checks": checks,
        "warnings": warnings,
        "blockers": blockers,
        "evidence_status": "dry_run_only",
        "claim_allowed": False,
        "next_action": NEXT_V5_ACTION,
    }
    lines = [
        "# CertGen V4 Final Audit",
        "",
        f"Summary: `{'passed' if passed else 'failed'}`",
        "",
        "`NO_REAL_EVIDENCE`",
        "",
        f"Checks passed: `{payload['checks_passed']}/{payload['checks_total']}`",
        "Evidence status: `dry_run_only`",
        "Claim allowed: `false`",
        "",
        "| Check | Status | Detail |",
        "|---|---:|---|",
    ]
    for check in checks:
        lines.append(f"| `{check['name']}` | `{'pass' if check['passed'] else 'fail'}` | {_md(check['detail'])} |")
    lines.extend(["", "## Blockers"])
    lines.extend(f"- {blocker}" for blocker in blockers or ["none"])
    lines.extend(["", "## Warnings"])
    lines.extend(f"- {warning}" for warning in warnings or ["none"])
    lines.extend(["", "## Exact Next V5 Action", "", NEXT_V5_ACTION, ""])
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text("\n".join(lines), encoding="utf-8")
    write_json(payload, json_out)
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run CertGen V4 final audit.")
    parser.add_argument("--out", required=True)
    parser.add_argument("--json-out", required=True)
    args = parser.parse_args(argv)
    payload = run_v4_final_audit(out=args.out, json_out=args.json_out)
    print(f"V4 audit status: {'passed' if payload['passed'] else 'failed'}")
    return 0 if payload["passed"] else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
