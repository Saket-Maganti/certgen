"""Render a V3 pilot report card."""

from __future__ import annotations

import argparse

from certgen.reporting.pilot_cards import render_pilot_report_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render a claim-safe V3 pilot report.")
    parser.add_argument("--summary-json", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    render_pilot_report_file(args.summary_json, args.out)
    print(f"Wrote pilot report card: {args.out}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
