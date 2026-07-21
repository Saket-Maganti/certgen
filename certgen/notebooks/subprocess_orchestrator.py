"""CUDA-safe deterministic per-GPU queue orchestrator.

The parent never imports PyTorch.  Each physical GPU has one queue and, by
default, exactly one active subprocess.  Resume markers are schema/hash checked
before reuse; stale markers are quarantined and rerun.
"""

from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Sequence

from certgen.core.hashing import file_sha256
from certgen.cvpr.contracts import atomic_write_json
from certgen.notebooks.worker_contract import (
    IMPLEMENTATION_VERSIONS,
    infer_worker_type,
    validate_completion_identity,
)


@dataclass(frozen=True)
class WorkerSpec:
    worker_id: str
    module: str
    physical_gpu: int
    shard_id: str
    args: tuple[str, ...] = ()
    completion_marker: str | None = None
    configuration_hash: str | None = None
    input_manifest_hash: str | None = None
    asset_manifest_hash: str | None = None
    worker_type: str | None = None
    worker_implementation_version: str | None = None
    config_schema_version: str | None = None
    output_schema_version: str | None = None


def _command(spec: WorkerSpec) -> list[str]:
    return [sys.executable, "-m", spec.module, *spec.args]


def _rerun_command(spec: WorkerSpec) -> str:
    command = " ".join(subprocess.list2cmdline([part]) for part in _command(spec))
    return f"CUDA_VISIBLE_DEVICES={spec.physical_gpu} {command}"


def _resume_verdict(spec: WorkerSpec) -> tuple[bool, str, str]:
    if not spec.completion_marker:
        return False, "RERUN_MISSING_OUTPUT", "completion marker not configured"
    marker = Path(spec.completion_marker)
    if not marker.is_file():
        return False, "RERUN_MISSING_OUTPUT", "completion marker missing"
    try:
        payload = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, "RERUN_INVALID_COMPLETION", f"completion marker unreadable: {exc}"
    if not isinstance(payload, dict) or payload.get("status") != "success":
        return False, "RERUN_INVALID_COMPLETION", "completion marker status is not success"
    worker_type = spec.worker_type or infer_worker_type(spec.module)
    expected_implementation = spec.worker_implementation_version or IMPLEMENTATION_VERSIONS[worker_type]
    identity = validate_completion_identity(
        payload,
        worker_type=worker_type,
        config_schema_version=spec.config_schema_version,
        output_schema_version=spec.output_schema_version,
    )
    if not identity["passed"]:
        return False, "RERUN_INVALID_COMPLETION", "; ".join(identity["errors"])
    if identity["compatibility"] == "current" and payload.get("worker_implementation_version") != expected_implementation:
        return False, "RERUN_INVALID_COMPLETION", "completion marker worker implementation mismatch"
    expected = {
        "configuration_hash": spec.configuration_hash,
        "input_manifest_hash": spec.input_manifest_hash,
        "asset_manifest_hash": spec.asset_manifest_hash,
    }
    for key, value in expected.items():
        if value is None:
            if payload.get(key) in {None, ""}:
                return False, "RERUN_INVALID_COMPLETION", f"completion marker lacks {key}"
            continue
        if payload.get(key) != value:
            status = "RERUN_ASSET_CHANGED" if key == "asset_manifest_hash" else "RERUN_CONFIG_CHANGED"
            return False, status, f"completion marker {key} mismatch"
    outputs = payload.get("outputs")
    if not isinstance(outputs, dict) or not outputs:
        return False, "RERUN_MISSING_OUTPUT", "completion marker has no output hashes"
    for raw, expected_hash in outputs.items():
        relative = PurePosixPath(str(raw))
        if (
            relative.is_absolute()
            or not relative.parts
            or ".." in relative.parts
            or "\\" in str(raw)
        ):
            return False, "RERUN_INVALID_COMPLETION", f"unsafe completion output path: {raw}"
        if (
            not isinstance(expected_hash, str)
            or len(expected_hash) != 64
            or any(character not in "0123456789abcdef" for character in expected_hash)
        ):
            return False, "RERUN_INVALID_COMPLETION", f"invalid completion output hash: {raw}"
        output = marker.parent.joinpath(*relative.parts)
        if not output.is_file():
            return False, "RERUN_MISSING_OUTPUT", f"completion output missing: {raw}"
        if file_sha256(output) != expected_hash:
            return False, "RERUN_INVALID_COMPLETION", f"completion output hash mismatch: {raw}"
    return True, "REUSED_VALID_COMPLETION", "marker schema, identity, and outputs validated"


def _quarantine_marker(spec: WorkerSpec, root: Path, status: str, reason: str) -> str | None:
    if not spec.completion_marker:
        return None
    marker = Path(spec.completion_marker)
    if not marker.exists():
        return None
    quarantine = root / "quarantine" / spec.worker_id
    quarantine.mkdir(parents=True, exist_ok=True)
    target = quarantine / marker.name
    counter = 1
    while target.exists():
        target = quarantine / f"{marker.stem}_{counter}{marker.suffix}"
        counter += 1
    shutil.move(str(marker), target)
    atomic_write_json(
        {
            "worker_id": spec.worker_id,
            "resume_status": status,
            "reason": reason,
            "quarantined_marker": str(target),
            "claim_allowed": False,
        },
        quarantine / "quarantine_record.json",
    )
    return str(target)


def _run_queue(
    gpu: int,
    specs: Sequence[WorkerSpec],
    *,
    output_dir: Path,
    deadline: float | None,
    resume: bool,
) -> list[dict[str, Any]]:
    logs = output_dir / "logs"
    statuses = output_dir / "status"
    rows: list[dict[str, Any]] = []
    queue_failed = False
    for queue_index, spec in enumerate(specs):
        if queue_failed:
            rows.append(
                {
                    **asdict(spec),
                    "status": "CANCELLED_QUEUE_FAILURE",
                    "exit_code": None,
                    "queue_index": queue_index,
                    "rerun_command": _rerun_command(spec),
                }
            )
            continue
        resume_status = "NOT_REQUESTED"
        resume_reason = "resume disabled"
        quarantined_marker: str | None = None
        if resume:
            valid, resume_status, resume_reason = _resume_verdict(spec)
            if valid:
                rows.append(
                    {
                        **asdict(spec),
                        "status": "REUSED_VALID_COMPLETION",
                        "exit_code": 0,
                        "queue_index": queue_index,
                        "resume_status": resume_status,
                        "resume_reason": resume_reason,
                    }
                )
                continue
            quarantined_marker = _quarantine_marker(spec, output_dir, resume_status, resume_reason)
        if deadline is not None and time.monotonic() >= deadline:
            rows.append(
                {
                    **asdict(spec),
                    "status": "TIMEOUT",
                    "exit_code": None,
                    "queue_index": queue_index,
                    "resume_status": resume_status,
                    "rerun_command": _rerun_command(spec),
                }
            )
            queue_failed = True
            continue
        environment = os.environ.copy()
        environment["CUDA_VISIBLE_DEVICES"] = str(gpu)
        environment["CERTGEN_PHYSICAL_GPU"] = str(gpu)
        environment["CERTGEN_SHARD_ID"] = spec.shard_id
        log_path = logs / f"{spec.worker_id}.log"
        start_wall = datetime.now(timezone.utc)
        start = time.monotonic()
        with log_path.open("w", encoding="utf-8") as handle:
            process = subprocess.Popen(
                _command(spec),
                stdout=handle,
                stderr=subprocess.STDOUT,
                text=True,
                env=environment,
            )
            remaining = None if deadline is None else max(0.0, deadline - time.monotonic())
            timed_out = False
            try:
                exit_code = process.wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                timed_out = True
                process.terminate()
                try:
                    exit_code = process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    exit_code = process.wait()
        end_wall = datetime.now(timezone.utc)
        status = "TIMEOUT" if timed_out else ("COMPLETE" if exit_code == 0 else "FAILED")
        queue_failed = status != "COMPLETE"
        row = {
            **asdict(spec),
            "status": status,
            "exit_code": exit_code,
            "queue_index": queue_index,
            "started_at": start_wall.isoformat(),
            "ended_at": end_wall.isoformat(),
            "duration_seconds": time.monotonic() - start,
            "log": str(log_path),
            "rerun_command": _rerun_command(spec),
            "resume_status": resume_status,
            "resume_reason": resume_reason,
            "quarantined_marker": quarantined_marker,
        }
        rows.append(row)
        atomic_write_json({**row, "claim_allowed": False}, statuses / f"{spec.worker_id}.json")
    return rows


def run_workers(
    specs: Sequence[WorkerSpec],
    *,
    output_dir: str | Path,
    timeout_seconds: float | None = None,
    resume: bool = False,
) -> dict[str, Any]:
    """Execute deterministic queues with one active subprocess per GPU."""

    if len({spec.worker_id for spec in specs}) != len(specs):
        raise ValueError("worker IDs must be unique")
    if len({spec.shard_id for spec in specs}) != len(specs):
        raise ValueError("shard assignments must not overlap")
    if any(spec.physical_gpu < 0 for spec in specs):
        raise ValueError("physical GPU assignments must be nonnegative")
    out = Path(output_dir)
    (out / "logs").mkdir(parents=True, exist_ok=True)
    (out / "status").mkdir(parents=True, exist_ok=True)
    queues: dict[int, list[WorkerSpec]] = {}
    for spec in specs:
        queues.setdefault(spec.physical_gpu, []).append(spec)
    assignments = {
        str(gpu): [spec.worker_id for spec in queue]
        for gpu, queue in sorted(queues.items())
    }
    atomic_write_json(
        {
            "scheduling_rule": "one_active_worker_per_physical_gpu",
            "queues": assignments,
            "claim_allowed": False,
        },
        out / "queue_assignments.json",
    )
    deadline = None if timeout_seconds is None else time.monotonic() + timeout_seconds
    rows: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(1, len(queues)), thread_name_prefix="certgen-gpu-queue") as executor:
        futures = [
            executor.submit(_run_queue, gpu, queue, output_dir=out, deadline=deadline, resume=resume)
            for gpu, queue in sorted(queues.items())
        ]
        for future in futures:
            rows.extend(future.result())
    rows.sort(key=lambda row: row["worker_id"])
    successful = {"COMPLETE", "REUSED_VALID_COMPLETION"}
    failed = any(row["status"] not in successful for row in rows)
    with (out / "worker_start_end.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("worker_id", "physical_gpu", "queue_index", "status", "started_at", "ended_at", "duration_seconds"),
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in writer.fieldnames})
    atomic_write_json(
        {row["worker_id"]: row.get("exit_code") for row in rows},
        out / "worker_exit_codes.json",
    )
    schedule = [
        {
            "worker_id": row["worker_id"],
            "physical_gpu": row["physical_gpu"],
            "queue_index": row.get("queue_index"),
            "status": row["status"],
        }
        for row in rows
    ]
    atomic_write_json({"workers": schedule, "claim_allowed": False}, out / "worker_schedule.json")
    atomic_write_json(
        {
            "method": "worker_wall_time_only_no_NVML_sampling",
            "per_gpu_worker_seconds": {
                str(gpu): sum(float(row.get("duration_seconds") or 0) for row in rows if row["physical_gpu"] == gpu)
                for gpu in sorted(queues)
            },
            "claim_allowed": False,
        },
        out / "gpu_utilization_summary.json",
    )
    payload = {
        "schema_version": "certgen.subprocess_orchestration.v2",
        "status": "PARTIAL_FAILURE" if failed else "COMPLETE",
        "scheduling_rule": "one_active_worker_per_physical_gpu",
        "workers": rows,
        "timeout_seconds": timeout_seconds,
        "parent_cuda_initialized": False,
        "evidence_class": "run_log_only",
        "claim_allowed": False,
    }
    atomic_write_json(payload, out / "orchestration_status.json")
    return payload


def load_orchestration_status(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("orchestration status must be an object")
    return payload
