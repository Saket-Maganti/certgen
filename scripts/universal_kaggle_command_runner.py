#!/usr/bin/env python3
"""Run one CPU-only command and append the universal Kaggle audit ledgers."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
LOG_ROOT = REPORTS / "universal_kaggle_command_logs"
CSV_LEDGER = REPORTS / "CERTGEN_UNIVERSAL_KAGGLE_COMMAND_LEDGER.csv"
JSONL_LEDGER = REPORTS / "CERTGEN_UNIVERSAL_KAGGLE_COMMAND_LEDGER.jsonl"
FIELDS = [
    "sequence",
    "phase",
    "command",
    "cwd",
    "start_utc",
    "end_utc",
    "duration_seconds",
    "exit_code",
    "stdout_log",
    "stderr_log",
    "status",
    "artifacts_created",
    "artifacts_reused",
    "blocker",
]


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def _next_sequence() -> int:
    if not CSV_LEDGER.is_file():
        return 1
    with CSV_LEDGER.open(encoding="utf-8", newline="") as handle:
        return 1 + max(
            (int(row["sequence"]) for row in csv.DictReader(handle) if row.get("sequence")),
            default=0,
        )


def _append(row: dict[str, object]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    csv_exists = CSV_LEDGER.is_file()
    with CSV_LEDGER.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        if not csv_exists:
            writer.writeheader()
        writer.writerow(row)
    with JSONL_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", required=True)
    parser.add_argument("--cwd", default=str(ROOT))
    parser.add_argument("--allow-exit-code", action="append", type=int, default=[])
    parser.add_argument("--artifacts-created", default="")
    parser.add_argument("--artifacts-reused", default="")
    parser.add_argument("--blocker", default="")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("a command is required after --")

    sequence = _next_sequence()
    LOG_ROOT.mkdir(parents=True, exist_ok=True)
    safe_phase = args.phase.replace("/", "_").replace(" ", "_")
    stem = f"{sequence:04d}_{safe_phase}"
    stdout_path = LOG_ROOT / f"{stem}.stdout.log"
    stderr_path = LOG_ROOT / f"{stem}.stderr.log"
    environment = os.environ.copy()
    environment["CUDA_VISIBLE_DEVICES"] = ""
    environment["CERTGEN_CPU_ONLY"] = "1"
    start_utc = _utc_now()
    started = time.monotonic()
    result = subprocess.run(command, cwd=args.cwd, env=environment, capture_output=True, text=True)
    duration = time.monotonic() - started
    end_utc = _utc_now()
    stdout_path.write_text(result.stdout, encoding="utf-8")
    stderr_path.write_text(result.stderr, encoding="utf-8")
    allowed = {0, *args.allow_exit_code}
    status = "PASS" if result.returncode == 0 else (
        "EXPECTED_BOUNDARY" if result.returncode in allowed else "FAIL"
    )
    resolved_cwd = Path(args.cwd).resolve()
    try:
        relative_cwd = resolved_cwd.relative_to(ROOT)
        recorded_cwd = "." if not relative_cwd.parts else relative_cwd.as_posix()
    except ValueError:
        recorded_cwd = "<external>"
    row: dict[str, object] = {
        "sequence": sequence,
        "phase": args.phase,
        "command": shlex.join(command),
        "cwd": recorded_cwd,
        "start_utc": start_utc,
        "end_utc": end_utc,
        "duration_seconds": f"{duration:.6f}",
        "exit_code": result.returncode,
        "stdout_log": str(stdout_path.relative_to(ROOT)),
        "stderr_log": str(stderr_path.relative_to(ROOT)),
        "status": status,
        "artifacts_created": args.artifacts_created,
        "artifacts_reused": args.artifacts_reused,
        "blocker": args.blocker,
    }
    _append(row)
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    return 0 if result.returncode in allowed else result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
