"""Provenance helpers for generated smoke artifacts."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from certgen import __version__
from certgen.core.hashing import stable_hash_json


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_provenance(
    *,
    config: dict[str, Any] | None = None,
    command: str | None = None,
    input_paths: list[str] | None = None,
    notes: list[str] | None = None,
) -> dict[str, Any]:
    config = config or {}
    input_paths = input_paths or []
    return {
        "created_at_utc": utc_now_iso(),
        "certgen_version": __version__,
        "code_version": "uncommitted_or_not_git_controlled_v1_placeholder",
        "config_hash": stable_hash_json(config),
        "command": command or "",
        "input_paths": [str(Path(path)) for path in input_paths],
        "notes": notes or [],
    }
