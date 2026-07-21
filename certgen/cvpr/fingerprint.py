"""Fail-closed reproducibility fingerprint for the canonical CVPR pipeline."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any, Mapping

from certgen.core.hashing import file_sha256, stable_hash_json
from certgen.cvpr.contracts import atomic_write_json


REQUIRED_INPUTS = (
    "benchmark_registry",
    "model_registry",
    "feature_registry",
    "preregistration",
    "reference_manifest",
    "asset_manifest",
    "generation_config",
    "feature_config",
    "family_config",
)


def _code_commit(root: Path) -> str:
    """Return the current commit, or an explicit portable non-Git label."""

    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    commit = completed.stdout.strip()
    return commit if completed.returncode == 0 and len(commit) == 40 else "NOT_AVAILABLE_NON_GIT_EXPORT"


def build_reproducibility_fingerprint(
    inputs: Mapping[str, str | Path],
    *,
    environment: Mapping[str, Any],
    root: str | Path = ".",
    out: str | Path | None = None,
) -> dict[str, Any]:
    """Bind every claim-relevant configuration and environment into one hash.

    Missing or duplicate inputs are rejected.  This deliberately cannot produce a
    partial fingerprint that could later be mistaken for complete lineage.
    """

    missing_keys = sorted(set(REQUIRED_INPUTS) - set(inputs))
    extra_keys = sorted(set(inputs) - set(REQUIRED_INPUTS))
    if missing_keys or extra_keys:
        raise ValueError(f"fingerprint input keys mismatch: missing={missing_keys}, extra={extra_keys}")
    resolved: dict[str, dict[str, Any]] = {}
    seen_paths: set[Path] = set()
    for name in REQUIRED_INPUTS:
        path = Path(inputs[name]).resolve()
        if not path.is_file() or path.is_symlink():
            raise FileNotFoundError(f"fingerprint input is missing or unsafe: {name}={path}")
        if path in seen_paths:
            raise ValueError(f"fingerprint inputs must be distinct: {path}")
        seen_paths.add(path)
        resolved[name] = {"path": os.path.relpath(path, Path(root).resolve()), "sha256": file_sha256(path)}
    if not environment:
        raise ValueError("fingerprint environment must be non-empty")
    payload: dict[str, Any] = {
        "schema_version": "certgen.cvpr.reproducibility_fingerprint.v1",
        "inputs": resolved,
        "code_commit": _code_commit(Path(root).resolve()),
        "environment": dict(environment),
        "environment_hash": stable_hash_json(environment),
        "complete": True,
        "claim_allowed": False,
    }
    payload["fingerprint"] = stable_hash_json(payload)
    if out is not None:
        atomic_write_json(payload, out)
    return payload


def verify_reproducibility_fingerprint(payload: Mapping[str, Any], *, root: str | Path = ".") -> dict[str, Any]:
    """Verify the fingerprint and every current file hash without mutating state."""

    candidate = dict(payload)
    expected = candidate.pop("fingerprint", None)
    errors: list[str] = []
    if expected != stable_hash_json(candidate):
        errors.append("fingerprint object hash mismatch")
    rows = payload.get("inputs")
    if not isinstance(rows, dict) or set(rows) != set(REQUIRED_INPUTS):
        errors.append("fingerprint input set is incomplete")
    else:
        base = Path(root).resolve()
        for name, raw in rows.items():
            if not isinstance(raw, dict):
                errors.append(f"invalid fingerprint row: {name}")
                continue
            path = (base / str(raw.get("path", ""))).resolve()
            if not path.is_file():
                errors.append(f"fingerprint input missing: {name}")
            elif file_sha256(path) != raw.get("sha256"):
                errors.append(f"fingerprint input changed: {name}")
    return {"passed": not errors, "errors": errors, "fingerprint": expected, "claim_allowed": False}
