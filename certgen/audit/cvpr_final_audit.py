"""Final local-safe audit for the CVPR real-execution closure build."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from certgen.core.io import write_json
from certgen.cvpr.contracts import CVPRStage, STAGE_TRANSITIONS
from certgen.cvpr.registries import validate_all_cvpr_registries
from certgen.notebooks.cvpr_static_analyzer import analyze_all
from certgen.paper.v9_paper_firewall import run_firewall
from certgen.pipeline.v9_next_action import ACTIONS, determine_next_action


REQUIRED_PATHS = (
    "CERTGEN_CVPR_FINAL_RUN_READY_EXECUTION_HANDBOOK.md",
    "CERTGEN_CVPR_FINAL_RUN_READY_CLOSURE_REPORT.md",
    "reports/CERTGEN_FINAL_RUN_READY_BASELINE.md",
    "reports/CERTGEN_FINAL_RUN_READY_COMMAND_LEDGER.csv",
    "reports/CERTGEN_FINAL_RUN_READY_CURRENT_STATE.json",
    "reports/CERTGEN_FINAL_RUN_READY_REPAIR_CHANGELOG.md",
    "reports/CERTGEN_FINAL_RUN_READY_TEST_MATRIX.md",
    "reports/CERTGEN_FINAL_RUN_READY_NOTEBOOK_READINESS.md",
    "reports/CERTGEN_FINAL_RUN_READY_HANDOFF_AUDIT.md",
    "reports/CERTGEN_ADAPTER_CONFORMANCE_MATRIX.csv",
    "docs/CERTGEN_CVPR_EXACT_NEXT_ACTION.md",
    "docs/CERTGEN_CVPR_SINGLE_FILE_HANDOFF.md",
    "docs/execution/CERTGEN_KAGGLE_ENVIRONMENT_BOOTSTRAP.md",
    "docs/execution/CERTGEN_MODEL_ASSET_POLICY.md",
    "docs/execution/CERTGEN_T4X2_SUBPROCESS_ARCHITECTURE.md",
    "docs/execution/CERTGEN_BATCH_AND_OOM_PROTOCOL.md",
    "docs/execution/CERTGEN_PREPROCESSING_OBSERVED_CONTRACT.md",
    "docs/execution/CERTGEN_RESUME_RESTART_FORCE_PROTOCOL.md",
    "docs/execution/CERTGEN_CANONICAL_PREPARE_COMMANDS.md",
    "docs/execution/CERTGEN_RUNTIME_CALIBRATION_PROTOCOL.md",
    "docs/execution/CERTGEN_CLEAN_ARCHIVE_GUIDE.md",
    "docs/execution/CERTGEN_REAL_MODEL_PREFLIGHT_PROTOCOL.md",
    "docs/execution/CERTGEN_REAL_EXTRACTOR_PREFLIGHT_PROTOCOL.md",
    "docs/execution/CERTGEN_GPU_QUEUE_SCHEDULER.md",
    "docs/execution/CERTGEN_MODEL_ADAPTER_CONTRACT.md",
    "docs/execution/CERTGEN_LOCAL_ASSET_LOADING_CONTRACT.md",
    "docs/execution/CERTGEN_GENERATION_PACKAGE_CONTRACT.md",
    "docs/execution/CERTGEN_FEATURE_PACKAGE_AND_MERGE_CONTRACT.md",
    "docs/execution/CERTGEN_OUTPUT_SCHEMA_AND_IMPORT_CONTRACT.md",
    "docs/execution/CERTGEN_RESUME_AND_FINAL_ZIP_RECOVERY.md",
    "docs/execution/CERTGEN_PORTABLE_ARCHIVE_CONTRACT.md",
    "registry/cvpr/benchmark_registry.yaml",
    "registry/cvpr/model_registry.yaml",
    "registry/cvpr/feature_space_registry.yaml",
    "registry/cvpr/comparison_registry.csv",
    "registry/cvpr/published_claim_registry.csv",
    "configs/cvpr/certgen_cvpr_preregistration_template.yaml",
    "configs/cvpr/execution_matrix.yaml",
    "configs/cvpr/metric_reproduction_gate_template.yaml",
    "configs/cvpr/sanity_gates_template.yaml",
    "configs/cvpr/runtime_plan_template.yaml",
    "docs/theory/CERTGEN_CVPR_STATISTICAL_CORE_AUDIT.md",
    "docs/theory/CERTGEN_FORMAL_STREAM_CONTRACT.md",
    "docs/theory/CERTGEN_REFERENCE_DRAW_PROTOCOL.md",
    "docs/theory/CERTGEN_MULTIPLICITY_FAMILY_PROTOCOL.md",
    "docs/theory/CERTGEN_METRIC_CAPABILITY_REGISTRY.csv",
    "docs/engineering/CERTGEN_CVPR_CANONICAL_ARCHITECTURE.md",
    "docs/engineering/CERTGEN_CVPR_CLI_REFERENCE.md",
    "paper/CERTGEN_CVPR_CLAIM_CONTRACT.md",
    "paper/CERTGEN_CVPR_RESULT_TABLE_CONTRACTS.md",
    "paper/CERTGEN_CVPR_FIGURE_CONTRACTS.md",
    "paper/CERTGEN_CVPR_REVIEWER_SIMULATION.md",
    "paper/CERTGEN_CVPR_REVIEWER_REPAIR_MATRIX.csv",
    "release/CERTGEN_CVPR_PUBLIC_RELEASE_MANIFEST.txt",
    "release/CERTGEN_CVPR_INTERNAL_ARCHIVE_CANDIDATES.txt",
)


def _has_claim_true(value: Any) -> bool:
    if isinstance(value, dict):
        return any((key == "claim_allowed" and item is True) or _has_claim_true(item) for key, item in value.items())
    if isinstance(value, list):
        return any(_has_claim_true(item) for item in value)
    return False


def _claim_true_json(root: Path) -> list[str]:
    hits: list[str] = []
    for base_name in ("data", "reports", "release"):
        base = root / base_name
        if not base.exists():
            continue
        for path in base.rglob("*.json*"):
            if not path.is_file():
                continue
            try:
                values = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()] if path.suffix == ".jsonl" else [json.loads(path.read_text(encoding="utf-8"))]
            except (OSError, json.JSONDecodeError):
                continue
            if any(_has_claim_true(value) for value in values):
                hits.append(str(path.relative_to(root)))
    return sorted(hits)


def run_cvpr_audit(root: str | Path = ".", *, write_outputs: bool = True) -> dict[str, Any]:
    base = Path(root).resolve()
    missing = [path for path in REQUIRED_PATHS if not (base / path).is_file()]
    registry = validate_all_cvpr_registries(base)
    notebooks = analyze_all(base / path for path in (
        "notebooks/kaggle/certgen_cvpr_checkpoint_preflight_t4x2.ipynb",
        "notebooks/kaggle/certgen_cvpr_cifar10_generation_t4x2_1k.ipynb",
        "notebooks/kaggle/certgen_cvpr_generation_t4x2_generic.ipynb",
        "notebooks/kaggle/certgen_cvpr_feature_extraction_t4x2_1k.ipynb",
        "notebooks/kaggle/certgen_cvpr_feature_extraction_t4x2_generic.ipynb",
    ))
    firewall = run_firewall(
        base / "data/results/cvpr_paper_firewall.json",
        base / "docs/CERTGEN_CVPR_PAPER_FIREWALL_REPORT.md",
    )
    action = determine_next_action()
    state_path = base / "reports/CERTGEN_FINAL_RUN_READY_CURRENT_STATE.json"
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        state = {}
    stage_values = {item.stage for item in STAGE_TRANSITIONS}
    expected_state_status = {
        "PROVIDE_CIFAR_REFERENCE": "CVPR_RUN_READY_BLOCKED_BY_REFERENCE_INPUT",
        "VALIDATE_CIFAR_REFERENCE": "CVPR_RUN_READY_BLOCKED_BY_REFERENCE_INPUT",
        "RUN_KAGGLE_ENVIRONMENT_DIAGNOSTIC": "WAITING_FOR_KAGGLE_DIAGNOSTIC",
        "RUN_KAGGLE_CHECKPOINT_PREFLIGHT": "WAITING_FOR_KAGGLE_PREFLIGHT",
    }.get(str(action.get("action")), str(action.get("status", "")))
    checks = {
        "required_deliverables": {"passed": not missing, "detail": missing or "all present"},
        "registries": {"passed": registry["passed"], "detail": registry},
        "notebook_static_contract": {"passed": notebooks["passed"], "detail": notebooks},
        "paper_firewall": {"passed": firewall["passed"], "detail": firewall.get("blockers", [])},
        "no_claim_allowed_true_json": {"passed": not _claim_true_json(base), "detail": _claim_true_json(base) or "none"},
        "complete_stage_machine": {"passed": stage_values == set(CVPRStage) and len(STAGE_TRANSITIONS) == len(CVPRStage), "detail": f"{len(STAGE_TRANSITIONS)}/{len(CVPRStage)}"},
        "blocked_honest_next_action": {
            "passed": action.get("action") in ACTIONS
            and bool(action.get("exact_command"))
            and action.get("claim_allowed") is False,
            "detail": action,
        },
        "current_state_taxonomy": {
            "passed": state.get("top_level_status")
            == expected_state_status
            and state.get("claim_allowed") is False,
            "detail": state.get("top_level_status"),
        },
    }
    passed = all(row["passed"] for row in checks.values())
    payload = {
        "audit_name": "CERTGEN_CVPR_REAL_EXECUTION_CLOSURE_LOCAL_AUDIT",
        "passed": passed,
        "checks_passed": sum(row["passed"] for row in checks.values()),
        "checks_total": len(checks),
        "checks": checks,
        "top_level_status": expected_state_status if passed else "FINAL_RUN_READY_CLOSURE_FAILED",
        "exact_next_action": action,
        "not_empirical_evidence": True,
        "claim_allowed": False,
    }
    if write_outputs:
        write_json(payload, base / "reports/CERTGEN_CVPR_FINAL_AUDIT.json")
        lines = ["# CertGen CVPR Real-Execution Closure Audit", "", "Static/local-safe audit only; not empirical model evidence.", "", f"Passed: `{passed}`", f"Checks: `{payload['checks_passed']}/{payload['checks_total']}`", f"Status: `{payload['top_level_status']}`", "Claim allowed: `false`", "", "| Check | Passed |", "|---|---:|"]
        lines.extend(f"| `{name}` | `{row['passed']}` |" for name, row in checks.items())
        (base / "reports/CERTGEN_CVPR_FINAL_AUDIT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv)
    payload = run_cvpr_audit(args.root)
    print(f"cvpr_audit={payload['passed']} checks={payload['checks_passed']}/{payload['checks_total']}")
    return 0 if payload["passed"] else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
