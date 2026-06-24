"""Run V4 batch certificates."""

from __future__ import annotations

import argparse

from certgen.certs.batch_certificate import run_batch_from_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run V4 batch clean-core certificates.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args(argv)
    payload = run_batch_from_file(args.config, args.out_json, args.report)
    print(f"Batch certificates: {len(payload['rows'])} rows")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
