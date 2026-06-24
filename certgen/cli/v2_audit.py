"""CLI for the CertGen V2 final audit."""

from __future__ import annotations

import argparse

from certgen.audit.v2_audit import run_v2_audit


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the CertGen V2 final audit.")
    parser.add_argument("--out", required=True)
    parser.add_argument("--json-out", required=True)
    args = parser.parse_args(argv)
    payload = run_v2_audit(out=args.out, json_out=args.json_out)
    print(f"V2 audit status: {payload['audit_status']}")
    return 0 if payload["audit_status"] == "passed" else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
