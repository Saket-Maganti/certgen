"""Deterministic factory for five production-hardened CVPR Kaggle notebooks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


NOTEBOOK_SPECS = {
    "notebooks/kaggle/certgen_cvpr_checkpoint_preflight_t4x2.ipynb": ("preflight", "preflight", False),
    "notebooks/kaggle/certgen_cvpr_cifar10_generation_t4x2_1k.ipynb": ("generation", "1k", False),
    "notebooks/kaggle/certgen_cvpr_generation_t4x2_generic.ipynb": ("generation", "config-driven", True),
    "notebooks/kaggle/certgen_cvpr_feature_extraction_t4x2_1k.ipynb": ("features", "1k", False),
    "notebooks/kaggle/certgen_cvpr_feature_extraction_t4x2_generic.ipynb": ("features", "config-driven", True),
}


def _cell(cell_type: str, source: str, stage: str) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "cell_type": cell_type,
        "metadata": {"tags": [f"certgen:{stage}"]},
        "source": [line + "\n" for line in source.strip().splitlines()],
    }
    if cell_type == "code":
        payload.update({"execution_count": None, "outputs": []})
    return payload


def _worker_spec_code(kind: str) -> str:
    if kind == "preflight":
        return '''
specs = []
for index, asset in enumerate(CONFIG["assets"]):
    gpu = index % GPU_COUNT
    cache_root = RUN_ROOT / "model_cache" / asset["asset_id"]
    if asset["asset_kind"] == "model":
        model_id = asset["model_or_extractor_id"]
        shard_id = f"model__{model_id}"
        worker_out = RUN_ROOT / "per_model" / model_id
        specs.append(WorkerSpec(
            worker_id=shard_id, module="certgen.notebooks.workers.preflight_worker",
            physical_gpu=gpu, shard_id=shard_id,
            args=("--config", str(INPUT_ROOT / "configuration.yaml"), "--asset-id", asset["asset_id"],
                  "--shard-id", shard_id, "--cache-root", str(cache_root), "--out", str(worker_out)),
            completion_marker=str(worker_out / "worker_completion.json"),
            configuration_hash=CONFIG["configuration_hash"], input_manifest_hash=CONFIG["input_manifest_hash"],
        ))
    else:
        extractor_id = asset["model_or_extractor_id"]
        asset_shard = f"extractor_asset__{extractor_id}"
        asset_out = RUN_ROOT / "per_asset" / extractor_id
        specs.append(WorkerSpec(
            worker_id=asset_shard, module="certgen.notebooks.workers.preflight_worker",
            physical_gpu=gpu, shard_id=asset_shard,
            args=("--config", str(INPUT_ROOT / "configuration.yaml"), "--asset-id", asset["asset_id"],
                  "--shard-id", asset_shard, "--cache-root", str(cache_root), "--out", str(asset_out), "--asset-only"),
            completion_marker=str(asset_out / "worker_completion.json"),
            configuration_hash=CONFIG["configuration_hash"], input_manifest_hash=CONFIG["input_manifest_hash"],
        ))
        extractor_shard = f"extractor__{extractor_id}"
        extractor_out = RUN_ROOT / "per_extractor" / extractor_id
        specs.append(WorkerSpec(
            worker_id=extractor_shard, module="certgen.notebooks.workers.extractor_preflight_worker",
            physical_gpu=gpu, shard_id=extractor_shard,
            args=("--config", str(INPUT_ROOT / "configuration.yaml"), "--extractor-id", extractor_id,
                  "--shard-id", extractor_shard, "--asset-manifest", str(asset_out / "asset_manifest.json"),
                  "--cache-root", str(cache_root), "--out", str(extractor_out)),
            completion_marker=str(extractor_out / "worker_completion.json"),
            configuration_hash=CONFIG["configuration_hash"], input_manifest_hash=CONFIG["input_manifest_hash"],
        ))
'''
    if kind == "generation":
        return '''
specs = []
for model in CONFIG["models"]:
    for index, _seeds in enumerate(CONFIG["seed_shards"][model["model_id"]]):
        shard_id = f"shard_{index:04d}"
        worker_id = f"{model['model_id']}__{shard_id}"
        worker_out = RUN_ROOT / "per_model" / model["model_id"] / "per_shard" / shard_id
        args = ("--config", str(INPUT_ROOT / "configuration.yaml"), "--model-id", model["model_id"],
                "--shard-id", shard_id, "--asset-manifest", str(INPUT_ROOT / "asset_manifests" / f"{model['model_id']}.json"),
                "--cache-root", str(INPUT_ROOT / "model_cache" / model["model_id"]), "--out", str(worker_out))
        if MODE == "resume": args += ("--resume",)
        specs.append(WorkerSpec(worker_id=worker_id, module="certgen.notebooks.workers.generation_worker",
                                physical_gpu=index % GPU_COUNT, shard_id=worker_id, args=args,
                                completion_marker=str(worker_out / "worker_completion.json"),
                                configuration_hash=CONFIG["configuration_hash"], input_manifest_hash=CONFIG["reference_manifest_hash"],
                                asset_manifest_hash=hashlib.sha256((INPUT_ROOT / "asset_manifests" / f"{model['model_id']}.json").read_bytes()).hexdigest()))
'''
    return '''
specs = []
for extractor_index, extractor in enumerate(CONFIG["extractors"]):
    for shard in CONFIG["image_shards"]:
        shard_id = str(shard["shard_id"])
        worker_id = f"{extractor['feature_space_id']}__{shard_id}"
        worker_out = RUN_ROOT / "shards" / extractor["feature_space_id"] / shard_id
        specs.append(WorkerSpec(
            worker_id=worker_id, module="certgen.notebooks.workers.feature_worker",
            physical_gpu=(extractor_index + len(specs)) % GPU_COUNT, shard_id=worker_id,
            args=("--config", str(INPUT_ROOT / "configuration.yaml"), "--extractor-id", extractor["feature_space_id"],
                  "--shard-id", shard_id, "--asset-manifest", str(INPUT_ROOT / "asset_manifests" / f"{extractor['feature_space_id']}.json"),
                  "--cache-root", str(INPUT_ROOT / "model_cache" / extractor["feature_space_id"]),
                  "--image-manifest", str(INPUT_ROOT / "image_shards" / f"{shard_id}.jsonl"),
                  "--image-root", str(RESOLVED_IMAGE_ROOT), "--out", str(worker_out)),
            completion_marker=str(worker_out / "worker_completion.json"),
            configuration_hash=CONFIG["configuration_hash"],
            input_manifest_hash=hashlib.sha256((INPUT_ROOT / "image_shards" / f"{shard_id}.jsonl").read_bytes()).hexdigest(),
            asset_manifest_hash=hashlib.sha256((INPUT_ROOT / "asset_manifests" / f"{extractor['feature_space_id']}.json").read_bytes()).hexdigest(),
        ))
'''


def input_discovery_code(kind: str) -> str:
    """Return the stdlib bootstrap followed by canonical content discovery."""

    package_type = f"{kind.upper()}_INPUT"
    return f'''
from __future__ import annotations
import json, os, subprocess, sys, zipfile
from pathlib import Path, PurePosixPath

SEARCH_ROOTS = [Path(value) for value in os.environ.get("CERTGEN_SEARCH_ROOTS", "/kaggle/input:/kaggle/working").split(os.pathsep) if value]

def _bootstrap_certgen_discovery():
    sources = []
    candidate_count = 0
    for search_root in SEARCH_ROOTS:
        if not search_root.exists() or search_root.is_symlink():
            continue
        for current, directories, filenames in os.walk(search_root, topdown=True, followlinks=False):
            current_path = Path(current)
            depth = len(current_path.relative_to(search_root).parts)
            directories[:] = sorted(
                name for name in directories
                if depth < 12 and name not in {{".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}}
                and not (current_path / name).is_symlink()
            )
            if "package_identity.json" in filenames and not (current_path / ".certgen_runtime_location.json").exists():
                candidate_count += 1
                identity = json.loads((current_path / "package_identity.json").read_text(encoding="utf-8"))
                if identity.get("package_type") == "{package_type}" and identity.get("stage") == "{kind}" and (current_path / "certgen/discovery/__init__.py").is_file():
                    sources.append(current_path)
            for filename in sorted(filenames):
                path = current_path / filename
                if path.suffix.casefold() != ".zip" or path.is_symlink():
                    continue
                candidate_count += 1
                with zipfile.ZipFile(path) as archive:
                    infos = archive.infolist()
                    names, seen, total = set(), set(), 0
                    safe = len(infos) <= 200000
                    for info in infos:
                        member = PurePosixPath(info.filename)
                        key = member.as_posix().casefold()
                        mode = (info.external_attr >> 16) & 0o170000
                        safe = safe and not member.is_absolute() and ".." not in member.parts and "\\\\" not in info.filename and key not in seen and mode != 0o120000
                        seen.add(key); names.add(info.filename); total += info.file_size
                    safe = safe and total <= 20 * 1024**3
                    if safe and {{"package_identity.json", "certgen/discovery/__init__.py"}}.issubset(names):
                        identity = json.loads(archive.read("package_identity.json"))
                        if identity.get("package_type") == "{package_type}" and identity.get("stage") == "{kind}":
                            sources.append(path)
                if candidate_count > 10000:
                    raise RuntimeError("bootstrap discovery candidate-count limit exceeded")
    unique = sorted({{str(path.resolve()) for path in sources}})
    if len(unique) != 1:
        raise RuntimeError(f"bootstrap discovery expected one {package_type}; found {{len(unique)}} matching sources: {{unique}}")
    sys.path.insert(0, unique[0])

try:
    import certgen.discovery
except ImportError:
    _bootstrap_certgen_discovery()

from certgen.notebooks.kaggle_io import load_frozen_configuration, safe_extract_one_input_package, verify_input_integrity
INPUT_ROOT = safe_extract_one_input_package(
    search_roots=SEARCH_ROOTS,
    destination="/kaggle/working/certgen-input-{kind}",
    expected_stage="{kind}",
    expected_package_type="{package_type}",
)
verify_input_integrity(INPUT_ROOT)
CONFIG = load_frozen_configuration(INPUT_ROOT)
WORK_ROOT = Path("/kaggle/working/certgen-cvpr")
'''


def build_notebook(kind: str, *, scale: str = "1k", generic: bool = False) -> dict[str, Any]:
    if kind not in {"preflight", "generation", "features"}:
        raise ValueError("kind must be preflight, generation, or features")
    title = {
        "preflight": "CertGen CVPR Checkpoint Preflight — Kaggle T4x2",
        "generation": f"CertGen CVPR {'Generic ' if generic else 'CIFAR-10 '}Generation {scale} — Kaggle T4x2",
        "features": f"CertGen CVPR {'Generic ' if generic else 'CIFAR-10 '}Feature Extraction {scale} — Kaggle T4x2",
    }[kind]
    evidence = "non_evidence_preflight" if kind == "preflight" else "run_log_only"
    status_code = {
        "preflight": "PREFLIGHT_PASS",
        "generation": "GENERATION_COMPLETE",
        "features": "FEATURE_EXTRACTION_SHARDS_COMPLETE",
    }[kind]
    cells = [
        _cell("markdown", f'''# {title}

`{evidence}` · `not_empirical_evidence` · `not paper evidence` · `claim_allowed=false`

Production-hardened, static-validation passed, fixture-runtime passed; real Kaggle preflight is still required. The run contract is hash-bound and supports `resume`, `restart`, and `force_new_run`. GPU work occurs only in isolated subprocess workers.''', "title"),
        _cell("code", input_discovery_code(kind), "input-discovery"),
        _cell("code", f'''
from certgen.notebooks.environment_bootstrap import bootstrap_environment
ENVIRONMENT = bootstrap_environment(
    "kaggle_t4x2_{'preflight' if kind == 'preflight' else ('generation' if kind == 'generation' else 'features')}",
    output_dir=WORK_ROOT / "environment", network_allowed=bool(CONFIG["dependency_network_allowed"]), apply=True,
    revalidate_after_restart=bool(os.environ.get("CERTGEN_POST_RESTART")),
    search_roots=SEARCH_ROOTS,
    lock_path=INPUT_ROOT / "requirements/stage.lock",
    constraints_path=INPUT_ROOT / "requirements/kaggle-constraints.txt",
)
if ENVIRONMENT["status"] != "ENVIRONMENT_COMPATIBLE":
    raise RuntimeError(ENVIRONMENT["restart_instruction"] or "environment incompatible")
''', "environment-bootstrap"),
        _cell("code", '''
MODE = CONFIG["mode"]
if MODE not in {"resume", "restart", "force_new_run"}:
    raise ValueError("mode must be resume, restart, or force_new_run")
''', "input-hash-config-validation"),
        _cell("code", '''
from certgen.notebooks.model_assets import AssetPolicy
from certgen.notebooks.network_policy import network_policy_from_config
ASSET_POLICY = AssetPolicy(CONFIG["asset_policy"])
NETWORK_POLICY = network_policy_from_config(CONFIG)
if ASSET_POLICY is AssetPolicy.ONLINE_PREFLIGHT_DOWNLOAD and not NETWORK_POLICY.model_asset_network_allowed:
    raise RuntimeError("online preflight asset policy requires model asset network")
if CONFIG["kind"] != "preflight" and NETWORK_POLICY.model_asset_network_allowed:
    raise RuntimeError("model asset downloads are confined to checkpoint/extractor preflight")
''', "network-cache-policy"),
        *(
            [
                _cell(
                    "code",
                    '''
from certgen.notebooks.kaggle_io import validate_feature_input_images
IMAGE_INPUT_VALIDATION = validate_feature_input_images(INPUT_ROOT, CONFIG, search_roots=SEARCH_ROOTS)
RESOLVED_IMAGE_ROOT = Path(IMAGE_INPUT_VALIDATION["resolved_image_root"])
print(json.dumps(IMAGE_INPUT_VALIDATION, indent=2, sort_keys=True))
''',
                    "all-image-paths-before-gpu",
                )
            ]
            if kind == "features"
            else []
        ),
        _cell("code", '''
from certgen.notebooks.kaggle_io import disk_guard
DISK = disk_guard("/kaggle/working", int(CONFIG.get("required_disk_bytes", 8 * 1024**3)))
''', "disk-check"),
        _cell("code", '''
# Parent visibility check deliberately uses nvidia-smi and never imports or initializes PyTorch.
probe = subprocess.run(["nvidia-smi", "-L"], check=True, capture_output=True, text=True)
GPU_LINES = [line for line in probe.stdout.splitlines() if line.strip().startswith("GPU ")]
GPU_COUNT = len(GPU_LINES)
requested = int(CONFIG.get("requested_gpu_count", 2))
if GPU_COUNT < requested and not (GPU_COUNT == 1 and CONFIG.get("allow_single_gpu_fallback") is True):
    raise RuntimeError(f"requested {requested} GPUs but nvidia-smi reported {GPU_COUNT}")
''', "gpu-visibility-parent-no-cuda"),
        _cell("code", '''
from certgen.notebooks.run_state import RunIdentity, prepare_run_directory
IDENTITY = RunIdentity(CONFIG["run_id"], CONFIG["configuration_hash"],
                       str(CONFIG.get("source_manifest_hash", CONFIG.get("reference_manifest_hash", "preflight_none"))),
                       str(CONFIG.get("asset_manifest_hash", "preflight_to_be_generated")))
RUN_STATE = prepare_run_directory(WORK_ROOT, IDENTITY, MODE)
RUN_ROOT = Path(RUN_STATE["run_dir"])
frozen_config_copy = RUN_ROOT / "configuration.yaml"
if frozen_config_copy.exists():
    if hashlib.sha256(frozen_config_copy.read_bytes()).hexdigest() != hashlib.sha256((INPUT_ROOT / "configuration.yaml").read_bytes()).hexdigest():
        raise ValueError("run-root frozen configuration differs from the uploaded configuration")
else:
    shutil.copy2(INPUT_ROOT / "configuration.yaml", frozen_config_copy)
''', "resume-restart-force"),
        _cell("code", '''
from certgen.notebooks.subprocess_orchestrator import WorkerSpec
'''+_worker_spec_code(kind)+'''
from certgen.notebooks.kaggle_io import assert_unique_shards
assert_unique_shards([{"shard_id": spec.shard_id} for spec in specs])
''', "worker-script-preparation"),
        _cell("code", '''
from certgen.notebooks.subprocess_orchestrator import run_workers
ORCHESTRATION = run_workers(specs, output_dir=RUN_ROOT / "orchestration", timeout_seconds=CONFIG.get("worker_timeout_seconds"), resume=MODE == "resume")
''', "subprocess-launch"),
        _cell("code", '''
FAILED = [row for row in ORCHESTRATION["workers"] if row["status"] not in {"COMPLETE", "REUSED_VALID_COMPLETION"}]
for row in ORCHESTRATION["workers"]:
    print(row["worker_id"], row["status"], row.get("log"), row.get("rerun_command"))
if FAILED:
    raise RuntimeError("BLOCKED_PARTIAL_FAILURE; preserve completed shards and use the emitted rerun commands")
''', "per-worker-monitoring"),
        _cell("code", f'''
from certgen.cvpr.contracts import atomic_write_json
from certgen.notebooks.kaggle_io import all_worker_statuses_complete
if not all_worker_statuses_complete(ORCHESTRATION):
    raise RuntimeError("shard validation failed")
ROOT_STATUS = {{"status_code": "{status_code}", "passed": True, "configuration_hash": CONFIG["configuration_hash"],
                "mode": MODE, "expected_workers": sorted(spec.worker_id for spec in specs),
                "completed_workers": sorted(row["worker_id"] for row in ORCHESTRATION["workers"]),
                "output_schema_version": CONFIG["output_schema_version"],
                "evidence_class": "{evidence}", "claim_allowed": False}}
atomic_write_json(ROOT_STATUS, RUN_ROOT / "status.json")
if CONFIG["kind"] == "preflight":
    ROOT_STATUS["results"] = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(RUN_ROOT.glob("per_model/*/status.json"))]
    ROOT_STATUS["extractor_results"] = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(RUN_ROOT.glob("per_extractor/*/status.json"))]
    atomic_write_json(ROOT_STATUS, RUN_ROOT / "checkpoint_preflight_status.json")
elif CONFIG["kind"] == "generation":
    atomic_write_json(ROOT_STATUS, RUN_ROOT / "generation_status.json")
else:
    atomic_write_json(ROOT_STATUS, RUN_ROOT / "feature_extraction_status.json")
''', "shard-validation"),
        _cell("code", '''
# Deterministic merge is sample-ID based inside each worker and orchestration status is sorted by worker ID.
MERGE_INDEX = sorted((row["worker_id"], row["shard_id"]) for row in ORCHESTRATION["workers"])
atomic_write_json({"workers": MERGE_INDEX, "configuration_hash": CONFIG["configuration_hash"], "claim_allowed": False}, RUN_ROOT / "merge_index.json")
''', "deterministic-merge"),
        _cell("code", '''
from certgen.notebooks.kaggle_io import write_integrity_manifest
INTEGRITY = write_integrity_manifest(RUN_ROOT)
''', "integrity-manifest"),
        _cell("code", f'''
from certgen.notebooks.kaggle_io import copyback_instructions
from certgen.notebooks.final_zip import finalize_output_zip
ZIP_PATH = Path("/kaggle/working") / f"certgen_cvpr_{kind}_{{CONFIG['run_id']}}.zip"
(RUN_ROOT / "copyback_instructions.md").write_text(copyback_instructions("{kind}", ZIP_PATH), encoding="utf-8")
write_integrity_manifest(RUN_ROOT)
ZIP = finalize_output_zip(RUN_ROOT, ZIP_PATH, mode=MODE, configuration_hash=CONFIG["configuration_hash"],
                          asset_manifest_hash=str(CONFIG.get("asset_manifest_hash", "preflight_generated")))
''', "deterministic-output-zip"),
        _cell("markdown", f'''## Copy-back and local import

Copy the final ZIP without unpacking it; renaming is allowed. Preserve its hash and run either:

`python3 -m certgen import {'features' if kind == 'features' else kind} <copied-back-zip>`

or `python3 scripts/run_all_available_cpu_stages.py --resume --explain --search-root /path/to/downloads` for recursive content-based resume.

{'Then run `python3 -m certgen merge features --run <run_id>` locally and validate every cache-v2 sidecar.' if kind == 'features' else ''}

On failure, preserve completed shards/logs and run only each exact `rerun_command` emitted in the monitoring cell. Changed input, config, or asset hashes require `restart` or `force_new_run`; never reuse incompatible markers.''', "copyback-recovery"),
        _cell("code", f'''
FINAL_STATUS = {{"status": "RUN_READY_BY_LOCAL_CONTRACT_REAL_KAGGLE_EXECUTION_REQUIRED",
                "output_zip": ZIP, "evidence_class": "{evidence}", "claim_allowed": False}}
print(json.dumps(FINAL_STATUS, indent=2, sort_keys=True))
''', "final-status"),
    ]
    return {
        "cells": cells,
        "metadata": {
            "accelerator": "GPU",
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.11"},
            "certgen": {
                "generated_by": "certgen.notebooks.cvpr_factory.v2",
                "kind": kind,
                "scale": scale,
                "generic": generic,
                "runtime_architecture": "isolated_subprocess_workers",
                "claim_allowed": False,
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def write_canonical_notebooks(root: str | Path = ".", *, replace_generated: bool = False) -> list[str]:
    base = Path(root)
    written: list[str] = []
    for relative, (kind, scale, generic) in NOTEBOOK_SPECS.items():
        path = base / relative
        payload = build_notebook(kind, scale=scale, generic=generic)
        serialized = json.dumps(payload, indent=1, sort_keys=True) + "\n"
        if path.exists() and path.read_text(encoding="utf-8") != serialized:
            current = json.loads(path.read_text(encoding="utf-8"))
            marker = (current.get("metadata") or {}).get("certgen") or {}
            if not replace_generated or marker.get("kind") != kind:
                raise FileExistsError(f"refusing to overwrite changed notebook: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(serialized, encoding="utf-8")
        written.append(str(path))
    return written


if __name__ == "__main__":  # pragma: no cover
    print("\n".join(write_canonical_notebooks(replace_generated=True)))
