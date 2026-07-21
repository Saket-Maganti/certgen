"""Structural and safety analyzer for canonical CVPR Kaggle notebooks."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any, Iterable

from certgen.notebooks.cvpr_factory import NOTEBOOK_SPECS


SECRET_PATTERNS = (re.compile(r"sk-[A-Za-z0-9]{20,}"), re.compile(r"ghp_[A-Za-z0-9]{20,}"))
REQUIRED_TAGS = {
    "title",
    "environment-bootstrap",
    "input-discovery",
    "input-hash-config-validation",
    "network-cache-policy",
    "disk-check",
    "gpu-visibility-parent-no-cuda",
    "worker-script-preparation",
    "subprocess-launch",
    "per-worker-monitoring",
    "resume-restart-force",
    "shard-validation",
    "deterministic-merge",
    "integrity-manifest",
    "deterministic-output-zip",
    "copyback-recovery",
    "final-status",
}


def analyze_notebook(path: str | Path) -> dict[str, Any]:
    notebook_path = Path(path)
    errors: list[str] = []
    try:
        payload = json.loads(notebook_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return {"path": str(path), "passed": False, "errors": [str(error)], "claim_allowed": False}
    if payload.get("nbformat") != 4 or not isinstance(payload.get("cells"), list):
        errors.append("invalid notebook schema")
    code = "\n".join("".join(cell.get("source", [])) for cell in payload.get("cells", []) if cell.get("cell_type") == "code")
    text = "\n".join("".join(cell.get("source", [])) for cell in payload.get("cells", []))
    try:
        ast.parse(code)
    except SyntaxError as error:
        errors.append(f"Python syntax error: {error}")
    tags = {
        tag.removeprefix("certgen:")
        for cell in payload.get("cells", [])
        for tag in cell.get("metadata", {}).get("tags", [])
        if isinstance(tag, str) and tag.startswith("certgen:")
    }
    errors.extend(f"missing contract cell: {tag}" for tag in sorted(REQUIRED_TAGS - tags))
    for index, cell in enumerate(payload.get("cells", [])):
        if cell.get("cell_type") == "code" and (cell.get("outputs") or cell.get("execution_count") is not None):
            errors.append(f"stored execution state in cell {index}")
    required = {
        "non_evidence_labels": "claim_allowed=false" in text and "not paper evidence" in text,
        "shared_environment_bootstrap": "bootstrap_environment" in code,
        "explicit_asset_policy": "AssetPolicy" in code,
        "separate_network_policies": "dependency_network_allowed" in code and "model_asset_network_allowed" in code,
        "subprocess_worker_isolation": "run_workers" in code and "WorkerSpec" in code,
        "explicit_gpu_pinning": "physical_gpu=" in code and "CUDA_VISIBLE_DEVICES" not in code,
        "parent_cuda_non_initialization": "nvidia-smi" in code and "torch.cuda" not in code and "import torch" not in code,
        "non_overlapping_shards": "assert_unique_shards" in code,
        "resume_modes": all(mode in code for mode in ("resume", "restart", "force_new_run")) and "worker_completion.json" in code,
        "atomic_integrity": "write_integrity_manifest" in code,
        "idempotent_final_zip": "finalize_output_zip" in code,
        "shared_output_schema": "output_schema_version" in code,
        "copyback_import": "python3 -m certgen import" in text,
        "failure_recovery": "rerun_command" in code and "BLOCKED_PARTIAL_FAILURE" in code,
    }
    errors.extend(f"missing contract: {name}" for name, present in required.items() if not present)
    forbidden = (
        "ProcessPoolExecutor",
        'get_context("fork")',
        "multiprocessing.get_context",
        "claim_allowed=True",
        '"claim_allowed": True',
        "certify_clean_metric",
        "run_batch_certificates",
        "|| true",
        "/Users/",
        "errorless",
        "production proven",
    )
    errors.extend(f"forbidden text: {item}" for item in forbidden if item in text)
    errors.extend(f"secret-like pattern: {pattern.pattern}" for pattern in SECRET_PATTERNS if pattern.search(text))
    marker = (payload.get("metadata") or {}).get("certgen") or {}
    if marker.get("runtime_architecture") != "isolated_subprocess_workers":
        errors.append("notebook metadata does not declare isolated subprocess workers")
    return {
        "path": str(path),
        "passed": not errors,
        "errors": errors,
        "claim_allowed": False,
        "static_only": True,
        "real_kaggle_tested": False,
    }


def analyze_all(paths: Iterable[str | Path] | None = None) -> dict[str, Any]:
    results = [analyze_notebook(path) for path in list(paths or NOTEBOOK_SPECS)]
    return {
        "passed": all(row["passed"] for row in results),
        "results": results,
        "static_only": True,
        "fixture_runtime_required": True,
        "real_run_required": True,
        "claim_allowed": False,
    }
