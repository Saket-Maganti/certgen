"""Deterministic Phase 1 Kaggle T4x2 notebook generation and validation."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
from typing import Any

from certgen.notebooks.cvpr_factory import (
    _expected_identity_from_active_bundle,
    build_notebook,
    input_discovery_code,
)


PHASE1_NOTEBOOKS = {
    "diagnostic": "notebooks/kaggle/certgen_kaggle_environment_diagnostic_t4x2.ipynb",
    "preflight": "notebooks/kaggle/certgen_cvpr_checkpoint_preflight_t4x2.ipynb",
    "generation": "notebooks/kaggle/certgen_cvpr_generation_1k_t4x2.ipynb",
    "features": "notebooks/kaggle/certgen_cvpr_feature_extraction_t4x2.ipynb",
}

SECTIONS = (
    "0 Human instructions",
    "1 Immutable user configuration",
    "2 Input discovery",
    "3 Environment diagnostics",
    "4 Dependency setup and validation",
    "5 Asset discovery and validation",
    "6 Configuration/provenance validation",
    "7 Tiny dual-GPU dry run",
    "8 Runtime calibration",
    "9 Full parallel execution",
    "10 Merge and validation",
    "11 Atomic output ZIP",
    "12 Local handoff",
)


def _cell(cell_type: str, source: str, tag: str) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "cell_type": cell_type,
        "metadata": {"tags": [f"certgen:phase1-{tag}"]},
        "source": [line + "\n" for line in source.strip().splitlines()],
    }
    if cell_type == "code":
        payload.update({"execution_count": None, "outputs": []})
    return payload


def _heading(index: int, extra: str = "") -> dict[str, Any]:
    body = f"## {SECTIONS[index]}"
    if extra:
        body += "\n\n" + extra
    return _cell("markdown", body, f"section-{index}")


def _tiny_gpu_code() -> str:
    return '''
import multiprocessing as mp
mp.set_start_method("spawn", force=True)
from certgen.notebooks.subprocess_orchestrator import WorkerSpec, run_workers
TINY_SPECS = [
    WorkerSpec(
        worker_id=f"tiny_gpu_{gpu}",
        module="certgen.notebooks.workers.diagnostic_worker",
        physical_gpu=gpu,
        shard_id=f"tiny_gpu_{gpu}",
        args=("--out", str(RUN_ROOT / "tiny_gpu_diagnostic" / f"gpu_{gpu}"),
              "--configuration-hash", CONFIG["configuration_hash"],
              "--input-manifest-hash", str(CONFIG.get("input_manifest_hash", CONFIG.get("reference_manifest_hash", "diagnostic_static_input")))),
        completion_marker=str(RUN_ROOT / "tiny_gpu_diagnostic" / f"gpu_{gpu}" / "worker_completion.json"),
        configuration_hash=CONFIG["configuration_hash"],
        input_manifest_hash=str(CONFIG.get("input_manifest_hash", CONFIG.get("reference_manifest_hash", "diagnostic_static_input"))),
        asset_manifest_hash="no_assets_required",
        worker_type="diagnostic",
        config_schema_version="certgen.kaggle.diagnostic_config.v1",
        output_schema_version="certgen.kaggle.diagnostic_output.v1",
    )
    for gpu in range(2)
]
TINY_DUAL_GPU = run_workers(TINY_SPECS, output_dir=RUN_ROOT / "tiny_gpu_orchestration", resume=MODE == "resume")
if sorted(row["physical_gpu"] for row in TINY_DUAL_GPU["workers"]) != [0, 1]:
    raise RuntimeError("tiny dry run did not execute one worker on each physical GPU")
'''


def _calibration_code() -> str:
    return '''
from certgen.cvpr.contracts import atomic_write_json
CALIBRATION_ROWS = [
    json.loads((RUN_ROOT / "tiny_gpu_diagnostic" / f"gpu_{gpu}" / "diagnostic_report.json").read_text(encoding="utf-8"))
    for gpu in range(2)
]
RUNTIME_CALIBRATION = {
    "model_load_seconds": [row["model_load_seconds"] for row in CALIBRATION_ROWS],
    "warmup_seconds": [row["warmup_seconds"] for row in CALIBRATION_ROWS],
    "throughput_iterations_per_second": [row["throughput_iterations_per_second"] for row in CALIBRATION_ROWS],
    "peak_vram_bytes": [row["peak_allocated_bytes"] for row in CALIBRATION_ROWS],
    "safe_batch_size": min(row["safe_batch_size"] for row in CALIBRATION_ROWS),
    "planning_only": True,
    "not_empirical_evidence": True,
    "claim_allowed": False,
}
atomic_write_json(RUNTIME_CALIBRATION, RUN_ROOT / "runtime_calibration.json")
'''


def _decorate(payload: dict[str, Any], kind: str) -> dict[str, Any]:
    source_cells = payload["cells"]
    title = source_cells[0]
    title["source"].extend(
        [
            "\n",
            "Select **GPU T4 ×2** in Kaggle before running any code. Kaggle Internet is used only according to the immutable dependency mode; model and extractor loading remains offline from a validated private mount.\n",
            "\n",
            "This notebook uses multiprocessing `spawn`, keeps CUDA out of the parent, and schedules one subprocess worker per physical GPU.\n",
        ]
    )
    by_before_tag = {
        "input-discovery": [
            _heading(0, "Run top-to-bottom only after selecting `GPU T4 ×2`. Never edit a frozen hash in place."),
            _heading(1),
            _heading(2),
        ],
        "environment-bootstrap": [
            _heading(3),
            _heading(4, "The bootstrap runs `python -m pip check` and writes `dependency_report.json`, `dependency_freeze.txt`, and `pip_check.txt`."),
        ],
        "input-hash-config-validation": [_heading(5), _heading(6)],
        "resume-restart-force": [_heading(7)],
        "worker-script-preparation": [_heading(8), _cell("code", _calibration_code(), "runtime-calibration"), _heading(9)],
        "shard-validation": [_heading(10)],
        "deterministic-output-zip": [_heading(11)],
        "copyback-recovery": [_heading(12)],
    }
    decorated: list[dict[str, Any]] = [title]
    for cell in source_cells[1:]:
        tags = [tag.removeprefix("certgen:") for tag in cell.get("metadata", {}).get("tags", [])]
        for tag in tags:
            decorated.extend(by_before_tag.get(tag, []))
        decorated.append(cell)
        if "resume-restart-force" in tags:
            decorated.append(_cell("code", _tiny_gpu_code(), "tiny-dual-gpu"))
    for cell in decorated:
        source = "".join(cell.get("source", []))
        if cell.get("cell_type") == "code" and "bootstrap_environment(" in source:
            source = source.replace(
                "apply=True,",
                'apply=True, install_mode=CONFIG.get("dependency_mode", "KAGGLE_INTERNET_ON_INSTALL"),',
            )
            source += '''\nif ENVIRONMENT["pip_check"]["returncode"] != 0:\n    raise RuntimeError("python -m pip check failed; inspect pip_check.txt")\n'''
            cell["source"] = [line + "\n" for line in source.strip().splitlines()]
        if cell.get("cell_type") == "code" and "ASSET_POLICY = AssetPolicy" in source:
            source += '''
from certgen.discovery import discover_asset_mount, write_asset_resolution_report
REQUIRED_ASSETS = {row["asset_id"]: row.get("revision") for row in CONFIG.get("assets", [])}
if REQUIRED_ASSETS:
    ASSET_RESOLUTION = discover_asset_mount(SEARCH_ROOTS, required_assets=REQUIRED_ASSETS)
    if ASSET_RESOLUTION["status"] not in {"SELECTED_UNIQUE_VALID_ASSET_MOUNT", "DUPLICATE_IDENTICAL_COPY_DEDUPED"}:
        raise RuntimeError(f"private asset discovery failed: {ASSET_RESOLUTION['status']}")
    ASSET_RESOLUTION_REPORT_PATH = WORK_ROOT / "asset_resolution_report.json"
    ASSET_RESOLUTION_REPORT = write_asset_resolution_report(ASSET_RESOLUTION, ASSET_RESOLUTION_REPORT_PATH)
    ASSET_RUNTIME_MAP = {row["asset_id"]: row for row in ASSET_RESOLUTION_REPORT["assets"]}
    ASSET_RUNTIME_BY_ID = {row["model_or_extractor_id"]: row for row in ASSET_RESOLUTION_REPORT["assets"]}
    ASSET_VALIDATION = ASSET_RESOLUTION
else:
    ASSET_RESOLUTION_REPORT_PATH = WORK_ROOT / "asset_resolution_report.json"
    ASSET_RUNTIME_MAP = {}
    ASSET_RUNTIME_BY_ID = {}
'''
            cell["source"] = [line + "\n" for line in source.strip().splitlines()]
        if cell.get("cell_type") == "code" and "specs = []" in source:
            source = source.replace(
                'str(INPUT_ROOT / "model_cache" / model["model_id"])',
                'str(PRIVATE_ASSET_ROOT / model["model_id"])',
            )
            source = source.replace(
                'str(INPUT_ROOT / "model_cache" / extractor["feature_space_id"])',
                'str(PRIVATE_ASSET_ROOT / ("clip-vit-large-patch14" if extractor["feature_space_id"] == "clip" else extractor["feature_space_id"]))',
            )
            cell["source"] = [line + "\n" for line in source.strip().splitlines()]
        if cell.get("cell_type") == "code" and "finalize_output_zip" in source:
            source = source.replace(
                "from certgen.notebooks.final_zip import finalize_output_zip",
                "from certgen.notebooks.final_zip import finalize_output_zip, validate_final_zip, write_multipart_fallback",
            )
            source += '''\nif not validate_final_zip(RUN_ROOT, ZIP_PATH)["passed"]:\n    raise RuntimeError("final output ZIP revalidation failed")\nMULTIPART = write_multipart_fallback(ZIP_PATH) if ZIP_PATH.stat().st_size > 3800 * 1024**2 else None\n'''
            cell["source"] = [line + "\n" for line in source.strip().splitlines()]
    payload["cells"] = decorated
    payload["metadata"]["certgen"].update(
        {
            "phase1_sections": list(SECTIONS),
            "required_accelerator": "GPU T4 x2",
            "multiprocessing_start_method": "spawn",
            "kind": kind,
        }
    )
    return payload


def _diagnostic_notebook() -> dict[str, Any]:
    cells = [
        _cell("markdown", '''# CertGen Kaggle environment diagnostic — T4 ×2

Select **GPU T4 ×2**. This is `synthetic_validation_only`, `not_empirical_evidence`, and `claim_allowed=false`. Run top-to-bottom. Do not enable model assets for this diagnostic.''', "diagnostic-title"),
        _heading(0, "Select `GPU T4 ×2`; the parent process must not import or initialize CUDA."),
        _heading(1),
        _cell("code", input_discovery_code("diagnostic") + '''
import multiprocessing as mp
mp.set_start_method("spawn", force=True)
MODE = CONFIG["mode"]
WORK_ROOT = Path("/kaggle/working/certgen-diagnostic")
RUN_ROOT = WORK_ROOT / CONFIG["run_id"]
RUN_ROOT.mkdir(parents=True, exist_ok=True)''', "configuration"),
        _heading(2),
        _cell("code", '''print(json.dumps({"input_root": str(INPUT_ROOT), "configuration_hash": CONFIG["configuration_hash"]}, indent=2))''', "input-discovery"),
        _heading(3),
        _cell("code", '''probe = subprocess.run(["nvidia-smi", "-L"], check=True, capture_output=True, text=True)
GPU_LINES = [line for line in probe.stdout.splitlines() if line.strip().startswith("GPU ")]
if len(GPU_LINES) != 2: raise RuntimeError(f"GPU T4 x2 required; found {len(GPU_LINES)} devices")''', "gpu-visibility"),
        _heading(4, "The bootstrap runs `python -m pip check` and writes `dependency_report.json`, `dependency_freeze.txt`, and `pip_check.txt`."),
        _cell("code", '''from certgen.notebooks.environment_bootstrap import bootstrap_environment
DEPENDENCIES = bootstrap_environment("kaggle_t4x2_diagnostic", output_dir=RUN_ROOT / "dependencies", network_allowed=CONFIG["dependency_network_allowed"], apply=True, install_mode=CONFIG["dependency_mode"], search_roots=SEARCH_ROOTS, lock_path=INPUT_ROOT / "requirements/stage.lock", constraints_path=INPUT_ROOT / "requirements/kaggle-constraints.txt", lock_integrity_path=INPUT_ROOT / "requirements/lock_integrity.json", expected_input_identity={"package_sha256": AUTHENTICATION_REPORT["package_sha256"], "scientific_identity_hash": AUTHENTICATION_REPORT["identity"]["scientific_identity_hash"]})
if DEPENDENCIES["status"] != "ENVIRONMENT_COMPATIBLE" or DEPENDENCIES["pip_check"]["returncode"] != 0: raise RuntimeError("dependency validation failed")''', "dependencies"),
        _heading(5),
        _cell("code", '''from certgen.notebooks.model_assets import AssetPolicy
ASSET_POLICY = AssetPolicy(CONFIG["asset_policy"])
ASSET_VALIDATION = {"required_assets": [], "passed": True, "claim_allowed": False}''', "assets"),
        _heading(6),
        _cell("code", '''from certgen.cvpr.contracts import atomic_write_json
PROVENANCE = {"configuration_hash": CONFIG["configuration_hash"], "input_manifest_hash": CONFIG["input_manifest_hash"], "claim_allowed": False}
atomic_write_json(PROVENANCE, RUN_ROOT / "provenance.json")''', "provenance"),
        _heading(7),
        _cell("code", _tiny_gpu_code(), "tiny-dual-gpu"),
        _heading(8),
        _cell("code", _calibration_code(), "runtime-calibration"),
        _heading(9),
        _cell("code", '''# For the diagnostic stage, the two-worker dry run is the complete parallel execution.
ORCHESTRATION = TINY_DUAL_GPU''', "full-parallel-execution"),
        _heading(10),
        _cell("code", '''from certgen.notebooks.kaggle_io import all_worker_statuses_complete, write_integrity_manifest
if not all_worker_statuses_complete(ORCHESTRATION): raise RuntimeError("dual-GPU diagnostic worker failure")
STATUS = {"status_code": "KAGGLE_DIAGNOSTIC_PASS", "gpu_count": 2, "configuration_hash": CONFIG["configuration_hash"], "synthetic_validation_only": True, "not_empirical_evidence": True, "claim_allowed": False}
atomic_write_json(STATUS, RUN_ROOT / "diagnostic_status.json")
write_integrity_manifest(RUN_ROOT)''', "merge-validation"),
        _heading(11),
        _cell("code", '''from certgen.notebooks.final_zip import finalize_output_zip, validate_final_zip, write_multipart_fallback
ZIP_PATH = Path("/kaggle/working/certgen_kaggle_environment_diagnostic_output.zip")
ZIP = finalize_output_zip(RUN_ROOT, ZIP_PATH, mode=MODE, configuration_hash=CONFIG["configuration_hash"], asset_manifest_hash="no_assets_required", input_identity={"package_sha256": AUTHENTICATION_REPORT["package_sha256"], "scientific_identity_hash": AUTHENTICATION_REPORT["identity"]["scientific_identity_hash"]})
if not validate_final_zip(RUN_ROOT, ZIP_PATH)["passed"]: raise RuntimeError("final diagnostic ZIP revalidation failed")
MULTIPART = write_multipart_fallback(ZIP_PATH) if ZIP_PATH.stat().st_size > 3800 * 1024**2 else None''', "atomic-output-zip"),
        _heading(12),
        _cell("markdown", '''Download the diagnostic output ZIP to any local directory; it may be renamed but must not be edited or unpacked. Run:

`CUDA_VISIBLE_DEVICES="" CERTGEN_CPU_ONLY=1 python3 scripts/run_all_available_cpu_stages.py --resume --explain --search-root /path/to/downloads`

Preserve worker logs and status files on failure; resume only when configuration and input hashes are unchanged.''', "handoff"),
    ]
    return {
        "cells": cells,
        "metadata": {
            "accelerator": "GPU",
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.11"},
            "certgen": {
                "generated_by": "certgen.phase1.notebooks.v1",
                "kind": "diagnostic",
                "required_accelerator": "GPU T4 x2",
                "multiprocessing_start_method": "spawn",
                "phase1_sections": list(SECTIONS),
                "expected_package_identity": _expected_identity_from_active_bundle("diagnostic"),
                "explicit_expected_identity_required": False,
                "trusted_bootstrap_sha256": hashlib.sha256(
                    Path(
                        str(
                            __import__(
                                "certgen.notebooks.trusted_bootstrap",
                                fromlist=["trusted_bootstrap"],
                            ).__file__
                        )
                    ).read_bytes()
                ).hexdigest(),
                "claim_allowed": False,
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def notebook_payloads() -> dict[str, dict[str, Any]]:
    return {
        "diagnostic": _diagnostic_notebook(),
        "preflight": _decorate(build_notebook("preflight", scale="preflight"), "preflight"),
        "generation": _decorate(build_notebook("generation", scale="1k"), "generation"),
        "features": _decorate(build_notebook("features", scale="1k"), "features"),
    }


def write_phase1_notebooks(root: str | Path = ".") -> dict[str, Any]:
    base = Path(root)
    written: list[str] = []
    reused: list[str] = []
    for kind, payload in notebook_payloads().items():
        path = base / PHASE1_NOTEBOOKS[kind]
        serialized = json.dumps(payload, indent=1, sort_keys=True) + "\n"
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.is_file() and path.read_text(encoding="utf-8") == serialized:
            reused.append(str(path))
        else:
            if path.is_file():
                current = json.loads(path.read_text(encoding="utf-8"))
                marker = (current.get("metadata") or {}).get("certgen") or {}
                if not marker.get("generated_by", "").startswith(("certgen.notebooks.cvpr_factory", "certgen.phase1.notebooks")):
                    raise FileExistsError(f"refusing to overwrite non-generated notebook: {path}")
            path.write_text(serialized, encoding="utf-8")
            written.append(str(path))
    return {"status": "NOTEBOOKS_READY", "written": written, "reused": reused, "claim_allowed": False}


def validate_phase1_notebooks(root: str | Path = ".", *, deterministic: bool = True) -> dict[str, Any]:
    base = Path(root)
    expected = notebook_payloads()
    results: list[dict[str, Any]] = []
    for kind, relative in PHASE1_NOTEBOOKS.items():
        path = base / relative
        errors: list[str] = []
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            results.append({"kind": kind, "path": str(path), "passed": False, "errors": [str(exc)]})
            continue
        text = "\n".join("".join(cell.get("source", [])) for cell in payload.get("cells", []))
        code = "\n".join("".join(cell.get("source", [])) for cell in payload.get("cells", []) if cell.get("cell_type") == "code")
        try:
            ast.parse(code)
        except SyntaxError as exc:
            errors.append(f"Python syntax error: {exc}")
        for section in SECTIONS:
            if section not in text:
                errors.append(f"missing section: {section}")
        required = (
            "GPU T4 ×2", "spawn", "nvidia-smi", "WorkerSpec", "physical_gpu", "configuration_hash",
            "dependency_report.json", "dependency_freeze.txt", "pip_check.txt", "safe_batch_size",
            "runtime_calibration", "finalize_output_zip", "validate_final_zip", "claim_allowed=false",
        )
        errors.extend(f"missing notebook contract: {item}" for item in required if item not in text)
        if "torch.cuda" in code or "import torch" in code:
            errors.append("parent notebook imports or initializes CUDA")
        if any(cell.get("outputs") or cell.get("execution_count") is not None for cell in payload.get("cells", []) if cell.get("cell_type") == "code"):
            errors.append("stored notebook execution state")
        serialized = json.dumps(payload, indent=1, sort_keys=True) + "\n"
        expected_serialized = json.dumps(expected[kind], indent=1, sort_keys=True) + "\n"
        if deterministic and serialized != expected_serialized:
            errors.append("notebook differs from deterministic regeneration")
        results.append({"kind": kind, "path": str(path), "passed": not errors, "errors": errors})
    return {
        "status": "PASS" if all(row["passed"] for row in results) else "LOCAL_DEFECT",
        "passed": all(row["passed"] for row in results),
        "results": results,
        "deterministic_regeneration": deterministic,
        "claim_allowed": False,
    }
