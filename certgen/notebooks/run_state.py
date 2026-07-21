"""Hash-bound resume, restart, and force-new-run state transitions."""

from __future__ import annotations

import json
import os
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from certgen.core.hashing import file_sha256
from certgen.cvpr.contracts import atomic_write_json


class RunMode(str, Enum):
    RESUME = "resume"
    RESTART = "restart"
    FORCE_NEW_RUN = "force_new_run"


SAFE_REASON = re.compile(r"[^A-Za-z0-9._-]+")


@dataclass(frozen=True)
class RunIdentity:
    run_id: str
    configuration_hash: str
    input_manifest_hash: str
    asset_manifest_hash: str

    def as_dict(self) -> dict[str, str]:
        return {
            "run_id": self.run_id,
            "configuration_hash": self.configuration_hash,
            "input_manifest_hash": self.input_manifest_hash,
            "asset_manifest_hash": self.asset_manifest_hash,
        }


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _read_identity(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("run identity must be an object")
    return payload


def _atomic_replace_json(payload: Mapping[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(json.dumps(dict(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _archive_existing(run_dir: Path, reason: str) -> Path:
    safe_reason = SAFE_REASON.sub("_", reason).strip("_") or "incompatible_state"
    quarantine = run_dir.parent / "quarantine" / f"{_timestamp()}_{safe_reason}"
    counter = 1
    while quarantine.exists():
        quarantine = quarantine.with_name(f"{quarantine.name}_{counter}")
        counter += 1
    quarantine.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(run_dir), quarantine)
    atomic_write_json(
        {
            "reason": reason,
            "quarantined_run": run_dir.name,
            "quarantine_path": str(quarantine),
            "evidence_class": "run_log_only",
            "claim_allowed": False,
        },
        quarantine / "quarantine_record.json",
    )
    return quarantine


def prepare_run_directory(
    root: str | Path,
    identity: RunIdentity,
    mode: RunMode | str,
) -> dict[str, Any]:
    selected = RunMode(mode)
    base = Path(root)
    run_id = identity.run_id
    if selected is RunMode.FORCE_NEW_RUN:
        run_id = f"{identity.run_id}__{_timestamp()}"
        identity = RunIdentity(
            run_id=run_id,
            configuration_hash=identity.configuration_hash,
            input_manifest_hash=identity.input_manifest_hash,
            asset_manifest_hash=identity.asset_manifest_hash,
        )
    run_dir = base / run_id
    quarantined: str | None = None
    reused: list[str] = []

    if run_dir.exists():
        identity_path = run_dir / "run_identity.json"
        prior = _read_identity(identity_path) if identity_path.is_file() else {}
        mismatches = [key for key, value in identity.as_dict().items() if prior.get(key) != value]
        if selected is RunMode.RESUME:
            if mismatches:
                raise ValueError("resume identity mismatch: " + ", ".join(mismatches))
            reused = [
                name for name in ("input", "model_cache", "shards", "features", "logs")
                if (run_dir / name).exists()
            ]
        elif selected is RunMode.RESTART:
            quarantined = str(_archive_existing(run_dir, "explicit_restart"))
        else:
            raise FileExistsError(f"force-new-run collision: {run_dir}")
    elif selected is RunMode.RESUME:
        raise FileNotFoundError(f"resume requested but run does not exist: {run_dir}")

    run_dir.mkdir(parents=True, exist_ok=True)
    if not (run_dir / "run_identity.json").exists():
        atomic_write_json({**identity.as_dict(), "claim_allowed": False}, run_dir / "run_identity.json")
    for name in ("logs", "shards", "status"):
        (run_dir / name).mkdir(exist_ok=True)
    payload = {
        "mode": selected.value,
        "run_id": run_id,
        "run_dir": str(run_dir),
        "quarantined": quarantined,
        "reused": reused,
        "status": "RUN_DIRECTORY_READY",
        "evidence_class": "run_log_only",
        "claim_allowed": False,
    }
    _atomic_replace_json(payload, run_dir / "status" / "run_state.json")
    return payload


def validate_completed_marker(marker: str | Path, identity: RunIdentity) -> dict[str, Any]:
    path = Path(marker)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("status") != "COMPLETE":
        raise ValueError(f"invalid completion marker: {path}")
    for key, expected in identity.as_dict().items():
        if payload.get(key) != expected:
            raise ValueError(f"completion marker {key} mismatch")
    outputs = payload.get("outputs")
    if not isinstance(outputs, dict) or not outputs:
        raise ValueError("completion marker requires output hashes")
    for raw_path, expected_hash in outputs.items():
        output = path.parent / str(raw_path)
        if not output.is_file() or file_sha256(output) != expected_hash:
            raise ValueError(f"completion marker output invalid: {raw_path}")
    return payload


def should_rebuild_final_zip(
    *,
    completed_markers_valid: bool,
    final_zip: str | Path,
    expected_sha256: str | None,
) -> bool:
    if not completed_markers_valid:
        return False
    path = Path(final_zip)
    return not path.is_file() or expected_sha256 is None or file_sha256(path) != expected_sha256


def write_completion_marker(
    path: str | Path,
    identity: RunIdentity,
    outputs: Mapping[str, str],
) -> None:
    atomic_write_json(
        {
            **identity.as_dict(),
            "status": "COMPLETE",
            "outputs": dict(outputs),
            "evidence_class": "run_log_only",
            "claim_allowed": False,
        },
        path,
    )
