"""Run V3 optional-stopping lab."""

from __future__ import annotations

import argparse

from certgen.stats.optional_stopping_lab import run_optional_stopping_lab_v3


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the V3 optional-stopping lab.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--json-out", required=True)
    args = parser.parse_args(argv)
    run_optional_stopping_lab_v3(args.config, args.out, args.json_out)
    print(f"Wrote V3 optional-stopping lab: {args.out}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
