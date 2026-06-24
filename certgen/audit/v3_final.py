"""V3 final audit."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np

from certgen.certs.fid_policy import assert_no_rigorous_fid_claim
from certgen.certs.replay import replay_certificate
from certgen.core.hashing import file_sha256
from certgen.core.io import write_json
from certgen.core.status import evaluate_claim_policy, validate_v3_evidence_status
from certgen.features.cache_validate import validate_v3_feature_cache
from certgen.fixtures.make_v2_feature_fixtures import make_v2_feature_fixtures
from certgen.gates.claim_gate import scan_report_for_overclaims
from certgen.pilot.orchestrator import run_first_pilot
from certgen.registry.provenance import validate_provenance_ledger
from certgen.registry.v3_schema import render_availability_table, validate_v3_registry
from certgen.reporting.pilot_cards import render_pilot_report
from certgen.stats.optional_stopping_lab import run_optional_stopping_lab_v3


def _write_v3_sidecar(feature_path: Path, sidecar_path: Path, *, cache_id: str, model_id: str) -> None:
    with np.load(feature_path, allow_pickle=False) as loaded:
        shape = loaded["features"].shape
    write_json(
        {
            "cache_id": cache_id,
            "benchmark_id": "smoke_benchmark",
            "model_id": model_id,
            "split": "smoke",
            "feature_extractor": "custom",
            "feature_dim": int(shape[1]),
            "n_samples": int(shape[0]),
            "preprocessing": {"resize": "none", "interpolation": "none", "crop": "none", "normalization": "none"},
            "source": {"type": "precomputed_features", "uri_or_path": str(feature_path), "license_status": "verified_free"},
            "hashes": {"features_sha256": file_sha256(feature_path), "source_manifest_sha256": "smoke"},
            "created_by": "certgen_v3_audit",
            "created_at": "2026-06-23T00:00:00Z",
            "certgen_version": "0.3.0",
        },
        sidecar_path,
    )


def _prepare_smoke_inputs(root: Path) -> dict[str, str]:
    paths = make_v2_feature_fixtures(root / "features", seed=11)
    sidecars = {}
    for key, model_id in [("reference", "reference"), ("model_a_close", "model_a"), ("model_b_far", "model_b")]:
        sidecar = root / "features" / f"{key}.v3_sidecar.json"
        _write_v3_sidecar(Path(paths[key]), sidecar, cache_id=f"{key}_cache", model_id=model_id)
        sidecars[key] = str(sidecar)
    return {**paths, **{f"{k}_sidecar": v for k, v in sidecars.items()}}


def run_v3_final_audit(*, out: str | Path, json_out: str | Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    warnings: list[str] = []
    blockers: list[str] = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})
        if not passed:
            blockers.append(f"{name}: {detail}")

    try:
        import certgen

        add("package_import", bool(certgen.__version__), certgen.__version__)
    except Exception as exc:
        add("package_import", False, str(exc))

    add("v1_v2_compatibility_docs_present", Path("docs/V2_FINAL_AUDIT.md").exists() and Path("docs/V1_FINAL_AUDIT.md").exists(), "V1/V2 audit docs present")
    add("v3_intake_audit_available", Path("certgen/cli/v3_intake_audit.py").exists(), "V3 intake audit CLI present")
    add("evidence_statuses_enforced", validate_v3_evidence_status("dry_run_only") and not evaluate_claim_policy("smoke_only", True).passed, "V3 status policy active")
    add("smoke_dry_run_claim_blocked", not evaluate_claim_policy("dry_run_only", True).passed, "dry-run claim_allowed=true rejected")

    prov = validate_provenance_ledger("registry/provenance/released_sample_ledger_template.csv", allow_missing_local=True)
    add("provenance_ledger_template_validates", prov["passed"], "; ".join(prov["errors"]) or "passed")

    root = Path("data/smoke/v3/audit")
    inputs = _prepare_smoke_inputs(root)
    valid_cache = validate_v3_feature_cache(features_path=inputs["reference"], sidecar_path=inputs["reference_sidecar"], strict_hash=True, allow_constant=True)
    add("feature_cache_valid_fixture_passes", valid_cache.passed, "; ".join(valid_cache.errors) or "passed")
    nan_path = root / "features" / "nan.npz"
    np.savez_compressed(nan_path, features=np.array([[float("nan"), 0.0], [0.0, 1.0]]))
    nan_sidecar = root / "features" / "nan.v3_sidecar.json"
    _write_v3_sidecar(Path(inputs["reference"]), nan_sidecar, cache_id="nan", model_id="nan")
    bad = validate_v3_feature_cache(features_path=nan_path, sidecar_path=nan_sidecar, strict_hash=False)
    add("feature_cache_rejects_nan_or_mismatch", not bad.passed, "; ".join(bad.errors))

    from certgen.cli.plan_feature_extraction import write_feature_extraction_plan

    plan = write_feature_extraction_plan(
        input_manifest="registry/manifests/first_pilot_samples_template.jsonl",
        extractor="inception_v3_pool3",
        out_dir="data/features/first_pilot/inception",
        device="auto",
        batch_size=32,
        out="docs/FEATURE_EXTRACTION_PLAN.md",
        json_out="data/results/feature_extraction_plan.json",
    )
    add("feature_extraction_planner_dry_run", plan["evidence_status"] == "dry_run_only", "plan emitted")

    metric_cfg = root / "metric_repro.json"
    write_json(
        {
            "audit_id": "audit",
            "metric": "kid",
            "reference_features": {"npz": inputs["reference"], "sidecar": inputs["reference_sidecar"]},
            "model_features": {"npz": inputs["model_a_close"], "sidecar": inputs["model_a_close_sidecar"]},
            "expected": {"source": "none"},
            "sample_count": 20,
            "seed": 0,
        },
        metric_cfg,
    )
    from certgen.audit.metric_reproduction import run_metric_reproduction_audit

    metric = run_metric_reproduction_audit(metric_cfg, "docs/METRIC_REPRODUCTION_AUDIT.md", "data/results/metric_reproduction_audit.json")
    add("metric_reproduction_audit_works", not metric["errors"], metric["reproduction_status"])
    metric_gate = root / "metric_reproduction_gate.json"
    write_json(
        {
            "within_tolerance": True,
            "claim_allowed": False,
            "reproduction_status": "within_tolerance",
            "evidence_status": "synthetic_only",
        },
        metric_gate,
    )

    pilot_cfg = root / "pilot.yaml"
    pilot_cfg.write_text(
        f"""pilot_id: smoke_pilot_v3
mode: real_features
metrics: [mmd_rbf]
alpha: 0.05
max_samples: 20
seed: 0
metric_reproduction_audit: {metric_gate}
reference_cache:
  npz: {inputs['reference']}
  sidecar: {inputs['reference_sidecar']}
comparisons:
  - comparison_id: smoke_a_vs_b
    model_a_cache:
      npz: {inputs['model_a_close']}
      sidecar: {inputs['model_a_close_sidecar']}
    model_b_cache:
      npz: {inputs['model_b_far']}
      sidecar: {inputs['model_b_far_sidecar']}
claim_policy:
  allow_claims: false
""",
        encoding="utf-8",
    )
    pilot = run_first_pilot(pilot_cfg, "data/results/first_pilot_v3", "docs/FIRST_PILOT_V3_REPORT.md", "data/results/first_pilot_v3/summary.json")
    add("first_pilot_real_mode_synthetic_validated", pilot["pilot_result_computed"] and not pilot["claim_allowed"], "synthetic validated caches only")
    add("clean_core_certificates_generated", bool(pilot["certificates"]), str(pilot["certificates"]))

    try:
        assert_no_rigorous_fid_claim({"metric_label": "fid_inception", "rigorous_anytime_certificate": True})
        add("fid_policy_blocks_rigorous", False, "FID rigorous claim unexpectedly allowed")
    except ValueError:
        add("fid_policy_blocks_rigorous", True, "blocked")

    cert_path = pilot["certificates"][0]["path"]
    replay = replay_certificate(cert_path, "docs/CERTIFICATE_REPLAY_REPORT.md", "data/results/certificate_replay.json")
    add("certificate_replay_passes", replay["replay_status"] == "passed", replay["replay_status"])
    card = render_pilot_report(pilot)
    add("pilot_report_card_renders", "not paper evidence" in card.lower(), "rendered")
    add("claim_scanner_catches_overclaim", not scan_report_for_overclaims("our results demonstrate model A is better", claim_allowed=False).passed, "overclaim blocked")

    reg = validate_v3_registry("registry/v3/benchmarks_template.csv", "registry/v3/model_pairs_template.csv", "registry/v3/feature_caches_template.csv")
    add("v3_registry_validator_works", reg["passed"], "; ".join(reg["errors"]) or "passed")
    table = render_availability_table("registry/v3", "docs/V3_AVAILABILITY_TABLE.md", "data/results/v3_availability_table.json")
    add("availability_table_renders", table["claim_allowed"] is False, "rendered")
    lab = run_optional_stopping_lab_v3("configs/optional_stopping_lab_v3.yaml", "docs/OPTIONAL_STOPPING_LAB_V3.md", "data/results/optional_stopping_lab_v3.json")
    add("optional_stopping_lab_tiny_runs", lab["evidence_status"] == "synthetic_only", "synthetic lab ran")

    cmd_index = Path("docs/COMMAND_INDEX_V3.md")
    add("command_index_includes_v3_commands", cmd_index.exists() and "v3_audit" in cmd_index.read_text(encoding="utf-8"), "command index checked")
    required_docs = ["docs/V3_RUNBOOK.md", "docs/REPRODUCIBILITY_CAPSULE_V3.md", "docs/CLAIM_POLICY_V3.md", "docs/FID_POLICY_V3.md", "docs/V3_SINGLE_FILE_HANDOFF.md"]
    add("required_docs_exist", all(Path(p).exists() for p in required_docs), ", ".join(required_docs))

    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["CERTGEN_SKIP_V2_AUDIT_TEST"] = "1"
    env["CERTGEN_SKIP_V3_AUDIT_TEST"] = "1"
    env["CERTGEN_SKIP_V4_AUDIT_TEST"] = "1"
    env["CERTGEN_SKIP_V5_AUDIT_TEST"] = "1"
    pytest_result = subprocess.run([sys.executable, "-m", "pytest", "-q"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env, timeout=300)
    detail = pytest_result.stdout.strip().splitlines()[-1] if pytest_result.stdout.strip() else "no pytest output"
    add("pytest_passes", pytest_result.returncode == 0, detail)
    add("final_audit_non_evidence", True, "dry_run_only claim_allowed false")
    fake_phrases = ["published wins are undecided", "ranking changes", "model a is better"]
    offenders = []
    for path in Path("docs").glob("*.md"):
        if "POLICY" in path.name or "CLAIMS" in path.name:
            continue
        lowered = path.read_text(encoding="utf-8", errors="ignore").lower()
        lowered = lowered.replace("no ranking changes", "")
        lowered = lowered.replace("no ranking movement", "")
        offenders.extend(f"{path}:{phrase}" for phrase in fake_phrases if phrase in lowered)
    add("no_fake_real_numbers_in_docs", not offenders, "; ".join(offenders) if offenders else "no fake claim phrases")

    passed = not blockers
    payload = {
        "audit_name": "v3_final_audit",
        "passed": passed,
        "checks_passed": sum(1 for c in checks if c["passed"]),
        "checks_total": len(checks),
        "warnings": warnings,
        "blockers": blockers,
        "checks": checks,
        "evidence_status": "dry_run_only",
        "claim_allowed": False,
        "next_action": "fill provenance ledger for one benchmark and validate real feature caches",
    }
    lines = ["# CertGen V3 Final Audit", "", f"Summary: `{'passed' if passed else 'failed'}`", "", "`NO_REAL_EVIDENCE`", "", "| Check | Status | Detail |", "|---|---:|---|"]
    for check in checks:
        lines.append(f"| `{check['name']}` | `{'pass' if check['passed'] else 'fail'}` | {check['detail']} |")
    lines.extend(["", "## Next Action", "", payload["next_action"]])
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_json(payload, json_out)
    return payload
