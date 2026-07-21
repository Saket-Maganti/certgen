#!/usr/bin/env python3
"""Run one local-safe closure command and append a durable command ledger row."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import os
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
LOG_ROOT = REPORTS / "real_execution_closure_command_logs"
LEDGER = REPORTS / "CERTGEN_REAL_EXECUTION_CLOSURE_COMMAND_LEDGER.csv"
FIELDS = [
    "command_id",
    "command",
    "working_directory",
    "environment",
    "start_utc",
    "end_utc",
    "duration_seconds",
    "exit_code",
    "passed",
    "failed",
    "skipped_or_deselected",
    "warnings",
    "output",
    "evidence_boundary",
]
COUNT_PATTERNS = {
    "passed": re.compile(r"(?:^|\s)(\d+) passed(?:\s|,|$)"),
    "failed": re.compile(r"(?:^|\s)(\d+) failed(?:\s|,|$)"),
    "skipped": re.compile(r"(?:^|\s)(\d+) skipped(?:\s|,|$)"),
    "deselected": re.compile(r"(?:^|\s)(\d+) deselected(?:\s|,|$)"),
    "warnings": re.compile(r"(?:^|\s)(\d+) warnings?(?:\s|,|$)"),
}


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def _existing_ids() -> set[str]:
    if not LEDGER.is_file():
        return set()
    with LEDGER.open(encoding="utf-8", newline="") as handle:
        return {row.get("command_id", "") for row in csv.DictReader(handle)}


def _append(row: dict[str, object]) -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    exists = LEDGER.is_file()
    with LEDGER.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def _last_summary(output: str) -> str:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    summary = lines[-1] if lines else "no console output"
    return summary.replace(str(ROOT), "<repo-root>")[:1000]


def _last_count(pattern: re.Pattern[str], output: str) -> int:
    matches = pattern.findall(output)
    return int(matches[-1]) if matches else 0


def _portable_working_directory(path: Path) -> str:
    resolved = path.resolve()
    try:
        relative = resolved.relative_to(ROOT)
    except ValueError:
        return resolved.name
    return "." if not relative.parts else relative.as_posix()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", required=True)
    parser.add_argument("--cwd", default=str(ROOT))
    parser.add_argument("--allow-exit-code", action="append", type=int, default=[])
    parser.add_argument("--evidence-boundary", default="local-safe software validation only")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("a command is required after --")
    if args.id in _existing_ids():
        parser.error(f"command id already exists in closure ledger: {args.id}")

    safe_id = re.sub(r"[^A-Za-z0-9_.-]", "_", args.id)
    LOG_ROOT.mkdir(parents=True, exist_ok=True)
    stdout_path = LOG_ROOT / f"{safe_id}.stdout.log"
    stderr_path = LOG_ROOT / f"{safe_id}.stderr.log"
    environment = os.environ.copy()
    environment["CUDA_VISIBLE_DEVICES"] = ""
    environment["CERTGEN_CPU_ONLY"] = "1"
    environment["PYTHONHASHSEED"] = "0"
    start_utc = _utc_now()
    started = time.monotonic()
    result = subprocess.run(
        command,
        cwd=Path(args.cwd),
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    duration = time.monotonic() - started
    end_utc = _utc_now()
    stdout_path.write_text(result.stdout, encoding="utf-8")
    stderr_path.write_text(result.stderr, encoding="utf-8")
    combined = "\n".join(part for part in (result.stdout, result.stderr) if part)
    skipped = _last_count(COUNT_PATTERNS["skipped"], combined)
    deselected = _last_count(COUNT_PATTERNS["deselected"], combined)
    _append(
        {
            "command_id": args.id,
            "command": shlex.join(command),
            "working_directory": _portable_working_directory(Path(args.cwd)),
            "environment": "CUDA_VISIBLE_DEVICES='' CERTGEN_CPU_ONLY=1 PYTHONHASHSEED=0",
            "start_utc": start_utc,
            "end_utc": end_utc,
            "duration_seconds": f"{duration:.6f}",
            "exit_code": result.returncode,
            "passed": _last_count(COUNT_PATTERNS["passed"], combined),
            "failed": _last_count(COUNT_PATTERNS["failed"], combined),
            "skipped_or_deselected": skipped + deselected,
            "warnings": _last_count(COUNT_PATTERNS["warnings"], combined),
            "output": _last_summary(combined),
            "evidence_boundary": args.evidence_boundary,
        }
    )
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    allowed = {0, *args.allow_exit_code}
    return 0 if result.returncode in allowed else result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
