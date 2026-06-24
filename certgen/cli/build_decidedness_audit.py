"""Build V4 decidedness audit."""

from __future__ import annotations

import argparse

from certgen.analysis.decidedness import build_decidedness_audit


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a V4 decidedness audit from batch certificates.")
    parser.add_argument("--batch-json", required=True)
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args(argv)
    build_decidedness_audit(args.batch_json, args.out_csv, args.out_json, args.report)
    print(f"Wrote decidedness audit: {args.out_json}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
