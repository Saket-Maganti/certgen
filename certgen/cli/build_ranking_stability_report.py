"""Build V4 ranking stability report."""

from __future__ import annotations

import argparse

from certgen.analysis.ranking_stability import build_ranking_stability


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a V4 ranking stability report.")
    parser.add_argument("--batch-json", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--json-out", required=True)
    args = parser.parse_args(argv)
    build_ranking_stability(args.batch_json, args.out, args.json_out)
    print(f"Wrote ranking stability report: {args.out}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
