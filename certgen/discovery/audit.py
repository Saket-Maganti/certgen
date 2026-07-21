"""Live universal-Kaggle acceptance audit over source-controlled artifacts."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

from certgen.discovery import PackageRequirement, PackageType, SelectionStatus, discover_packages
from certgen.phase1.audit import _locks
from certgen.phase1.notebooks import PHASE1_NOTEBOOKS, validate_phase1_notebooks


ACCOUNT_PATH = re.compile(r"/kaggle/input/[A-Za-z0-9_.-]+")


def run_universal_kaggle_audit(root: str | Path = ".") -> dict[str, Any]:
    base = Path(root).resolve()
    checks: dict[str, dict[str, Any]] = {}

    def check(name: str, passed: bool, detail: Any) -> None:
        checks[name] = {"passed": bool(passed), "detail": detail}

    matrix_path = base / "reports/CERTGEN_FOUR_ACCOUNT_PORTABILITY_MATRIX.csv"
    with matrix_path.open(encoding="utf-8", newline="") as handle:
        matrix = list(csv.DictReader(handle))
    expected_lanes = {
        "diagnostic", "preflight", "generation", "features",
        "diagnostic_output", "preflight_output", "generation_output", "features_output",
        "builder_faithful_rehearsal",
    }
    accounts = {row["account_fixture"] for row in matrix}
    complete_accounts = all(
        {row["stage"] for row in matrix if row["account_fixture"] == account} == expected_lanes
        for account in accounts
    )
    check(
        "four_account_matrix",
        len(accounts) == 4 and len(matrix) == 36 and complete_accounts
        and all(row["result"] == "PASS" for row in matrix),
        {"rows": len(matrix), "accounts": len(accounts), "lanes_per_account": len(expected_lanes)},
    )

    state = json.loads((base / "reports/CERTGEN_UNIVERSAL_KAGGLE_CURRENT_STATE.json").read_text(encoding="utf-8"))
    required_state = {
        "universal_account_support",
        "arbitrary_filename_support",
        "arbitrary_mount_support",
        "recursive_discovery_support",
        "extracted_package_support",
        "multiple_dataset_support",
        "local_return_recursive_support",
        "dependency_profiles_closed",
        "online_mode_tested",
        "offline_wheelhouse_tested",
        "preinstalled_mode_tested",
        "four_account_matrix_passed",
    }
    check("current_state", all(state.get(name) is True for name in required_state) and state.get("claim_allowed") is False, state)

    package_root = base / "artifacts/cvpr/kaggle_inputs"
    package_results: dict[str, str] = {}
    for stage, package_type in (
        ("diagnostic", PackageType.DIAGNOSTIC_INPUT),
        ("preflight", PackageType.PREFLIGHT_INPUT),
    ):
        result = discover_packages(
            (package_root,),
            requirement=PackageRequirement(
                expected_package_type=package_type,
                expected_stage=stage,
                required_completion_status="INPUT_PACKAGE_READY",
            ),
        )
        package_results[stage] = result.status.value
    check(
        "canonical_packages_content_discoverable",
        all(status == SelectionStatus.SELECTED_UNIQUE_VALID_PACKAGE.value for status in package_results.values()),
        package_results,
    )

    notebooks = validate_phase1_notebooks(base, deterministic=True)
    notebook_text = "\n".join(
        (base / relative).read_text(encoding="utf-8") for relative in PHASE1_NOTEBOOKS.values()
    )
    check(
        "canonical_notebooks_shared_discovery",
        notebooks["passed"] and "certgen.discovery" in notebook_text and "glob(\"*/configuration.yaml\")" not in notebook_text,
        notebooks,
    )
    dependency = _locks(base)
    check("dependency_closure", dependency["passed"], dependency)

    hits: list[str] = []
    for source_root in (base / "certgen/discovery", base / "certgen/notebooks", base / "certgen/phase1"):
        for path in source_root.rglob("*.py"):
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                if ACCOUNT_PATH.search(line):
                    hits.append(f"{path.relative_to(base).as_posix()}:{number}")
    check("no_account_specific_runtime_paths", not hits, hits or "none")
    check("evidence_boundary", state.get("claim_allowed") is False, "claim_allowed=false")
    passed = all(row["passed"] for row in checks.values())
    payload = {
        "schema_version": "certgen.universal_kaggle.audit.v1",
        "status": "UNIVERSAL_KAGGLE_AUDIT_PASS" if passed else "LOCAL_DEFECT",
        "passed": passed,
        "checks": checks,
        "claim_allowed": False,
    }
    lines = [
        "# CertGen universal Kaggle final audit",
        "",
        f"Status: `{payload['status']}`",
        "",
        "| Check | Passed |",
        "|---|---:|",
        *[f"| `{name}` | `{row['passed']}` |" for name, row in checks.items()],
        "",
        "This is a local, synthetic/static audit. It does not claim a real Kaggle run or empirical evidence. `claim_allowed=false`.",
    ]
    (base / "reports/CERTGEN_UNIVERSAL_KAGGLE_FINAL_AUDIT.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    return payload
