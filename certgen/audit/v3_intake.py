"""V3 intake audit for post-V2 readiness."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from certgen import __version__
from certgen.core.io import read_json, write_json
from certgen.core.provenance import utc_now_iso
from certgen.gates.claim_gate import scan_text_for_forbidden_claims


def module_exists(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def run_v3_intake_audit(*, out: str | Path, json_out: str | Path, run_pytest: bool = True) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    warnings: list[str] = []
    blockers: list[str] = []

    def add(name: str, passed: bool, detail: str, *, warn_only: bool = False) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail, "warning": warn_only})
        if not passed:
            (warnings if warn_only else blockers).append(f"{name}: {detail}")

    add("package_import", bool(__version__), f"certgen {__version__}")
    for name in [
        "certgen.metrics.streams",
        "certgen.certs.api",
        "certgen.cli.certify_clean_metric",
        "certgen.features.validate_cache",
        "certgen.registry.validate",
        "certgen.pilot.first_pilot_v2",
    ]:
        add(f"module_{name}", module_exists(name), "importable" if module_exists(name) else "missing")
    for path in ["docs/V2_FID_POLICY.md", "docs/COMMAND_INDEX_V2.md", "docs/V2_SINGLE_FILE_HANDOFF.md"]:
        add(f"file_{path}", Path(path).exists(), path)

    smoke_cert = Path("data/smoke/v2/certificates/smoke_pair_001_kid_certificate.json")
    if smoke_cert.exists():
        cert = read_json(smoke_cert)
        add("smoke_certificate_non_evidence", cert.get("claim_allowed") is False and cert.get("evidence_status") in {"smoke_only", "dry_run_only"}, str(smoke_cert))
    else:
        add("smoke_certificate_non_evidence", False, "optional V2 smoke certificate absent", warn_only=True)

    if run_pytest:
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["CERTGEN_SKIP_V3_INTAKE_TEST"] = "1"
        result = subprocess.run([sys.executable, "-m", "pytest", "-q"], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env, timeout=240)
        detail = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else "no pytest output"
        add("pytest_invocable", result.returncode == 0, detail)
    else:
        add("pytest_invocable", True, "disabled by caller", warn_only=True)

    for root in ["docs", "data/results"]:
        for path in Path(root).glob("**/*"):
            if path.is_file() and path.suffix in {".md", ".json"}:
                if "POLICY" in path.name or "CLAIMS" in path.name or "RULES" in path.name or "audit" in path.name.lower():
                    continue
                text = path.read_text(encoding="utf-8", errors="ignore")
                text = text.replace("no real empirical results", "")
                text = text.replace("no paper evidence", "")
                text = text.replace("no ranking changes", "")
                text = text.replace("no empirical result", "")
                decision = scan_text_for_forbidden_claims(text, evidence_status="dry_run_only")
                if not decision.passed:
                    add("forbidden_claim_scan", False, f"{path}: {decision.reason}")
                    break
    v2_audit = Path("data/results/v2_final_audit.json")
    if v2_audit.exists():
        data = read_json(v2_audit)
        add("v2_audit_passed", data.get("audit_status") == "passed", str(v2_audit))
    else:
        add("v2_audit_passed", False, "optional V2 audit JSON absent", warn_only=True)

    add("heavy_imports_lazy", not any(name in sys.modules for name in ["torch", "torchvision", "transformers", "timm"]), "no heavy modules imported")
    passed = not blockers
    payload = {
        "audit_name": "v3_intake_audit",
        "passed": passed,
        "checks_passed": sum(1 for c in checks if c["passed"]),
        "checks_total": len(checks),
        "warnings": warnings,
        "blockers": blockers,
        "checks": checks,
        "evidence_status": "dry_run_only",
        "claim_allowed": False,
        "created_at": utc_now_iso(),
    }
    lines = ["# V3 Intake Audit", "", "`NO_REAL_EVIDENCE_FROM_INTAKE_AUDIT`", "", f"Status: `{'passed' if passed else 'failed'}`", "", "| Check | Status | Detail |", "|---|---:|---|"]
    for check in checks:
        lines.append(f"| `{check['name']}` | `{'pass' if check['passed'] else 'fail'}` | {check['detail']} |")
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_json(payload, json_out)
    return payload
