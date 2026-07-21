#!/usr/bin/env python3
"""Run every currently available CertGen CPU stage and stop at a real boundary."""

# ruff: noqa: E402 -- CPU policy must be installed before importing project modules.

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any


os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["CERTGEN_CPU_ONLY"] = "1"

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from certgen.core.hashing import file_sha256
from certgen.discovery import (
    PackageCandidate,
    PackageRequirement,
    PackageType,
    SelectionStatus,
    configured_roots,
    discover_packages,
)
from certgen.cvpr.reference import materialize_reference_source, validate_reference_source
from certgen.cvpr.study import freeze_study
from certgen.max_ceiling.contracts import freeze_scale_plan, freeze_sensitivity
from certgen.packaging.v9_import_repair import import_repair
from certgen.paper.v9_paper_firewall import run_firewall
from certgen.phase1.kaggle import (
    build_static_input,
    import_diagnostic_output,
    validate_input,
    write_blocked_plan,
)
from certgen.phase1.notebooks import validate_phase1_notebooks, write_phase1_notebooks
from certgen.phase1.state import phase1_state
from certgen.pipeline.v9_next_action import determine_next_action


EXIT_LABELS = {
    0: "CPU_AVAILABLE_STAGES_COMPLETE",
    10: "WAITING_FOR_REFERENCE",
    11: "WAITING_FOR_KAGGLE_DIAGNOSTIC",
    12: "WAITING_FOR_KAGGLE_PREFLIGHT",
    13: "WAITING_FOR_KAGGLE_GENERATION",
    14: "WAITING_FOR_KAGGLE_FEATURES",
    20: "SCIENTIFIC_GATE_FAILED",
    30: "LOCAL_DEFECT",
}


def _assert_cpu_only() -> None:
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "" or os.environ.get("CERTGEN_CPU_ONLY") != "1":
        raise RuntimeError("CPU-only environment policy is not active")
    if "torch" in sys.modules:
        raise RuntimeError("unexpected local PyTorch/CUDA-capable import before CPU orchestration")


OUTPUT_REQUIREMENTS = {
    "diagnostic": (PackageType.DIAGNOSTIC_OUTPUT, ("KAGGLE_DIAGNOSTIC_PASS",)),
    "preflight": (PackageType.PREFLIGHT_OUTPUT, ("PREFLIGHT_PASS",)),
    "generation": (PackageType.GENERATION_OUTPUT, ("GENERATION_COMPLETE", "VALIDATED_GENERATED_PILOT")),
    "features": (PackageType.FEATURE_OUTPUT, ("FEATURE_EXTRACTION_SHARDS_COMPLETE",)),
}


def _returned_package(search_roots: tuple[Path, ...], stage: str) -> PackageCandidate | None:
    package_type, statuses = OUTPUT_REQUIREMENTS[stage]
    result = discover_packages(
        search_roots,
        requirement=PackageRequirement(
            expected_package_type=package_type,
            expected_stage=stage,
            required_completion_status=statuses,
        ),
    )
    if result.status is SelectionStatus.NO_MATCHING_PACKAGE:
        return None
    if result.status is not SelectionStatus.SELECTED_UNIQUE_VALID_PACKAGE or result.selected is None:
        matches = [str(row.path) for row in result.matching_candidates]
        raise RuntimeError(f"ambiguous returned {stage} packages: {matches}")
    return result.selected


@contextmanager
def _zip_for_import(candidate: PackageCandidate):  # type: ignore[no-untyped-def]
    if candidate.path.is_file():
        yield candidate.path
        return
    from certgen.notebooks.kaggle_io import deterministic_zip

    with tempfile.TemporaryDirectory(prefix="certgen_extracted_output_import_") as temporary:
        archive = Path(temporary) / "content-addressed-output.zip"
        deterministic_zip(candidate.path, archive)
        yield archive


def _run_canonical_cpu_frontier(root: Path, steps: list[dict[str, Any]]) -> tuple[int | None, str | None]:
    """Execute canonical local commands until the dispatcher reaches GPU or user input."""

    seen: set[tuple[str, str]] = set()
    for _ in range(64):
        action = determine_next_action(root=root)
        key = (str(action.get("status")), str(action.get("exact_command")))
        if key in seen:
            return 30, f"state machine repeated without progress: {key[0]}"
        seen.add(key)
        if action.get("CPU_or_GPU") != "CPU" or action.get("action") in {
            "PROVIDE_CIFAR_REFERENCE",
            "STOP_FIRST_PILOT_COMPLETE",
        }:
            return None, None
        command = shlex.split(str(action["exact_command"]))
        if command[:3] != ["python3", "-m", "certgen"]:
            return 30, f"refusing non-canonical CPU frontier command: {command}"
        result = subprocess.run(command, cwd=root, env=os.environ.copy(), capture_output=True, text=True)
        steps.append(
            {
                "step": f"canonical_cpu_{action['action'].lower()}",
                "result": {
                    "command": command,
                    "exit_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "claim_allowed": False,
                },
            }
        )
        if result.returncode != 0:
            return (20 if "GATE" in str(action.get("action")) else 30), result.stderr or result.stdout
    return 30, "canonical CPU frontier exceeded 64 transitions"


def _run(
    root: Path,
    *,
    dry_run: bool,
    explain: bool,
    search_roots: tuple[Path, ...] | None = None,
) -> tuple[int, dict[str, Any]]:
    os.chdir(root)
    _assert_cpu_only()
    steps: list[dict[str, Any]] = []
    resolved_search_roots = search_roots or configured_roots(repository_root=root)

    def add(name: str, payload: Any) -> None:
        steps.append({"step": name, "result": payload})

    if dry_run:
        notebooks = validate_phase1_notebooks(root, deterministic=False)
    else:
        write_phase1_notebooks(root)
        notebooks = validate_phase1_notebooks(root, deterministic=True)
    add("notebooks", notebooks)
    if not notebooks["passed"]:
        return 30, {"steps": steps, "errors": ["canonical notebook validation failed"]}

    for stage in ("diagnostic", "preflight"):
        built = build_static_input(stage, root=root, dry_run=dry_run)
        add(f"build_{stage}_input", built)
        if not dry_run:
            verdict = validate_input(root / built["zip_path"])
            add(f"validate_{stage}_input", verdict)
            if not verdict["passed"]:
                return 30, {"steps": steps, "errors": verdict["errors"]}
    for stage in ("generation", "features"):
        add(f"blocked_{stage}_plan", write_blocked_plan(stage, root=root, dry_run=dry_run))

    if not dry_run:
        diagnostic_package = _returned_package(resolved_search_roots, "diagnostic")
        if diagnostic_package:
            with _zip_for_import(diagnostic_package) as diagnostic_zip:
                result = import_diagnostic_output(diagnostic_zip, root=root)
            add("import_diagnostic", result)
            if not result.get("passed"):
                return 30, {"steps": steps, "errors": result.get("errors", [])}
        preflight_package = _returned_package(resolved_search_roots, "preflight")
        if preflight_package:
            with _zip_for_import(preflight_package) as preflight_zip:
                result = import_repair(
                    kind="preflight",
                    zip_path=preflight_zip,
                    out_json=root / "data/results/cvpr/preflight_import_status.json",
                    out_report=root / "reports/CERTGEN_PHASE1_PREFLIGHT_IMPORT.md",
                    registry_path=root / "data/artifact_registry.jsonl",
                )
            add("import_preflight", result)
            if not result.get("passed"):
                return 30, {"steps": steps, "errors": result.get("errors", [])}
        for returned_kind, import_kind in (("generation", "generation"), ("features", "feature")):
            returned_package = _returned_package(resolved_search_roots, returned_kind)
            if returned_package:
                with _zip_for_import(returned_package) as returned_zip:
                    result = import_repair(
                        kind=import_kind,
                        zip_path=returned_zip,
                        out_json=root / f"data/results/cvpr/{import_kind}_import_status.json",
                        out_report=root / f"reports/CERTGEN_PHASE1_{returned_kind.upper()}_IMPORT.md",
                        registry_path=root / "data/artifact_registry.jsonl",
                    )
                add(f"import_{returned_kind}", result)
                if not result.get("passed"):
                    return 30, {"steps": steps, "errors": result.get("errors", [])}

    source = root / "data/sources/cifar-10-python.tar.gz"
    reference = root / "registry/manifests/cvpr/cifar10_reference.jsonl"
    if source.is_file():
        validation = validate_reference_source(source)
        add("validate_cifar", {**validation, "source_sha256": file_sha256(source), "source_size": source.stat().st_size})
        if not validation["passed"]:
            return 30, {"steps": steps, "errors": validation["errors"]}
        if not reference.is_file() and not dry_run:
            add(
                "materialize_cifar",
                materialize_reference_source(
                    source,
                    out_manifest=reference,
                    out_summary=root / "data/results/cvpr_reference_materialization.json",
                ),
            )
    else:
        add("cifar", {"status": "WAITING_FOR_OFFICIAL_ARCHIVE", "expected_path": str(source.relative_to(root))})

    if reference.is_file():
        study = root / "artifacts/cvpr/study/cifar_integrity_minimal.yaml"
        if not study.is_file() and not dry_run:
            add("freeze_study", freeze_study("cifar_integrity_minimal", out_path=study))
        if study.is_file() and not dry_run:
            add("freeze_scale_plan", freeze_scale_plan(study, root=root))
            add("freeze_sensitivity", freeze_sensitivity(study, root=root))
            draw = root / "registry/manifests/cvpr/reference_draw_plan.json"
            if not draw.is_file():
                from certgen.cvpr.reference_draw import prepare_reference_draw

                add(
                    "reference_draw",
                    prepare_reference_draw(
                        profile_id="cifar_integrity_minimal",
                        study_path=study,
                        reference_manifest=reference,
                        out_path=draw,
                        registry_path=root / "data/artifact_registry.jsonl",
                    ),
                )
            add("paper_firewall", run_firewall())

    if not dry_run:
        current_phase = phase1_state(root)
        if current_phase["preflight_imported"]:
            failure_code, failure = _run_canonical_cpu_frontier(root, steps)
            if failure_code is not None:
                return failure_code, {
                    "steps": steps,
                    "errors": [failure or "canonical CPU frontier failed"],
                }
        else:
            add(
                "canonical_cpu_frontier",
                {
                    "status": "DEFERRED_UNTIL_VALID_PREFLIGHT_IMPORT",
                    "boundary": current_phase["boundary"],
                    "claim_allowed": False,
                },
            )

    state = phase1_state(root)
    code = int(state["exit_code"])
    payload = {
        "schema_version": "certgen.phase1.cpu_autorun.v1",
        "status": EXIT_LABELS[code],
        "exit_code": code,
        "dry_run": dry_run,
        "cpu_only": True,
        "search_roots": [str(path) for path in resolved_search_roots],
        "steps": steps,
        "state": state,
        "exact_next_action": state["exact_next_action"],
        "claim_allowed": False,
    }
    if not dry_run:
        output = root / "reports/CERTGEN_PHASE1_AUTORUN_STATUS.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if explain:
        payload["explanation"] = "All local static and CPU actions were attempted; the exit code names the first genuine external boundary."
    return code, payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--explain", action="store_true")
    parser.add_argument("--search-root", action="append", default=[])
    args = parser.parse_args(argv)
    if not args.dry_run and not args.resume:
        parser.error("choose --dry-run or --resume")
    try:
        root = Path(args.root).resolve()
        roots = configured_roots(args.search_root, repository_root=root) if args.search_root else None
        code, payload = _run(root, dry_run=args.dry_run, explain=args.explain, search_roots=roots)
    except Exception as exc:
        code = 30
        payload = {
            "status": EXIT_LABELS[code],
            "exit_code": code,
            "error": f"{type(exc).__name__}: {exc}",
            "cpu_only": True,
            "claim_allowed": False,
        }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
