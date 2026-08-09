"""Deterministic, output-free Kaggle T4x2 notebook factory."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from certgen.icml2027.common import stable_hash, write_json


NOTEBOOKS: dict[str, dict[str, str]] = {
    "dinov2_preflight": {"filename": "certgen_icml2027_dinov2_preflight_t4x2.ipynb", "stage": "preflight"},
    "dinov2_features": {"filename": "certgen_icml2027_dinov2_features_t4x2.ipynb", "stage": "features"},
    "cifar_cross_family_preflight": {"filename": "certgen_icml2027_cifar_cross_family_preflight_t4x2.ipynb", "stage": "preflight"},
    "cifar_10k_generation": {"filename": "certgen_icml2027_cifar_10k_generation_t4x2.ipynb", "stage": "generation"},
    "cifar_10k_features": {"filename": "certgen_icml2027_cifar_10k_features_t4x2.ipynb", "stage": "features"},
    "released_sample_features": {"filename": "certgen_icml2027_released_sample_features_t4x2.ipynb", "stage": "features"},
    "ffhq": {"filename": "ffhq/certgen_icml2027_ffhq_t4x2.ipynb", "stage": "blocked_plan"},
    "imagenet": {"filename": "imagenet/certgen_icml2027_imagenet_t4x2.ipynb", "stage": "blocked_plan"},
    "text_to_image": {"filename": "text_to_image/certgen_icml2027_text_to_image_t4x2.ipynb", "stage": "blocked_plan"},
}


def _source(lines: list[str]) -> list[str]:
    return [line + ("" if line.endswith("\n") else "\n") for line in lines]


def build_notebook(notebook_id: str) -> dict[str, Any]:
    spec = NOTEBOOKS[notebook_id]
    stage = spec["stage"]
    bootstrap = [
        "# Trusted bootstrap and exact package identity",
        "import json, os, shutil, subprocess, sys, zipfile",
        "from pathlib import Path",
        "from certgen.notebooks.trusted_bootstrap import discover_authenticated_package",
        "EXPECTED_IDENTITY = json.loads(os.environ['CERTGEN_EXPECTED_PACKAGE_IDENTITY_JSON'])",
        "INPUT_ROOTS = [Path('/kaggle/input')]",
        "authenticated = discover_authenticated_package(INPUT_ROOTS, EXPECTED_IDENTITY)",
        "assert authenticated['selection_status'] in {'SELECTED_UNIQUE_VALID_PACKAGE','DUPLICATE_IDENTICAL_COPY_DEDUPED'}",
    ]
    runtime = [
        "# Dependency restart marker, GPU visibility, worker isolation, and disk guard",
        "RESTART_MARKER = Path('/kaggle/working/.certgen_dependency_restart_complete')",
        "if not RESTART_MARKER.exists():",
        "    raise RuntimeError('dependency bootstrap/restart marker is required')",
        "import torch",
        "if torch.cuda.device_count() != 2:",
        "    raise RuntimeError(f'exactly two visible GPUs required, found {torch.cuda.device_count()}')",
        "free = shutil.disk_usage('/kaggle/working').free",
        "if free < 10 * 1024**3:",
        "    raise RuntimeError('disk guard: fewer than 10 GiB free')",
        "WORKER_ENV = {'CUDA_VISIBLE_DEVICES': None, 'CERTGEN_CPU_ONLY': '0'}",
    ]
    execution = [
        f"# Deterministic {stage} shards, asset resolution, resume/restart, and output identity closure",
        f"STAGE = {stage!r}",
        f"NOTEBOOK_ID = {notebook_id!r}",
        "SHARDS = list(range(int(os.environ.get('CERTGEN_NUM_SHARDS', '1'))))",
        "for shard_id in SHARDS:",
        "    marker = Path(f'/kaggle/working/completed_shard_{shard_id:04d}.json')",
        "    if marker.exists():",
        "        continue  # deterministic resume",
        "    raise RuntimeError('worker execution requires an authenticated stage input and explicit worker command')",
        "# A real run replaces the fail-closed boundary above only through the source-controlled worker.",
        "# Final ZIP validation must verify membership, hashes, stage identity, configuration hash, and completion status.",
        "# Copy the validated ZIP back before local import/resume; never treat notebook state as evidence.",
    ]
    return {
        "cells": [
            {"cell_type": "markdown", "metadata": {}, "source": _source([
                f"# CertGen ICML 2027 — {notebook_id}",
                "Planning/execution notebook. `claim_allowed=false`. No outputs are source-controlled.",
            ])},
            {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": _source(bootstrap)},
            {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": _source(runtime)},
            {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": _source(execution)},
        ],
        "metadata": {
            "accelerator": "GPU",
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.11"},
            "certgen": {"notebook_id": notebook_id, "stage": stage, "gpu_count": 2, "claim_allowed": False},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def generate_notebooks(root: str | Path = "notebooks/kaggle/icml2027") -> dict[str, Any]:
    target = Path(root)
    rows: list[dict[str, Any]] = []
    for notebook_id, spec in NOTEBOOKS.items():
        payload = build_notebook(notebook_id)
        path = target / spec["filename"]
        write_json(path, payload)
        rows.append({"notebook_id": notebook_id, "path": str(path), "sha256": stable_hash(payload), "claim_allowed": False})
    return {"passed": True, "notebooks": rows, "claim_allowed": False}


def check_notebook_determinism(root: str | Path = "notebooks/kaggle/icml2027") -> dict[str, Any]:
    target = Path(root)
    results: list[dict[str, Any]] = []
    for notebook_id, spec in NOTEBOOKS.items():
        path = target / spec["filename"]
        expected = build_notebook(notebook_id)
        actual = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None
        errors: list[str] = []
        if actual != expected:
            errors.append("notebook differs from deterministic factory output")
        if actual:
            if any(cell.get("outputs") for cell in actual.get("cells", []) if cell.get("cell_type") == "code"):
                errors.append("source-controlled notebook contains outputs")
            text = "\n".join("".join(cell.get("source", [])) for cell in actual.get("cells", []))
            for token in (
                "discover_authenticated_package", "EXPECTED_IDENTITY", "RESTART_MARKER", "torch.cuda.device_count() != 2",
                "disk guard", "deterministic resume", "Final ZIP validation", "Copy the validated ZIP",
            ):
                if token not in text:
                    errors.append(f"required notebook contract token missing: {token}")
        results.append({"notebook_id": notebook_id, "path": str(path), "passed": not errors, "errors": errors})
    return {"passed": all(row["passed"] for row in results), "results": results, "claim_allowed": False}
