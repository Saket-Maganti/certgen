"""Validate a released-sample provenance ledger."""

from __future__ import annotations

import argparse

from certgen.registry.provenance import validate_provenance_ledger, write_provenance_validation_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate CertGen V3 provenance ledger.")
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--json-out", required=True)
    parser.add_argument("--allow-missing-local", action="store_true")
    parser.add_argument("--require-real-pilot", action="store_true")
    args = parser.parse_args(argv)
    result = validate_provenance_ledger(args.ledger, allow_missing_local=args.allow_missing_local, require_real_pilot=args.require_real_pilot)
    write_provenance_validation_report(result, args.out, args.json_out)
    print(f"Provenance ledger validation: {'passed' if result['passed'] else 'failed'}")
    return 0 if result["passed"] else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
