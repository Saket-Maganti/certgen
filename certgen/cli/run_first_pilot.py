"""CLI for V3 first-pilot orchestration."""

from __future__ import annotations

import argparse

from certgen.pilot.orchestrator import run_first_pilot


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run or dry-run the V3 first pilot.")
    parser.add_argument("--pilot-config", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--json-out", required=True)
    args = parser.parse_args(argv)
    summary = run_first_pilot(args.pilot_config, args.out_dir, args.report, args.json_out)
    print(f"First pilot V3 status: mode={summary['mode']} claim_allowed={summary['claim_allowed']}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
