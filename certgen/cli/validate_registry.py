"""Validate pilot registry CSV templates."""

from __future__ import annotations

import argparse

from certgen.pilots.registry import read_csv_rows, validate_benchmark_rows, validate_pair_rows


def validate_registry(benchmarks: str, pairs: str) -> list[str]:
    errors = []
    errors.extend(validate_benchmark_rows(read_csv_rows(benchmarks)))
    errors.extend(validate_pair_rows(read_csv_rows(pairs)))
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate CertGen pilot registry templates.")
    parser.add_argument("--benchmarks", required=True)
    parser.add_argument("--pairs", required=True)
    args = parser.parse_args(argv)
    errors = validate_registry(args.benchmarks, args.pairs)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Registry templates valid: planned rows preserved; no scores fabricated.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
