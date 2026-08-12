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
    "dinov2_preflight": "READY_AFTER_AUTHENTICATED_PREREQUISITE",
    "dinov2_features": "READY_AFTER_AUTHENTICATED_PREREQUISITE",
    "cifar_cross_family_preflight": "BLOCKED_EXTERNAL_SOURCE",
    "cifar_10k_generation": "READY_AFTER_AUTHENTICATED_PREREQUISITE",
    "cifar_10k_features": "READY_AFTER_AUTHENTICATED_PREREQUISITE",
    "released_sample_features": "READY_AFTER_AUTHENTICATED_PREREQUISITE",
    "ffhq": "BLOCKED_EXTERNAL_SOURCE",
    "imagenet": "BLOCKED_EXTERNAL_SOURCE",
    "text_to_image": "BLOCKED_EXTERNAL_SOURCE",
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
    contract_path = input_root / "contract" / "execution_contract.json"
    if lane in {"cifar_10k_generation", "cifar_10k_features"}:
        if not contract_path.is_file():
            raise ValueError("authenticated input is missing the execution contract")
        from certgen.icml2027.execution_contract import validate_worker_spec

        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        validation = validate_worker_spec(spec, expected_lane=lane, contract=contract)
        if not validation["passed"]:
            raise ValueError(f"worker scientific identity rejected: {validation['errors']}")
    else:
        from certgen.icml2027.execution_contract import validate_worker_spec

        validation = validate_worker_spec(spec, expected_lane=lane, contract=None)
        if not validation["passed"]:
            raise ValueError(f"worker scientific identity rejected: {validation['errors']}")
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
        extractor_id = str(job.get("extractor_id", job.get("extractor", "")))
        source_role = str(job.get("source_role", "unknown"))
        result = run_sharded_extraction(
            input_manifest=str(_input_path(input_root, str(job["input_manifest"]))),
            extractor=str(job["extractor"]),
            out_dir=str(work_root / "features" / extractor_id / source_role),
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
        from certgen.generation.generate_cifar10_diffusers import KNOWN_CHECKPOINTS, run_generation_samples

        jobs = spec.get("jobs")
        if not isinstance(jobs, list) or not jobs:
            raise ValueError("generation worker requires non-empty jobs")
        if not 0 <= job_index < len(jobs):
            raise ValueError("generation job index is outside the authenticated job list")
        job = jobs[job_index]
        checkpoint_id = str(job["checkpoint_id"])
        if checkpoint_id not in KNOWN_CHECKPOINTS:
            raise ValueError(f"unregistered checkpoint blocked: {checkpoint_id}")
        seed_start = int(job["sample_index_start"])
        seed_stop = int(job["sample_index_stop"])
        if seed_start < 0 or seed_stop <= seed_start or seed_stop > 10_000:
            raise ValueError("generation shard is outside the frozen 10k sample-index range")
        manifest_path = input_root / "contract" / "generator_seed_manifest.json"
        if not manifest_path.is_file():
            raise ValueError("authenticated generation input is missing the frozen generator seed manifest")
        seed_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        seed_records = [
            row
            for row in seed_manifest.get("records", [])
            if row.get("model_id") == job.get("model_id")
            and seed_start <= int(row.get("sample_index", -1)) < seed_stop
        ]
        if len(seed_records) != seed_stop - seed_start:
            raise ValueError("frozen generator-seed shard has missing or extra records")
        if stable_hash(seed_records) != job.get("seed_records_sha256"):
            raise ValueError("frozen generator-seed shard hash mismatch")
        slug = checkpoint_id.replace("/", "__")
        result = run_generation_samples(
            checkpoint_id=checkpoint_id,
            samples=seed_records,
            out_dir=work_root / "generated" / slug,
            manifest_out=work_root / "manifests" / f"{slug}_{seed_start:08d}.jsonl",
            device=str(job.get("device", "cuda")),
            batch_size=int(job.get("batch_size", 32)),
            resume=True,
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


def _output_identity(lane: str, input_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    package_manifest = json.loads((input_root / "package_manifest.json").read_text(encoding="utf-8"))
    spec = _worker_spec(input_root, lane)
    contract_path = input_root / "contract/execution_contract.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8")) if contract_path.is_file() else {}
    dependency_report_path = Path(os.environ.get("CERTGEN_DEPENDENCY_REPORT", ""))
    dependency_report = (
        json.loads(dependency_report_path.read_text(encoding="utf-8"))
        if str(dependency_report_path) and dependency_report_path.is_file()
        else {}
    )
    identity = {
        "input_package_sha256": os.environ.get(
            "CERTGEN_AUTHENTICATED_INPUT_ZIP_SHA256", str(spec["input_package_sha256"])
        ),
        "study_id": spec["study_id"],
        "study_hash": spec["study_hash"],
        "configuration_sha256": spec["configuration_sha256"],
        "worker_spec_sha256": stable_hash(spec),
        "source_tree_sha256": package_manifest["source_tree_sha256"],
        "dependency_lock_sha256": dependency_report.get("identity", {}).get(
            "dependency_lock_sha256", "0" * 64
        ),
        "model_revisions": spec["model_revisions"],
        "extractor_revisions": spec["extractor_revisions"],
        "preprocessing_hashes": spec["preprocessing_hashes"],
        "reference_plan_sha256": spec.get("reference_plan_sha256"),
        "seed_manifest_sha256": contract.get("seed_manifest_sha256"),
        "claim_allowed": False,
    }
    if lane == "dinov2_features":
        identity.update({"robustness_feature_space": True, "confirmatory_family": False})
    return identity, spec


def _write_scientific_payload(
    lane: str,
    input_root: Path,
    work_root: Path,
) -> Path:
    from certgen.icml2027.payload import build_multipart_payload, validate_multipart_payload

    identity, spec = _output_identity(lane, input_root)
    parts: list[dict[str, bytes]] = []
    records: list[dict[str, Any]] = []
    if lane == "cifar_10k_generation":
        for shard_id, manifest_path in enumerate(sorted((work_root / "manifests").glob("*.jsonl"))):
            member_map: dict[str, bytes] = {f"manifests/{manifest_path.name}": manifest_path.read_bytes()}
            for line in manifest_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                image = Path(str(row["image_path"]))
                image_member = f"images/{row['model_id'].replace('/', '__')}/{image.name}"
                image_bytes = image.read_bytes()
                member_map[image_member] = image_bytes
                records.append(
                    {
                        "sample_id": row["sample_id"],
                        "sample_index": row["sample_index"],
                        "model_id": next(
                            model_id
                            for model_id, values in spec["model_revisions"].items()
                            if values["checkpoint_id"] == row["checkpoint_id"]
                        ),
                        "checkpoint_id": row["checkpoint_id"],
                        "checkpoint_revision": row["checkpoint_revision"],
                        "generator_seed": row["seed"],
                        "image_path": image_member,
                        "image_sha256": hashlib.sha256(image_bytes).hexdigest(),
                        "shard_id": shard_id,
                        "claim_allowed": False,
                    }
                )
            parts.append(member_map)
        payload_type = "generation"
    else:
        import numpy as np

        for shard_id, feature_path in enumerate(sorted((work_root / "features").rglob("*.npz"))):
            relative = feature_path.relative_to(work_root / "features")
            extractor_id, source_role = relative.parts[:2]
            with np.load(feature_path, allow_pickle=False) as loaded:
                features = np.asarray(loaded["features"])
                sample_ids = [str(value) for value in np.asarray(loaded["sample_ids"]).tolist()]
            feature_member = f"features/{relative.as_posix()}"
            sidecar_member = f"sidecars/{relative.with_suffix('.json').as_posix()}"
            revision = spec["extractor_revisions"][extractor_id]
            preprocessing = spec["preprocessing_hashes"][extractor_id]
            sidecar = {
                "sample_ids": sample_ids,
                "extractor_id": extractor_id,
                "extractor_revision": revision,
                "preprocessing_sha256": preprocessing,
                "dimension": int(features.shape[1]),
                "dtype": str(features.dtype),
                "claim_allowed": False,
            }
            parts.append(
                {
                    feature_member: feature_path.read_bytes(),
                    sidecar_member: json.dumps(sidecar, sort_keys=True, separators=(",", ":")).encode(),
                }
            )
            records.append(
                {
                    "extractor_id": extractor_id,
                    "extractor_revision": revision,
                    "preprocessing_sha256": preprocessing,
                    "source_role": source_role,
                    "source_manifest_sha256": spec["source_manifest_hashes"][source_role],
                    "feature_path": feature_member,
                    "sidecar_path": sidecar_member,
                    "dimension": int(features.shape[1]),
                    "dtype": str(features.dtype),
                    "row_count": int(features.shape[0]),
                    "source_sample_ids_sha256": stable_hash(sample_ids),
                    "shard_id": shard_id,
                    "claim_allowed": False,
                }
            )
        payload_type = "features"
    if not parts:
        raise RuntimeError(f"{lane} produced no scientific payload shards")
    for result_path in sorted((work_root / "worker_results").glob("*.json")):
        parts[0][f"runtime/worker_results/{result_path.name}"] = result_path.read_bytes()
    dependency_path = Path(os.environ.get("CERTGEN_DEPENDENCY_REPORT", ""))
    if str(dependency_path) and dependency_path.is_file():
        parts[0]["provenance/dependency_verification.json"] = dependency_path.read_bytes()
    parts[0]["provenance/worker_spec.json"] = json.dumps(spec, indent=2, sort_keys=True).encode() + b"\n"
    parts[0]["provenance/scientific_identity.json"] = (
        json.dumps(identity, indent=2, sort_keys=True).encode() + b"\n"
    )
    built = build_multipart_payload(
        lane=lane,
        payload_type=payload_type,
        parts=parts,
        records=records,
        identity=identity,
        out_dir=work_root,
        basename=lane,
    )
    validation = validate_multipart_payload(built["index_path"], expected_type=payload_type)
    if not validation["passed"]:
        raise RuntimeError("scientific multipart payload validation failed")
    return Path(str(built["index_path"]))


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
        if previous.get("output_index"):
            from certgen.icml2027.payload import validate_multipart_payload

            validation = validate_multipart_payload(previous["output_index"])
        else:
            validation = validate_output_zip(previous["output_zip"], expected_lane=lane)
        return {**previous, "resumed": True, "validation": validation, "claim_allowed": False}
    result = _run_worker_processes(
        lane,
        Path(input_root),
        root,
        fixture_mode=fixture_mode,
        fixture_shards=fixture_shards,
    )
    output_zip: Path | None = None
    output_index: Path | None = None
    if not fixture_mode and lane in {
        "cifar_10k_generation",
        "cifar_10k_features",
        "dinov2_features",
        "released_sample_features",
    }:
        output_index = _write_scientific_payload(lane, Path(input_root), root)
        from certgen.icml2027.payload import validate_multipart_payload

        validation = validate_multipart_payload(output_index)
    else:
        output_zip = _write_result_zip(lane, root, result)
        validation = validate_output_zip(output_zip, expected_lane=lane)
    payload = {
        "schema_version": "certgen.icml2027.notebook_lane_result.v1",
        "lane": lane,
        "lane_status": LANE_STATUS[lane],
        "fixture_mode": fixture_mode,
        "resumed": False,
        "result": result,
        "output_zip": str(output_zip) if output_zip else None,
        "output_index": str(output_index) if output_index else None,
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
