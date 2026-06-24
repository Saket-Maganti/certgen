"""Generate a first-pilot TODO plan from registry templates."""

from __future__ import annotations

import argparse
from pathlib import Path

from certgen.gates.claim_gate import assert_claim_safe
from certgen.pilots.registry import plan_first_pilot_markdown, read_csv_rows


def write_first_pilot_plan(*, pairs: str, out: str) -> str:
    rows = read_csv_rows(pairs)
    markdown = plan_first_pilot_markdown(rows)
    assert_claim_safe(markdown, evidence_status="non_evidence_planned")
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown, encoding="utf-8")
    return markdown


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write the first CertGen pilot plan.")
    parser.add_argument("--pairs", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    write_first_pilot_plan(pairs=args.pairs, out=args.out)
    print(f"Wrote first-pilot plan: {args.out}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
