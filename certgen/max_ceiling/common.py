"""Shared deterministic helpers for maximum-ceiling artifacts."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable, Mapping

from certgen.core.hashing import stable_hash_json
from certgen.cvpr.study import require_frozen_study


def load_study(path: str | Path) -> dict[str, Any]:
    """Load and independently validate one frozen prospective study."""

    return require_frozen_study(path)


def study_hash(study: Mapping[str, Any]) -> str:
    value = str(study.get("configuration_hash", ""))
    if len(value) != 64:
        raise ValueError("frozen study has no valid configuration_hash")
    return value


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, separators=(",", ": ")) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json_idempotent(payload: Any, path: str | Path) -> Path:
    target = Path(path)
    serialized = canonical_json_bytes(payload)
    if target.exists():
        if target.read_bytes() != serialized:
            raise FileExistsError(f"refusing to overwrite non-identical artifact: {target}")
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.tmp-{os.getpid()}")
    temporary.write_bytes(serialized)
    os.replace(temporary, target)
    return target


def write_text_idempotent(text: str, path: str | Path) -> Path:
    target = Path(path)
    data = text.encode("utf-8")
    if target.exists():
        if target.read_bytes() != data:
            raise FileExistsError(f"refusing to overwrite non-identical artifact: {target}")
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.tmp-{os.getpid()}")
    temporary.write_bytes(data)
    os.replace(temporary, target)
    return target


def write_csv_idempotent(
    rows: Iterable[Mapping[str, Any]], fields: list[str], path: str | Path
) -> Path:
    import io

    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow(
            {
                field: json.dumps(row.get(field), sort_keys=True)
                if isinstance(row.get(field), (dict, list))
                else row.get(field)
                for field in fields
            }
        )
    return write_text_idempotent(stream.getvalue(), path)


def artifact_root(study: Mapping[str, Any], root: str | Path = ".") -> Path:
    return Path(root) / "artifacts" / "max_ceiling" / study_hash(study)


def deterministic_identity(payload: Mapping[str, Any]) -> str:
    return stable_hash_json(dict(payload))
