"""V9 execution-supercharger audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from certgen.core.io import read_json, write_json
from certgen.notebooks.v9_static_analyzer import run_analysis
from certgen.paper.v9_paper_firewall import run_firewall
from certgen.pipeline.v9_execution_dashboard import build_dashboard
from certgen.pipeline.v9_next_action import ACTIONS, write_next_action
from certgen.pipeline.v9_runtime_budget_planner import build_plan


REQUIRED_PATHS = {
    "cifar_super_onramp": "certgen/data/cifar_reference_super_onramp.py",
    "checkpoint_preflight_notebook": "notebooks/kaggle/v9_checkpoint_real_load_preflight_t4x2.ipynb",
    "hardened_generation_notebook": "notebooks/kaggle/v9_cifar10_generation_t4x2_1k_hardened.ipynb",
    "hardened_feature_notebook": "notebooks/kaggle/v9_cifar10_feature_extraction_t4x2_1k_hardened.ipynb",
    "import_repair": "certgen/packaging/v9_import_repair.py",
    "next_action_engine": "certgen/pipeline/v9_next_action.py",
    "dashboard": "certgen/pipeline/v9_execution_dashboard.py",
    "runtime_planner": "certgen/pipeline/v9_runtime_budget_planner.py",
    "notebook_static_analyzer": "certgen/notebooks/v9_static_analyzer.py",
    "paper_firewall": "certgen/paper/v9_paper_firewall.py",
    "repo_snapshot_command": "commands/v9_cpu_execution/06_repo_snapshot_status.sh",
}
CLAIM_KEY = "claim_allowed"
CLAIM_EQUALS_TRUE = f"{CLAIM_KEY}=true"
CLAIM_JSON_TRUE = f'"{CLAIM_KEY}": true'
CLAIM_YAML_TRUE = f"{CLAIM_KEY}: true"


def _text_files() -> list[Path]:
    roots = [Path("certgen"), Path("commands"), Path("docs"), Path("data/results"), Path("notebooks")]
    files: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if "__pycache__" in path.parts:
                continue
            if any(part.startswith("certgen_prompt_pack") for part in path.parts):
                continue
            if path.suffix in {".py", ".sh", ".md", ".json", ".jsonl", ".ipynb", ".yaml", ".yml", ".txt"}:
                files.append(path)
    return files


def _has_claim_allowed_true(value: Any) -> bool:
    if isinstance(value, dict):
        return any((key == "claim_allowed" and item is True) or _has_claim_allowed_true(item) for key, item in value.items())
    if isinstance(value, list):
        return any(_has_claim_allowed_true(item) for item in value)
    return False


def _is_negated_claim_allowed_true_line(line: str) -> bool:
    lower = line.lower()
    negations = [
        f"no {CLAIM_EQUALS_TRUE}",
        f"no `{CLAIM_EQUALS_TRUE}`",
        f"no {CLAIM_JSON_TRUE}",
        "no output sets",
        f"not {CLAIM_EQUALS_TRUE}",
        "do not create",
        "never",
        "forbidden",
        "must not",
        "cannot",
        "rejected",
        "without final audit",
    ]
    return any(needle in lower for needle in negations)


def _is_negated_evidence_line(line: str) -> bool:
    lower = line.lower()
    if lower.strip() in {"- paper evidence", "* paper evidence"}:
        return True
    negations = [
        "no real empirical results",
        "no paper evidence",
        "not paper evidence",
        "does not create paper evidence",
        "do not create paper evidence",
        "do not treat",
        "do not convert",
        "does not run",
        "does not promote",
        "not a metric result and cannot support",
        "are not paper evidence",
        "is not a metric result",
        "no certificates or paper evidence are produced",
        "no certificate, metric reproduction, undecided fraction, or paper evidence is produced",
        "may be promoted",
        "remains blocked",
        "promotion remains blocked",
        "blocked_no_paper_evidence",
        "promote to paper evidence: `false`",
        "paper evidence: `false`",
        "paper-evidence promotion remains blocked",
        "no certificate code or paper evidence generation",
    ]
    return any(needle in lower for needle in negations)


def _claim_allowed_true_hits() -> list[str]:
    hits = []
    for path in _text_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        if path.suffix in {".json", ".ipynb"}:
            try:
                if _has_claim_allowed_true(json.loads(text)):
                    hits.append(str(path))
                continue
            except Exception:
                pass
        if path.suffix == ".jsonl":
            found = False
            for line in text.splitlines():
                try:
                    found = found or _has_claim_allowed_true(json.loads(line))
                except Exception:
                    lower = line.lower()
                    found = found or ((CLAIM_JSON_TRUE in lower or CLAIM_EQUALS_TRUE in lower) and not _is_negated_claim_allowed_true_line(line))
            if found:
                hits.append(str(path))
            continue
        if path.suffix == ".py":
            continue
        for line in text.splitlines():
            lower = line.lower()
            if ((CLAIM_JSON_TRUE in lower or CLAIM_EQUALS_TRUE in lower or CLAIM_YAML_TRUE in lower) and not _is_negated_claim_allowed_true_line(line)):
                hits.append(str(path))
                break
    return hits


def _unsafe_evidence_hits() -> list[str]:
    hits = []
    for path in _text_files():
        if path.suffix == ".py":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for line in text.splitlines():
            lower = line.lower()
            if "real empirical result" in lower and "no_real_evidence" not in lower and "not empirical project results" not in lower and not _is_negated_evidence_line(line):
                hits.append(str(path))
                break
            if "paper evidence" in lower and "not paper evidence" not in lower and "no paper evidence" not in lower and not _is_negated_evidence_line(line):
                hits.append(str(path))
                break
    return sorted(set(hits))


def run_audit(out: str | Path, json_out: str | Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def add(name: str, passed: bool, detail: Any) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    for name, path in REQUIRED_PATHS.items():
        add(f"{name}_exists", Path(path).exists(), path)

    notebook = run_analysis()
    add("notebook_static_analyzer_passes", notebook["passed"], notebook["results"])

    firewall = run_firewall()
    add("paper_firewall_passes", firewall["passed"], firewall["blockers"])

    runtime = build_plan("1k")
    add("runtime_budget_planner_runs", runtime["label"] == "planning estimates only, not empirical project results", runtime["planning_estimates"])

    next_action = write_next_action()
    add("exact_next_action_runs", next_action["action"] in ACTIONS, next_action)

    dashboard = build_dashboard()
    add("dashboard_renders", dashboard["claim_allowed"] is False and dashboard["paper_evidence_status"] == "blocked_no_paper_evidence", dashboard["current_stage"])

    claim_hits = _claim_allowed_true_hits()
    add("no_claim_allowed_true", not claim_hits, claim_hits or "none")

    evidence_hits = _unsafe_evidence_hits()
    add("no_fake_empirical_or_paper_evidence_claims", not evidence_hits, evidence_hits or "none")

    final_audit_path = Path("data/results/final_execution_audit.json")
    final = read_json(final_audit_path) if final_audit_path.exists() else {}
    add("final_execution_audit_honest_if_inputs_missing", final.get("status_code") in {
        "BLOCKED_MISSING_REFERENCE_SAMPLES",
        "BLOCKED_GENERATION_OUTPUT_ZIP_MISSING",
        "BLOCKED_GENERATED_MANIFEST_INVALID",
        "BLOCKED_FEATURE_INPUT_PACKAGE_MISSING",
        "BLOCKED_FEATURE_OUTPUT_ZIP_MISSING",
        "BLOCKED_FEATURE_CACHE_INVALID",
        "BLOCKED_METRIC_REPRODUCTION_OR_SANITY",
        "READY_FOR_FIRST_CERTIFICATE_PILOT",
        "FIRST_PILOT_COMPLETED_NO_CLAIM",
        "FIRST_PILOT_FAILED_GATES",
    }, final.get("status_code"))

    no_real_generation_claimed = not Path("data/kaggle_outputs/certgen_cifar10_generation_outputs_v9_1k.zip").exists()
    add("no_real_generation_claimed", no_real_generation_claimed, "no V9 generation output ZIP present")
    no_real_features_claimed = not Path("data/kaggle_outputs/certgen_cifar10_feature_outputs_v9_1k.zip").exists()
    add("no_real_features_claimed", no_real_features_claimed, "no V9 feature output ZIP present")
    cert_status = read_json("data/results/r1e_undecided_fraction.json") if Path("data/results/r1e_undecided_fraction.json").exists() else {}
    add("no_certificates_claimed", cert_status.get("status_code") != "PILOT_UNDECIDED_FRACTION_COMPUTED", cert_status.get("status_code", "missing"))

    passed = all(check["passed"] for check in checks)
    payload = {
        "audit_name": "CERTGEN_V9_EXECUTION_SUPERCHARGER_UPGRADE_ONLY",
        "passed": passed,
        "checks_passed": sum(1 for check in checks if check["passed"]),
        "checks_total": len(checks),
        "checks": checks,
        "next_action": next_action,
        "status_code": "V9_SUPERCHARGER_READY_BLOCKED_BY_INPUTS" if passed else "V9_SUPERCHARGER_AUDIT_FAILED",
        "claim_allowed": False,
        "no_fake_results": True,
        "not_paper_evidence": True,
    }
    write_json(payload, json_out)
    lines = [
        "# V9 Execution Supercharger Audit",
        "",
        "`NO_FAKE_RESULTS`",
        "`NO_REAL_EVIDENCE`",
        "`not paper evidence`",
        "",
        f"Audit status: `{'passed' if passed else 'failed'}`",
        f"Checks: `{payload['checks_passed']}/{payload['checks_total']}`",
        f"Next action: `{next_action['action']}`",
        "Claim allowed: `false`",
        "",
        "| Check | Passed | Detail |",
        "|---|---:|---|",
    ]
    for check in checks:
        detail = str(check["detail"]).replace("|", "\\|").replace("\n", " ")[:500]
        lines.append(f"| `{check['name']}` | `{check['passed']}` | {detail} |")
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the V9 execution-supercharger audit.")
    parser.add_argument("--out", required=True)
    parser.add_argument("--json-out", required=True)
    args = parser.parse_args(argv)
    payload = run_audit(args.out, args.json_out)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["passed"] else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
