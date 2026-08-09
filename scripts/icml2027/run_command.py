#!/usr/bin/env python3
"""Run one CPU-only ICML 2027 command and append auditable ledgers."""

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


ROOT = Path(__file__).resolve().parents[2]
REPORT_ROOT = ROOT / "reports" / "icml2027"
LOG_ROOT = REPORT_ROOT / "command_logs"
CSV_LEDGER = REPORT_ROOT / "CERTGEN_ICML2027_COMMAND_LEDGER.csv"
JSONL_LEDGER = REPORT_ROOT / "CERTGEN_ICML2027_COMMAND_LEDGER.jsonl"
FIELDS = (
    "sequence",
    "phase",
    "command",
    "cwd",
    "start_utc",
    "end_utc",
    "duration_seconds",
    "exit_code",
    "status",
    "stdout_log",
    "stderr_log",
    "artifacts_created",
    "artifacts_reused",
    "blocker",
    "claim_allowed",
)


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
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    exists = CSV_LEDGER.is_file()
    with CSV_LEDGER.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        if not exists:
            writer.writeheader()
        writer.writerow(row)
    with JSONL_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", required=True)
    parser.add_argument("--cwd", default=str(ROOT))
    parser.add_argument("--allow-exit-code", action="append", type=int, default=[])
    parser.add_argument("--artifacts-created", default="")
    parser.add_argument("--artifacts-reused", default="")
    parser.add_argument("--blocker", default="")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("a command is required after --")

    sequence = _next_sequence()
    safe_phase = args.phase.replace("/", "_").replace(" ", "_")
    LOG_ROOT.mkdir(parents=True, exist_ok=True)
    stdout_path = LOG_ROOT / f"{sequence:04d}_{safe_phase}.stdout.log"
    stderr_path = LOG_ROOT / f"{sequence:04d}_{safe_phase}.stderr.log"
    environment = os.environ.copy()
    environment.update(
        {
            "CUDA_VISIBLE_DEVICES": "",
            "CERTGEN_CPU_ONLY": "1",
            "PYTHONHASHSEED": "0",
            "OMP_NUM_THREADS": environment.get("OMP_NUM_THREADS", "1"),
        }
    )
    started_utc = _utc_now()
    started = time.monotonic()
    result = subprocess.run(
        command,
        cwd=args.cwd,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    duration = time.monotonic() - started
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
        "start_utc": started_utc,
        "end_utc": _utc_now(),
        "duration_seconds": f"{duration:.6f}",
        "exit_code": result.returncode,
        "status": status,
        "stdout_log": stdout_path.relative_to(ROOT).as_posix(),
        "stderr_log": stderr_path.relative_to(ROOT).as_posix(),
        "artifacts_created": args.artifacts_created,
        "artifacts_reused": args.artifacts_reused,
        "blocker": args.blocker,
        "claim_allowed": False,
    }
    _append(row)
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    return 0 if result.returncode in allowed else result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
