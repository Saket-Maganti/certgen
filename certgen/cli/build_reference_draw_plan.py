"""Build a precommitted with-replacement reference draw plan from JSONL."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from certgen.core.hashing import file_sha256
from certgen.core.io import write_json
from certgen.stats.reference_sampling import build_reference_draw_plan, validate_reference_draw_plan


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build an IID-with-replacement reference draw plan.")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--population-id", required=True)
    parser.add_argument("--num-draws", type=int, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    manifest = Path(args.manifest)
    rows = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    reference_rows = [row for row in rows if row.get("role") == "reference"]
    selected = reference_rows or rows
    source_ids = [row.get("sample_id") for row in selected]
    if any(item is None for item in source_ids):
        raise ValueError("every selected manifest row must contain sample_id")
    plan = build_reference_draw_plan(
        source_ids,
        num_draws=args.num_draws,
        seed=args.seed,
        population_id=args.population_id,
        source_manifest_sha256=file_sha256(manifest),
    )
    validation = validate_reference_draw_plan(plan, source_ids=source_ids)
    if not validation["passed"]:
        raise ValueError("generated reference draw plan failed validation: " + "; ".join(validation["errors"]))
    write_json(plan, args.out)
    print(f"Wrote reference draw plan: {args.out}; plan_sha256={plan['plan_sha256']}; claim_allowed=false")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
