"""CLI for metric reproduction audit."""

from __future__ import annotations

import argparse

from certgen.audit.metric_reproduction import run_metric_reproduction_audit


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a V3 metric reproduction audit.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--json-out", required=True)
    args = parser.parse_args(argv)
    payload = run_metric_reproduction_audit(args.config, args.out, args.json_out)
    print(f"Metric reproduction audit status: {payload['reproduction_status']}")
    return 0 if not payload["errors"] else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
