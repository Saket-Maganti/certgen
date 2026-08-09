"""Shared deterministic IO and validation helpers for the ICML 2027 layer."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import tempfile
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from certgen.icml2027 import PLANNING_BOUNDARY, TRUTH_BOUNDARY


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def stable_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def derive_seed(master_seed: int, *parts: object) -> int:
    payload = {"master_seed": int(master_seed), "parts": [str(part) for part in parts]}
    return int(stable_hash(payload)[:16], 16) % (2**32 - 1)


def load_mapping(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    with source.open(encoding="utf-8") as handle:
        if source.suffix.lower() == ".json":
            value = json.load(handle)
        else:
            value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"expected a mapping in {source}")
    return value


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        Path(temporary).unlink(missing_ok=True)
        raise


def write_json(path: str | Path, value: Mapping[str, Any] | Sequence[Any]) -> Path:
    target = Path(path)
    _atomic_write(target, json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False).encode() + b"\n")
    return target


def write_jsonl(path: str | Path, rows: Iterable[Mapping[str, Any]]) -> Path:
    target = Path(path)
    data = b"".join(canonical_json_bytes(dict(row)) for row in rows)
    _atomic_write(target, data)
    return target


def write_csv(path: str | Path, rows: Sequence[Mapping[str, Any]], fieldnames: Sequence[str] | None = None) -> Path:
    target = Path(path)
    if fieldnames is None:
        fieldnames = tuple(dict.fromkeys(key for row in rows for key in row))
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent, text=True)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    except Exception:
        Path(temporary).unlink(missing_ok=True)
        raise
    return target


def read_rows(path: str | Path) -> list[dict[str, Any]]:
    source = Path(path)
    if source.suffix == ".csv":
        with source.open(encoding="utf-8", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    if source.suffix == ".jsonl":
        return [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]
    value = json.loads(source.read_text(encoding="utf-8"))
    if isinstance(value, dict) and isinstance(value.get("records"), list):
        value = value["records"]
    if not isinstance(value, list):
        raise ValueError(f"expected a row array in {source}")
    return [dict(row) for row in value]


def synthetic_boundary(payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return {**(payload or {}), **TRUTH_BOUNDARY}


def planning_boundary(payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return {**(payload or {}), **PLANNING_BOUNDARY}


def require_false_claim(payload: Mapping[str, Any], *, planning: bool = False) -> None:
    if payload.get("claim_allowed") is not False:
        raise ValueError("claim_allowed must be false")
    if planning and payload.get("planning_only") is not True:
        raise ValueError("planning_only must be true")
