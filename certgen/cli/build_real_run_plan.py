"""CLI for V4 real-run plan construction."""

from __future__ import annotations

import argparse

from certgen.provenance.real_run_plan import build_real_run_plan


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a non-claim V4 real-run plan from provenance.")
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--comparison-id", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--requested-budget", type=int)
    args = parser.parse_args(argv)
    plan = build_real_run_plan(args.ledger, args.comparison_id, args.out, args.report, args.requested_budget)
    print(f"Real-run plan status: {'blocked' if plan['blockers'] else 'ready_nonclaim'}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
