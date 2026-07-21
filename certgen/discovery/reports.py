"""Stable JSON-safe discovery reporting helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


def write_resolution_report(payload: Mapping[str, Any], path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.tmp")
    temporary.write_text(json.dumps(dict(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(target)
