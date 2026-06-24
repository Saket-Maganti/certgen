"""Render V3 availability table."""

from __future__ import annotations

import argparse

from certgen.registry.v3_schema import render_availability_table


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render CertGen V3 availability table.")
    parser.add_argument("--registry-dir", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--json-out", required=True)
    args = parser.parse_args(argv)
    render_availability_table(args.registry_dir, args.out, args.json_out)
    print(f"Wrote availability table: {args.out}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
