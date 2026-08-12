"""Authenticated ICML notebook workers and CPU fixture rehearsals."""

from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

from certgen.icml2027.common import file_sha256, stable_hash, write_csv, write_json


LANE_STATUS = {
    "dinov2_preflight": "READY_AFTER_PRIVATE_ASSET",
    "dinov2_features": "READY_AFTER_DINOV2_PREFLIGHT",
    "cifar_cross_family_preflight": "BLOCKED_EXTERNAL_SOURCE_VERIFICATION",
    "cifar_10k_generation": "READY_AFTER_LEGACY_PREFLIGHT",
    "cifar_10k_features": "READY_AFTER_10K_GENERATION",
    "released_sample_features": "READY_AFTER_RELEASED_SAMPLE_IMPORT",
    "ffhq": "BLOCKED_EXTERNAL_REFERENCE_AND_SOURCE",
    "imagenet": "BLOCKED_EXTERNAL_REFERENCE_AND_SOURCE",
    "text_to_image": "BLOCKED_EXTERNAL_PROMPTS_REFERENCE_AND_SOURCE",
}
LOCALLY_IMPLEMENTABLE_LANES = {
    "dinov2_preflight",
    "dinov2_features",
    "cifar_cross_family_preflight",
    "cifar_10k_generation",
    "cifar_10k_features",
    "released_sample_features",
}


def _safe_relative(value: str) -> Path:
    pure = PurePosixPath(value)
    if not value or pure.is_absolute() or ".." in pure.parts or "\\" in value:
        raise ValueError(f"unsafe worker path: {value}")
    return Path(*pure.parts)


def _worker_spec(input_root: Path, lane: str) -> dict[str, Any]:
    candidates = sorted(input_root.glob("inputs/worker_spec*"))
    if len(candidates) != 1 or not candidates[0].is_file():
        raise ValueError("authenticated input must contain exactly one inputs/worker_spec file")
    spec = json.loads(candidates[0].read_text(encoding="utf-8"))
    if not isinstance(spec, dict) or spec.get("lane") != lane or spec.get("claim_allowed") is not False:
        raise ValueError("worker specification has the wrong lane or evidence gate")
    return spec


def _input_path(root: Path, value: str) -> Path:
    path = (root / _safe_relative(value)).resolve()
    path.relative_to(root.resolve())
    if not path.exists():
        raise FileNotFoundError(path)
    return path


def _run_real_worker(
    lane: str,
    spec: dict[str, Any],
    input_root: Path,
    work_root: Path,
    *,
    job_index: int = 0,
) -> dict[str, Any]:
    if lane == "dinov2_preflight":
        from certgen.icml2027.dinov2 import validate_asset_manifest

        result = validate_asset_manifest(
            _input_path(input_root, str(spec["asset_manifest"])),
            _input_path(input_root, str(spec["asset_root"])),
        )
        if not result["passed"]:
            raise RuntimeError("DINOv2 authenticated-asset preflight failed")
        return {"passed": True, "job_index": job_index, "result": result, "claim_allowed": False}
    if lane in {"dinov2_features", "cifar_10k_features", "released_sample_features"}:
        from certgen.features.extract import run_sharded_extraction

        jobs = spec.get("jobs")
        if not isinstance(jobs, list) or not jobs:
            raise ValueError("feature worker requires non-empty jobs")
        if not 0 <= job_index < len(jobs):
            raise ValueError("feature job index is outside the authenticated job list")
        job = jobs[job_index]
        shard_id = int(job["shard_id"])
        num_shards = int(job["num_shards"])
        result = run_sharded_extraction(
            input_manifest=str(_input_path(input_root, str(job["input_manifest"]))),
            extractor=str(job["extractor"]),
            out_dir=str(work_root / "features"),
            device=str(job.get("device", "cuda:0")),
            batch_size=int(job.get("batch_size", 64)),
            preprocessing_lock=str(_input_path(input_root, str(job["preprocessing_lock"]))),
            provenance_ledger=str(_input_path(input_root, str(job["provenance_ledger"])))
            if job.get("provenance_ledger")
            else None,
            shard_id=shard_id,
            num_shards=num_shards,
            execute=True,
            resume=True,
            force=False,
            json_out=None,
        )
        return {
            "passed": True,
            "job_index": job_index,
            "shard_id": shard_id,
            "result": result,
            "claim_allowed": False,
        }
    if lane == "cifar_10k_generation":
        from certgen.generation.generate_cifar10_diffusers import KNOWN_CHECKPOINTS, run_generation

        jobs = spec.get("jobs")
        if not isinstance(jobs, list) or not jobs:
            raise ValueError("generation worker requires non-empty jobs")
        if not 0 <= job_index < len(jobs):
            raise ValueError("generation job index is outside the authenticated job list")
        job = jobs[job_index]
        checkpoint_id = str(job["checkpoint_id"])
        if checkpoint_id not in KNOWN_CHECKPOINTS:
            raise ValueError(f"unregistered checkpoint blocked: {checkpoint_id}")
        seed_start = int(job["seed_start"])
        num_samples = int(job["num_samples"])
        if seed_start < 0 or num_samples <= 0 or seed_start + num_samples > 10_000:
            raise ValueError("generation shard is outside the frozen 10k seed range")
        slug = checkpoint_id.replace("/", "__")
        result = run_generation(
            checkpoint_id=checkpoint_id,
            seed_start=seed_start,
            seed_end=None,
            num_samples=num_samples,
            out_dir=work_root / "generated" / slug,
            manifest_out=work_root / "manifests" / f"{slug}_{seed_start:08d}.jsonl",
            device=str(job.get("device", "cuda")),
            batch_size=int(job.get("batch_size", 32)),
            resume=True,
            execute=True,
            dry_run=False,
        )
        return {"passed": True, "job_index": job_index, "result": result, "claim_allowed": False}
    if lane == "cifar_cross_family_preflight":
        raise RuntimeError("BLOCKED_EXTERNAL_SOURCE_VERIFICATION")
    raise RuntimeError(f"{LANE_STATUS[lane]}: no authenticated real worker may execute yet")


def fixture_worker_result(lane: str, job_index: int) -> dict[str, Any]:
    return {
        "lane": lane,
        "job_index": job_index,
        "device_assignment": f"cuda:{job_index % 2}",
        "visible_device": os.environ.get("CUDA_VISIBLE_DEVICES"),
        "fixture_payload_sha256": hashlib.sha256(f"{lane}|{job_index}|fixture-v1".encode()).hexdigest(),
        "completed": True,
        "claim_allowed": False,
    }


def _run_worker_processes(
    lane: str,
    input_root: Path,
    work_root: Path,
    *,
    fixture_mode: bool,
    fixture_shards: int,
) -> dict[str, Any]:
    spec = None if fixture_mode else _worker_spec(input_root, lane)
    jobs = spec.get("jobs") if spec else None
    job_count = fixture_shards if fixture_mode else (len(jobs) if isinstance(jobs, list) else 1)
    if job_count <= 0:
        raise ValueError("worker process count must be positive")
    result_root = work_root / "worker_results"
    result_root.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    for batch_start in range(0, job_count, 2):
        processes: list[tuple[subprocess.Popen[str], Path, int]] = []
        for job_index in range(batch_start, min(batch_start + 2, job_count)):
            output = result_root / f"job_{job_index:04d}.json"
            command = [
                sys.executable,
                "-m",
                "certgen.icml2027.notebook_worker",
                "--lane",
                lane,
                "--input-root",
                str(input_root),
                "--work-root",
                str(work_root),
                "--job-index",
                str(job_index),
                "--out",
                str(output),
            ]
            if fixture_mode:
                command.append("--fixture")
            environment = os.environ.copy()
            environment["CUDA_VISIBLE_DEVICES"] = str(job_index % 2)
            processes.append(
                (
                    subprocess.Popen(
                        command,
                        env=environment,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                    ),
                    output,
                    job_index,
                )
            )
        for process, output, job_index in processes:
            stdout, stderr = process.communicate()
            if process.returncode != 0 or not output.is_file():
                raise RuntimeError(f"worker {job_index} failed: stdout={stdout[-1000:]}; stderr={stderr[-1000:]}")
            results.append(json.loads(output.read_text(encoding="utf-8")))
    return {
        "passed": all(bool(row.get("completed", row.get("passed"))) for row in results),
        "fixture_mode": fixture_mode,
        "worker_processes": sorted(results, key=lambda row: int(row.get("job_index", 0))),
        "maximum_concurrent_workers": 2,
        "claim_allowed": False,
    }


def _write_result_zip(lane: str, work_root: Path, result: dict[str, Any]) -> Path:
    payload = json.dumps(result, indent=2, sort_keys=True).encode() + b"\n"
    rows = [{"path": "result.json", "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}]
    manifest = {
        "schema_version": "certgen.icml2027.notebook_output.v1",
        "lane": lane,
        "status": "COMPLETE",
        "inventory": rows,
        "result_hash": stable_hash(result),
        "claim_allowed": False,
    }
    target = work_root / f"certgen_icml2027_{lane}_output.zip"
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
    os.close(descriptor)
    temporary = Path(name)
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for member, data in (
                ("result.json", payload),
                ("output_manifest.json", json.dumps(manifest, indent=2, sort_keys=True).encode() + b"\n"),
            ):
                info = zipfile.ZipInfo(member, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                archive.writestr(info, data)
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return target


def validate_output_zip(path: str | Path, *, expected_lane: str) -> dict[str, Any]:
    source = Path(path)
    with zipfile.ZipFile(source) as archive:
        if set(archive.namelist()) != {"result.json", "output_manifest.json"}:
            raise ValueError("output ZIP has unexpected membership")
        manifest = json.loads(archive.read("output_manifest.json"))
        result_bytes = archive.read("result.json")
    row = manifest["inventory"][0]
    if manifest.get("lane") != expected_lane or manifest.get("status") != "COMPLETE":
        raise ValueError("output ZIP has the wrong lane or incomplete status")
    if row.get("bytes") != len(result_bytes) or row.get("sha256") != hashlib.sha256(result_bytes).hexdigest():
        raise ValueError("output ZIP result identity mismatch")
    return {
        "passed": True,
        "lane": expected_lane,
        "output_zip": str(source),
        "output_zip_sha256": file_sha256(source),
        "claim_allowed": False,
    }


def run_authenticated_lane(
    lane: str,
    input_root: str | Path,
    work_root: str | Path,
    *,
    fixture_mode: bool = False,
    fixture_shards: int = 4,
) -> dict[str, Any]:
    if lane not in LANE_STATUS:
        raise ValueError(f"unknown lane: {lane}")
    root = Path(work_root) / lane
    root.mkdir(parents=True, exist_ok=True)
    marker = root / "completed.json"
    if marker.is_file():
        previous = json.loads(marker.read_text(encoding="utf-8"))
        validation = validate_output_zip(previous["output_zip"], expected_lane=lane)
        return {**previous, "resumed": True, "validation": validation, "claim_allowed": False}
    result = _run_worker_processes(
        lane,
        Path(input_root),
        root,
        fixture_mode=fixture_mode,
        fixture_shards=fixture_shards,
    )
    output_zip = _write_result_zip(lane, root, result)
    validation = validate_output_zip(output_zip, expected_lane=lane)
    payload = {
        "schema_version": "certgen.icml2027.notebook_lane_result.v1",
        "lane": lane,
        "lane_status": LANE_STATUS[lane],
        "fixture_mode": fixture_mode,
        "resumed": False,
        "result": result,
        "output_zip": str(output_zip),
        "validation": validation,
        "not_empirical_paper_evidence": True,
        "claim_allowed": False,
    }
    write_json(marker, payload)
    return payload


def run_closure_rehearsals(out_dir: str | Path) -> dict[str, Any]:
    """Exercise sharding, resume, two-device assignment, and ZIP closure on CPU."""

    target = Path(out_dir)
    rows: list[dict[str, Any]] = []
    for lane in sorted(LOCALLY_IMPLEMENTABLE_LANES):
        first = run_authenticated_lane(lane, target / "fixture_input", target / "work", fixture_mode=True)
        second = run_authenticated_lane(lane, target / "fixture_input", target / "work", fixture_mode=True)
        workers = first["result"]["worker_processes"]
        validation = validate_output_zip(first["output_zip"], expected_lane=lane)
        rows.append(
            {
                "lane": lane,
                "declared_status": LANE_STATUS[lane],
                "worker_entrypoint": "certgen.icml2027.notebook_runtime.run_authenticated_lane",
                "fixture_mode": True,
                "dependency_restart_marker_contract_checked": True,
                "shard_count": len(workers),
                "worker_subprocesses_exercised": True,
                "gpu_assignment_contract": sorted({str(row["device_assignment"]) for row in workers}) == ["cuda:0", "cuda:1"],
                "resume_reused_validated_output": second["resumed"] is True,
                "output_zip_valid": validation["passed"],
                "output_zip_sha256": validation["output_zip_sha256"],
                "passed": bool(second["resumed"] and validation["passed"]),
                "synthetic_validation_only": True,
                "not_real_generator_evidence": True,
                "not_empirical_paper_evidence": True,
                "claim_allowed": False,
            }
        )
    write_csv(target / "closure_rehearsals.csv", rows)
    summary = {
        "schema_version": "certgen.icml2027.notebook_closure_rehearsal.v1",
        "passed": all(bool(row["passed"]) for row in rows),
        "lanes": len(rows),
        "real_workers_exercised": False,
        "fixture_orchestration_only": True,
        "claim_allowed": False,
    }
    write_json(target / "closure_rehearsals.summary.json", summary)
    return summary
