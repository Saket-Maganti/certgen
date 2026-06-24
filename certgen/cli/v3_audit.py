"""CLI for V3 final audit."""

from __future__ import annotations

import argparse

from certgen.audit.v3_final import run_v3_final_audit


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run CertGen V3 final audit.")
    parser.add_argument("--out", required=True)
    parser.add_argument("--json-out", required=True)
    args = parser.parse_args(argv)
    payload = run_v3_final_audit(out=args.out, json_out=args.json_out)
    print(f"V3 audit status: {'passed' if payload['passed'] else 'failed'}")
    return 0 if payload["passed"] else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
