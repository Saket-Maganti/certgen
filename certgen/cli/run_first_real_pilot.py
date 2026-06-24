"""CLI for V4 first-real-pilot controller."""

from __future__ import annotations

import argparse

from certgen.pipeline.first_real_pilot import run_first_real_pilot_controller


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run V4 first real pilot controller.")
    parser.add_argument("--plan", required=True)
    parser.add_argument("--ledger")
    parser.add_argument("--feature-cache-dir")
    parser.add_argument("--preprocessing-lock")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    run_first_real_pilot_controller(args.plan, args.out_dir, args.report, dry_run=args.dry_run)
    print(f"Wrote first real pilot controller report: {args.report}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
