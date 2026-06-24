"""CLI for V2 dry-run first-pilot planning."""

from __future__ import annotations

import argparse

from certgen.pilot.first_pilot_v2 import plan_first_pilot_v2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a dry-run-only V2 first-pilot plan.")
    parser.add_argument("--registry-dir", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    if not args.dry_run:
        raise SystemExit("--dry-run is required for V2 first-pilot planning")
    plan_first_pilot_v2(args.registry_dir, args.out_json, args.out_md, dry_run=True)
    print(f"Wrote V2 first-pilot dry-run plan: {args.out_json}, {args.out_md}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
