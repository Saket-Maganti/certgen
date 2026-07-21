#!/usr/bin/env python3
"""Run one Phase 1 command CPU-only and append a durable audit-ledger row."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
LOG_ROOT = REPORTS / "phase1_command_logs"
LEDGER = REPORTS / "CERTGEN_PHASE1_COMMAND_LEDGER.csv"
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
    if not LEDGER.is_file():
        return 1
    with LEDGER.open(encoding="utf-8", newline="") as handle:
        return 1 + max(
            (int(row["sequence"]) for row in csv.DictReader(handle) if row.get("sequence")),
            default=0,
        )


def _append(row: dict[str, object]) -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    exists = LEDGER.is_file()
    with LEDGER.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        if not exists:
            writer.writeheader()
        writer.writerow(row)


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
    stem = f"{sequence:04d}_{args.phase.replace('/', '_').replace(' ', '_')}"
    stdout_path = LOG_ROOT / f"{stem}.stdout.log"
    stderr_path = LOG_ROOT / f"{stem}.stderr.log"
    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = ""
    env["CERTGEN_CPU_ONLY"] = "1"
    start_utc = _utc_now()
    started = time.monotonic()
    result = subprocess.run(command, cwd=args.cwd, env=env, capture_output=True, text=True)
    duration = time.monotonic() - started
    end_utc = _utc_now()
    stdout_path.write_text(result.stdout, encoding="utf-8")
    stderr_path.write_text(result.stderr, encoding="utf-8")
    allowed = {0, *args.allow_exit_code}
    status = "PASS" if result.returncode == 0 else ("EXPECTED_BOUNDARY" if result.returncode in allowed else "FAIL")
    _append(
        {
            "sequence": sequence,
            "phase": args.phase,
            "command": shlex.join(command),
            "cwd": str(Path(args.cwd).resolve()),
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
    )
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    return 0 if result.returncode in allowed else result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
