"""Deterministic, output-free Kaggle T4x2 notebook factory."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from certgen.icml2027.common import stable_hash, write_json
from certgen.icml2027.notebook_runtime import LANE_STATUS


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


def _source(text: str) -> list[str]:
    return [line + "\n" for line in text.strip("\n").splitlines()]


def _bootstrap_code(notebook_id: str) -> str:
    return f'''# STDLIB-ONLY PRE-IMPORT AUTHENTICATION BOUNDARY
from __future__ import annotations
import hashlib, json, os, shutil, stat, sys, tempfile, zipfile
from pathlib import Path, PurePosixPath

LANE = {notebook_id!r}
raw_identity = os.environ.get("CERTGEN_EXPECTED_ICML_INPUT_IDENTITY_JSON")
if not raw_identity:
    raise RuntimeError("explicit CERTGEN_EXPECTED_ICML_INPUT_IDENTITY_JSON is required")
EXPECTED_IDENTITY = json.loads(raw_identity)
if EXPECTED_IDENTITY.get("schema_version") != "certgen.icml2027.expected_input.v1" or EXPECTED_IDENTITY.get("claim_allowed") is not False:
    raise RuntimeError("invalid expected input identity")
if EXPECTED_IDENTITY.get("expected_lane") != LANE or len(EXPECTED_IDENTITY.get("expected_input_zip_sha256", "")) != 64:
    raise RuntimeError("expected input identity is incomplete or for another lane")

def _sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def _safe_name(raw):
    value = PurePosixPath(raw)
    if not raw or value.is_absolute() or ".." in value.parts or "\\\\" in raw:
        raise RuntimeError("unsafe archive member")
    return value.as_posix()

candidates = []
for search_root in [Path("/kaggle/input")]:
    if not search_root.exists() or search_root.is_symlink():
        continue
    for current, directories, files in os.walk(search_root, topdown=True, followlinks=False):
        depth = len(Path(current).relative_to(search_root).parts)
        directories[:] = sorted(name for name in directories if depth < 8 and not (Path(current) / name).is_symlink())
        candidates.extend(Path(current) / name for name in sorted(files) if name.lower().endswith(".zip"))
        if len(candidates) > 10000:
            raise RuntimeError("candidate count limit exceeded")

accepted = []
for candidate in candidates:
    if _sha256_file(candidate) != EXPECTED_IDENTITY["expected_input_zip_sha256"]:
        continue
    with zipfile.ZipFile(candidate) as archive:
        infos = archive.infolist()
        if len(infos) > 200000 or sum(info.file_size for info in infos) > 20 * 1024**3:
            raise RuntimeError("archive resource limit exceeded")
        names = [_safe_name(info.filename) for info in infos if not info.is_dir()]
        if len(names) != len(set(name.casefold() for name in names)):
            raise RuntimeError("duplicate or case-colliding member")
        for info in infos:
            mode = (info.external_attr >> 16) & 0o177777
            if stat.S_IFMT(mode) == stat.S_IFLNK:
                raise RuntimeError("symlink member rejected")
        manifest = json.loads(archive.read("package_manifest.json"))
        rows = manifest.get("inventory")
        if manifest.get("lane") != LANE or manifest.get("claim_allowed") is not False or not isinstance(rows, list):
            raise RuntimeError("package manifest identity rejected")
        declared = {{row["path"]: row for row in rows}}
        if set(names) != set(declared) | {{"package_manifest.json"}}:
            raise RuntimeError("exact archive membership mismatch")
        for name, row in declared.items():
            data = archive.read(name)
            if row.get("bytes") != len(data) or row.get("sha256") != hashlib.sha256(data).hexdigest():
                raise RuntimeError("archive inventory hash mismatch")
    accepted.append(candidate)
if len(accepted) != 1:
    raise RuntimeError(f"expected exactly one authenticated input, found {{len(accepted)}}")

destination = Path("/kaggle/working") / f"certgen-authenticated-{{LANE}}"
if destination.exists():
    shutil.rmtree(destination)
partial = Path(tempfile.mkdtemp(prefix=f".certgen-{{LANE}}-", dir="/kaggle/working"))
try:
    with zipfile.ZipFile(accepted[0]) as archive:
        archive.extractall(partial)
    os.replace(partial, destination)
except Exception:
    shutil.rmtree(partial, ignore_errors=True)
    raise
INPUT_ROOT = destination
sys.path.insert(0, str(INPUT_ROOT / "source"))
# Authenticated package imports are permitted only in the next cell.
'''


def build_notebook(notebook_id: str) -> dict[str, Any]:
    spec = NOTEBOOKS[notebook_id]
    runtime = f'''# Identity-bound dependency lifecycle, then runtime/GPU/disk gates
import shutil
from certgen.icml2027.dependency_lifecycle import dependency_mode_from_environment, ensure_dependency_lifecycle
from certgen.icml2027.notebook_runtime import run_authenticated_lane, validate_output_zip
WORK_ROOT = Path("/kaggle/working/certgen-icml2027")
DEPENDENCY_PROFILE = INPUT_ROOT / "contract/dependency_profiles.json"
DEPENDENCY_REPORT = None
if DEPENDENCY_PROFILE.is_file():
    DEPENDENCY_REPORT = ensure_dependency_lifecycle(
        lane=LANE,
        input_zip_sha256=EXPECTED_IDENTITY["expected_input_zip_sha256"],
        source_tree_sha256=manifest["source_tree_sha256"],
        profile_path=DEPENDENCY_PROFILE,
        marker_path=WORK_ROOT / LANE / "dependency_restart_marker.json",
        report_path=WORK_ROOT / LANE / "dependency_verification.json",
        mode=dependency_mode_from_environment(),
        wheelhouse=os.environ.get("CERTGEN_AUTHENTICATED_WHEELHOUSE"),
    )
    if DEPENDENCY_REPORT["restart_required"]:
        raise RuntimeError("exact dependencies installed and identity-bound marker written; restart the runtime and rerun all cells")
    os.environ["CERTGEN_DEPENDENCY_REPORT"] = str(WORK_ROOT / LANE / "dependency_verification.json")
os.environ["CERTGEN_AUTHENTICATED_INPUT_ZIP_SHA256"] = EXPECTED_IDENTITY["expected_input_zip_sha256"]
import torch
if torch.cuda.device_count() != 2:
    raise RuntimeError(f"exactly two visible GPUs required, found {{torch.cuda.device_count()}}")
if shutil.disk_usage("/kaggle/working").free < 10 * 1024**3:
    raise RuntimeError("disk guard: fewer than 10 GiB free")
LANE_STATUS = {LANE_STATUS[notebook_id]!r}
'''
    execution = '''# Invoke the source-controlled worker; validate the closed output ZIP.
RESULT = run_authenticated_lane(LANE, INPUT_ROOT, WORK_ROOT, fixture_mode=False)
if RESULT.get("output_index"):
    from certgen.icml2027.payload import validate_multipart_payload
    OUTPUT_VALIDATION = validate_multipart_payload(RESULT["output_index"])
else:
    OUTPUT_VALIDATION = validate_output_zip(RESULT["output_zip"], expected_lane=LANE)
assert OUTPUT_VALIDATION["passed"]
print(json.dumps({"lane": LANE, "lane_status": LANE_STATUS, "output": OUTPUT_VALIDATION, "claim_allowed": False}, indent=2, sort_keys=True))
'''
    return {
        "cells": [
            {"cell_type": "markdown", "metadata": {}, "source": _source(
                f"# CertGen ICML 2027 — {notebook_id}\n\nStatus: `{LANE_STATUS[notebook_id]}`. `claim_allowed=false`."
            )},
            {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": _source(_bootstrap_code(notebook_id))},
            {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": _source(runtime)},
            {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": _source(execution)},
        ],
        "metadata": {
            "accelerator": "GPU",
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.11"},
            "certgen": {
                "notebook_id": notebook_id,
                "stage": spec["stage"],
                "lane_status": LANE_STATUS[notebook_id],
                "gpu_count": 2,
                "claim_allowed": False,
            },
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
        rows.append({
            "notebook_id": notebook_id,
            "path": str(path),
            "sha256": stable_hash(payload),
            "lane_status": LANE_STATUS[notebook_id],
            "claim_allowed": False,
        })
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
            first_code = next(cell for cell in actual["cells"] if cell.get("cell_type") == "code")
            first_text = "".join(first_code.get("source", []))
            if "from certgen" in first_text or "import certgen" in first_text:
                errors.append("project import appears before the authentication boundary")
            for token in (
                "STDLIB-ONLY PRE-IMPORT AUTHENTICATION BOUNDARY",
                "expected_input_zip_sha256",
                "exact archive membership mismatch",
                "run_authenticated_lane",
                "ensure_dependency_lifecycle",
                "source_tree_sha256",
                "dependency_restart_marker.json",
                "torch.cuda.device_count() != 2",
                "validate_output_zip",
            ):
                if token not in "\n".join("".join(cell.get("source", [])) for cell in actual["cells"]):
                    errors.append(f"required notebook contract token missing: {token}")
        results.append({"notebook_id": notebook_id, "path": str(path), "passed": not errors, "errors": errors})
    return {"passed": all(row["passed"] for row in results), "results": results, "claim_allowed": False}
