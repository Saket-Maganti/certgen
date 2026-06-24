"""Render a V2 certificate card."""

from __future__ import annotations

import argparse

from certgen.reporting.certificate_card import render_certificate_card_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render a Markdown card for a V2 certificate.")
    parser.add_argument("--certificate", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    render_certificate_card_file(args.certificate, args.out)
    print(f"Wrote certificate card: {args.out}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
