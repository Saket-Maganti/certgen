"""Validate reported metric claims."""

from __future__ import annotations

import argparse
from pathlib import Path

from certgen.core.io import write_json
from certgen.literature.claim_ingest import read_claims, validate_claims
from certgen.literature.claim_trace import build_claim_trace


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate reported metric claim rows.")
    parser.add_argument("--claims", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--json-out", required=True)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    result = validate_claims(args.claims, strict=args.strict)
    traces = [build_claim_trace(row) for row in read_claims(args.claims)]
    result["traces"] = traces
    lines = ["# Reported Claim Validation V4", "", "`NO_REAL_EVIDENCE`", "", f"Passed: `{result['passed']}`", "", "## Errors"]
    lines.extend(f"- {e}" for e in result["errors"] or ["none"])
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_json(result, args.json_out)
    print(f"Reported claims validation: {'passed' if result['passed'] else 'failed'}")
    return 0 if result["passed"] else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
