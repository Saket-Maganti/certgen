"""JSONL execution ledger for V7."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class LedgerEvent:
    stage: str
    command: str
    status: str
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    hashes: dict[str, str] = field(default_factory=dict)
    blocker_code: str | None = None
    claim_allowed: bool = False
    evidence_status: str = "NO_REAL_EVIDENCE"
    run_log_only: bool = True
    notes: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_json(self) -> str:
        if self.claim_allowed:
            raise ValueError("V7 ledger events must not set claim_allowed=true")
        return json.dumps(asdict(self), sort_keys=True)


def append_event(path: str | Path, event: LedgerEvent) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(event.to_json() + "\n")


def read_events(path: str | Path) -> list[dict[str, Any]]:
    path = Path(path)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def current_blocker(events: list[dict[str, Any]]) -> str:
    for event in reversed(events):
        blocker = event.get("blocker_code")
        if blocker:
            return str(blocker)
    return "BLOCKED_MISSING_REFERENCE_SAMPLES"


def render_dashboard(events: list[dict[str, Any]]) -> str:
    blocker = current_blocker(events)
    next_command = {
        "BLOCKED_MISSING_REFERENCE_SAMPLES": (
            "CIFAR_SEARCH_ROOT=/path/to/cifar bash "
            "commands/v7_cpu_execution/01_auto_materialize_cifar_reference.sh"
        ),
        "BLOCKED_GENERATION_OUTPUT_ZIP_MISSING": (
            "Run notebooks/kaggle/v7_certgen_cifar10_generation_t4x2_bookrun.ipynb"
        ),
        "BLOCKED_FEATURE_OUTPUT_ZIP_MISSING": (
            "Run notebooks/kaggle/v7_certgen_cifar10_feature_extraction_t4x2_bookrun.ipynb"
        ),
    }.get(blocker, "Inspect data/results/v7_execution_development_audit.json")
    lines = [
        "# V7 Execution Dashboard",
        "",
        f"- Current blocker: `{blocker}`",
        f"- Next exact command: `{next_command}`",
        f"- Ledger events: `{len(events)}`",
        "- Claim allowed: `false`",
        "- Evidence status: no fake evidence promoted",
    ]
    return "\n".join(lines) + "\n"
