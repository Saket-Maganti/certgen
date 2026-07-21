"""Fail-closed evidence classification derived from artifact provenance."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable


SYNTHETIC_STATUSES = {"synthetic_only", "smoke_only", "non_evidence_smoke", "non_evidence_synthetic"}
REAL_LIKE_STATUSES = {
    "real_features_validated",
    "real_pilot_non_claim",
    "real_pilot_claim_blocked",
    "pilot_only",
    "real_evidence_candidate",
}


def _path_is_synthetic(path: str | Path) -> bool:
    lowered = str(path).replace("\\", "/").lower()
    parts = {part for part in lowered.split("/") if part}
    return "/data/smoke/" in f"/{lowered.strip('/')}/" or bool(parts & {"smoke", "fixtures", "fixture"})


def _sidecar_is_synthetic(path: str | Path) -> bool:
    sidecar = Path(path)
    if not sidecar.is_file():
        return False
    try:
        payload = json.loads(sidecar.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    flattened = json.dumps(payload, sort_keys=True).lower()
    explicit = str(payload.get("evidence_status", "")).lower() in SYNTHETIC_STATUSES
    smoke_fields = any(
        "smoke" in str(payload.get(field, "")).lower()
        for field in ["benchmark_id", "split", "cache_id", "created_by"]
    )
    source_hash = str((payload.get("hashes") or {}).get("source_manifest_sha256", "")).lower()
    return explicit or smoke_fields or source_hash in {"smoke", "synthetic", "fixture"} or "/data/smoke/" in flattened


def classify_inputs(
    paths: Iterable[str | Path], sidecars: Iterable[str | Path] = ()
) -> tuple[str, str]:
    path_list = [str(path) for path in paths]
    sidecar_list = [str(path) for path in sidecars]
    if any(_path_is_synthetic(path) for path in path_list) or any(
        _sidecar_is_synthetic(path) for path in sidecar_list
    ):
        return "synthetic_only", "input path or sidecar identifies smoke, fixture, or synthetic provenance"
    return "provenance_not_synthetic", "no synthetic marker detected; real provenance still requires separate validation"


def enforce_declared_status(
    declared_status: str,
    paths: Iterable[str | Path],
    sidecars: Iterable[str | Path] = (),
) -> None:
    detected, reason = classify_inputs(paths, sidecars)
    if detected == "synthetic_only" and declared_status in REAL_LIKE_STATUSES:
        raise ValueError(f"synthetic/smoke inputs cannot use evidence_status={declared_status}: {reason}")
