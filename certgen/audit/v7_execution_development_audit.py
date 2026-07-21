"""Final V7 execution-development audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


CHECKS = {
    "cifar_autodetect": "certgen/data/autodetect_cifar10_root.py",
    "generation_bookrun": "notebooks/kaggle/v7_certgen_cifar10_generation_t4x2_bookrun.ipynb",
    "feature_bookrun": "notebooks/kaggle/v7_certgen_cifar10_feature_extraction_t4x2_bookrun.ipynb",
    "generation_importer": "certgen/packaging/import_kaggle_generation_outputs.py",
    "feature_importer": "certgen/packaging/import_kaggle_feature_outputs.py",
    "run_ledger": "certgen/runledger/ledger.py",
    "scale_lanes": "configs/v7_scale_lanes/cifar10_1k.yaml",
    "notebook_validator": "certgen/notebooks/validate_kaggle_notebooks.py",
    "paper_result_gate": "certgen/paper/audit_result_injection_gate.py",
}


def audit() -> dict[str, object]:
    checks = {name: Path(path).exists() for name, path in CHECKS.items()}
    text_hits = []
    for path in Path(".").rglob("*"):
        if any(part.startswith("certgen_prompt_pack") for part in path.parts):
            continue
        if path.parts[:2] == ("certgen", "audit") or path.parts[:2] == ("tests",):
            continue
        if path.is_file() and path.suffix in {".md", ".json", ".yaml", ".yml", ".ipynb"}:
            text = path.read_text(encoding="utf-8", errors="ignore")
            if '"claim_allowed": true' in text or "claim_allowed: true" in text:
                text_hits.append(str(path))
    blocker = "BLOCKED_MISSING_REFERENCE_SAMPLES"
    return {
        "checks": checks,
        "all_checks_pass": all(checks.values()) and not text_hits,
        "claim_allowed_true_hits": text_hits,
        "status_code": blocker,
        "current_blocker": blocker,
        "next_local_cpu_command": (
            "CIFAR_SEARCH_ROOT=/path/to/cifar bash "
            "commands/v7_cpu_execution/01_auto_materialize_cifar_reference.sh"
        ),
        "next_kaggle_step": "Run generation bookrun after reference materialization package exists.",
        "claim_allowed": False,
        "evidence_status": "NO_REAL_EVIDENCE",
    }


def write_report(payload: dict[str, object], path: str | Path) -> None:
    lines = [
        "# V7 Execution Development Audit",
        "",
        f"Status code: `{payload['status_code']}`",
        f"Current blocker: `{payload['current_blocker']}`",
        f"Next local CPU command: `{payload['next_local_cpu_command']}`",
        f"Next Kaggle step: `{payload['next_kaggle_step']}`",
        "",
        "No `claim_allowed=true` hits were permitted.",
    ]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--json-out", required=True)
    args = parser.parse_args(argv)
    payload = audit()
    Path(args.json_out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json_out).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(payload, args.out)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["all_checks_pass"] else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
