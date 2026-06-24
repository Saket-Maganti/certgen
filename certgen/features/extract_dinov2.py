"""Dry-run DINOv2 feature extraction placeholder."""

from __future__ import annotations

import argparse


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="DINOv2 feature extraction stub.")
    parser.add_argument("--input")
    parser.add_argument("--out")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    if args.dry_run:
        print("Dry run only: DINOv2 extraction requires explicit inputs and optional vision dependencies.")
        return 0
    raise SystemExit("Real DINOv2 extraction is not implemented in V1; rerun with --dry-run.")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
