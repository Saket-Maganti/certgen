"""CLI wrapper for the final V6 execution audit."""

from __future__ import annotations

import argparse

from certgen.pipeline.v6_execution import write_final_execution_audit


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write the final execution audit.")
    parser.add_argument("--out", required=True)
    parser.add_argument("--json-out", required=True)
    args = parser.parse_args(argv)
    payload = write_final_execution_audit(out_json=args.json_out, report=args.out)
    print(f"Final execution audit: {payload['status_code']}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
