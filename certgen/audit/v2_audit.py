"""Strict V2 audit for clean-core readiness."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np

from certgen.certs.api import certify_clean_metric_comparison
from certgen.certs.fid_policy import assert_no_rigorous_fid_claim
from certgen.core.io import read_json, write_json
from certgen.features.validate_cache import REQUIRED_MANIFEST_FIELDS
from certgen.fixtures.make_v2_feature_fixtures import make_v2_feature_fixtures
from certgen.gates.evidence_gate import validate_evidence_status
from certgen.metrics.streams import mmd_difference_stream
from certgen.reporting.certificate_card import render_certificate_card
from certgen.stats.design_contracts import CSConfig
from certgen.stats.cs import confidence_sequence


def _module_exists(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def run_v2_audit(*, out: str | Path, json_out: str | Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    try:
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["CERTGEN_SKIP_V2_AUDIT_TEST"] = "1"
        env["CERTGEN_SKIP_V3_AUDIT_TEST"] = "1"
        env["CERTGEN_SKIP_V4_AUDIT_TEST"] = "1"
        env["CERTGEN_SKIP_V5_AUDIT_TEST"] = "1"
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q"],
            cwd=Path.cwd(),
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=240,
            check=False,
        )
        detail = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else "no pytest output"
        add("pytest_suite_passes", result.returncode == 0, detail)
    except Exception as exc:
        add("pytest_suite_passes", False, str(exc))

    try:
        r = np.tile(np.array([[1.0, 0.0]]), (8, 1))
        a = r + 0.01
        b = np.tile(np.array([[0.0, 1.0]]), (8, 1))
        stream = mmd_difference_stream(a, b, r, {"name": "rbf", "normalize": "l2"}, seed=0)
        add("clean_core_stream_code_exists", len(stream.values) > 0 and stream.mean() < 0, "MMD difference stream imports and follows direction")
    except Exception as exc:
        add("clean_core_stream_code_exists", False, str(exc))

    try:
        result = confidence_sequence([-0.5] * 16, CSConfig(alpha=0.05, budget_units=16, lower_bound=-1, upper_bound=1))
        add("cs_implementation_exists", result.time_uniform and result.method_label, result.method_label)
    except Exception as exc:
        add("cs_implementation_exists", False, str(exc))

    try:
        fixture_dir = Path("data/smoke/v2/features")
        paths = make_v2_feature_fixtures(fixture_dir, seed=0)
        cert_path = "data/smoke/v2/certificates/audit_smoke_mmd_rbf.json"
        cert = certify_clean_metric_comparison(
            paths["model_a_close"],
            paths["model_b_far"],
            paths["reference"],
            "mmd_rbf",
            {},
            {"alpha": 0.05, "budget_units": 32, "method": "betting", "seed": 0},
            "v2_audit_smoke_pair",
            "smoke_only",
            cert_path,
        )
        add("certificate_api_exists", Path(cert_path).exists() and cert.claim_allowed is False, cert.decision)
    except Exception as exc:
        add("certificate_api_exists", False, str(exc))

    add("optional_stopping_lab_exists", _module_exists("certgen.experiments.optional_stopping_lab"), "module importable")
    add("feature_cache_schema_exists", bool(REQUIRED_MANIFEST_FIELDS), f"{len(REQUIRED_MANIFEST_FIELDS)} required fields")
    add("registry_v2_fields_exist", Path("registry/templates/candidate_model_pairs_template.csv").exists(), "V2 registry template present")
    add("first_pilot_v2_planner_exists", _module_exists("certgen.pilot.first_pilot_v2"), "module importable")

    try:
        assert_no_rigorous_fid_claim({"metric_label": "fid_inception", "rigorous_anytime_certificate": False, "decision": "descriptive_only"})
        try:
            assert_no_rigorous_fid_claim({"metric_label": "fid_inception", "rigorous_anytime_certificate": True})
            blocked = False
        except ValueError:
            blocked = True
        add("fid_rigorous_claims_blocked", blocked, "rigorous FID flag rejected")
    except Exception as exc:
        add("fid_rigorous_claims_blocked", False, str(exc))

    try:
        decision = validate_evidence_status("real_evidence_candidate", mode="smoke")
        add("smoke_artifacts_cannot_become_evidence", not decision.passed, decision.reason)
    except Exception as exc:
        add("smoke_artifacts_cannot_become_evidence", False, str(exc))

    try:
        certificate = read_json("data/smoke/v2/certificates/audit_smoke_mmd_rbf.json")
        card = render_certificate_card(certificate)
        add("certificate_reports_warn_not_evidence", "NOT PAPER EVIDENCE" in card and "NO_REAL_EVIDENCE" in card, "certificate card warning present")
    except Exception as exc:
        add("certificate_reports_warn_not_evidence", False, str(exc))

    try:
        offenders = []
        for path in [Path("docs/V2_SINGLE_FILE_HANDOFF.md"), Path("docs/V2_FID_POLICY.md"), Path("docs/V2_REPORTING.md")]:
            if path.exists():
                lowered = path.read_text(encoding="utf-8").lower()
                for phrase in ["we find that", "we show that", "published wins are undecided", "fid-certified winner"]:
                    if phrase in lowered:
                        offenders.append(f"{path}: {phrase}")
        add("no_forbidden_v2_claim_phrases", not offenders, "; ".join(offenders) if offenders else "selected V2 docs are claim-safe")
    except Exception as exc:
        add("no_forbidden_v2_claim_phrases", False, str(exc))

    try:
        heavy = ["torch", "torchvision", "transformers", "timm"]
        imported = [name for name in heavy if name in sys.modules]
        add("heavy_dependencies_optional_lazy", not imported, "not imported: " + ", ".join(heavy))
    except Exception as exc:
        add("heavy_dependencies_optional_lazy", False, str(exc))

    add("no_gpu_command_in_tests", "cuda" not in " ".join(path.read_text(encoding="utf-8").lower() for path in Path("tests").glob("test_*.py")), "tests do not invoke GPU/CUDA")

    handoff = Path("docs/V2_SINGLE_FILE_HANDOFF.md")
    if handoff.exists():
        text = handoff.read_text(encoding="utf-8")
        add("handoff_states_no_real_evidence", "NO_REAL_EVIDENCE" in text, "handoff contains no-real-evidence label")
    else:
        add("handoff_states_no_real_evidence", False, "handoff missing")

    status = "passed" if all(check["passed"] for check in checks) else "failed"
    payload = {"audit_status": status, "checks": checks}
    lines = [
        "# CertGen V2 Final Audit",
        "",
        f"Audit status: `{status}`",
        "",
        "| Check | Status | Detail |",
        "|---|---:|---|",
    ]
    for check in checks:
        lines.append(f"| `{check['name']}` | `{'pass' if check['passed'] else 'fail'}` | {check['detail']} |")
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_json(payload, json_out)
    return payload
