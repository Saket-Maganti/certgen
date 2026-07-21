"""Truthful Phase 1 state derived only from live immutable artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from certgen.pipeline.v9_next_action import determine_next_action


def _passed(path: Path) -> bool:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return payload.get("passed") is True or payload.get("status_code") in {
        "KAGGLE_DIAGNOSTIC_PASS",
        "PREFLIGHT_PASS",
    }


def _reference_ready(root: Path) -> bool:
    path = root / "registry/manifests/cvpr/cifar10_reference.jsonl"
    if not path.is_file():
        return False
    return sum(bool(line.strip()) for line in path.read_text(encoding="utf-8").splitlines()) == 10_000


def phase1_state(root: str | Path = ".") -> dict[str, Any]:
    base = Path(root).resolve()
    source = next(
        (
            path
            for path in (
                base / "data/sources/cifar-10-python.tar.gz",
                base / "cifar-10-python.tar.gz",
            )
            if path.is_file()
        ),
        base / "data/sources/cifar-10-python.tar.gz",
    )
    reference = _reference_ready(base)
    diagnostic = _passed(base / "data/results/cvpr/diagnostic_import_status.json")
    preflight = _passed(base / "data/results/cvpr/preflight_import_status.json")
    canonical = determine_next_action(root=base)
    if not source.is_file() or not reference:
        phase_status = "PHASE1_COMPLETE_WAITING_FOR_REFERENCE"
        boundary = "reference"
        exit_code = 10
        source_argument = source.relative_to(base).as_posix()
        exact = f"python3 -m certgen validate reference --source {source_argument} --explain"
        notebook = None
    elif not diagnostic:
        phase_status = "PHASE1_COMPLETE_WAITING_FOR_KAGGLE_DIAGNOSTIC"
        boundary = "kaggle_diagnostic"
        exit_code = 11
        exact = (
            "Upload artifacts/cvpr/kaggle_inputs/diagnostic/"
            "certgen_kaggle_environment_diagnostic_input.zip and run "
            "notebooks/kaggle/certgen_kaggle_environment_diagnostic_t4x2.ipynb on GPU T4 x2"
        )
        notebook = "notebooks/kaggle/certgen_kaggle_environment_diagnostic_t4x2.ipynb"
    elif not preflight:
        phase_status = "PHASE1_COMPLETE_WAITING_FOR_KAGGLE_PREFLIGHT"
        boundary = "kaggle_preflight"
        exit_code = 12
        exact = (
            "Upload artifacts/cvpr/kaggle_inputs/preflight/certgen_cvpr_preflight_input.zip "
            "with the private asset dataset and run "
            "notebooks/kaggle/certgen_cvpr_checkpoint_preflight_t4x2.ipynb on GPU T4 x2"
        )
        notebook = "notebooks/kaggle/certgen_cvpr_checkpoint_preflight_t4x2.ipynb"
    else:
        action = str(canonical.get("action", ""))
        if "GENERATION" in action:
            exit_code, boundary = 13, "kaggle_generation"
        elif "FEATURE" in action:
            exit_code, boundary = 14, "kaggle_features"
        else:
            exit_code, boundary = 0, "cpu_or_complete"
        phase_status = "CPU_AVAILABLE_STAGES_COMPLETE"
        exact = str(canonical.get("exact_command", ""))
        notebook = canonical.get("notebook_path")
    return {
        "schema_version": "certgen.phase1.state.v1",
        "phase1_status": phase_status,
        "boundary": boundary,
        "exit_code": exit_code,
        "cifar_source": str(source.relative_to(base)),
        "cifar_present": source.is_file(),
        "reference_materialized": reference,
        "diagnostic_imported": diagnostic,
        "preflight_imported": preflight,
        "exact_next_action": exact,
        "next_notebook": notebook,
        "canonical_next_action": canonical,
        "claim_allowed": False,
    }
