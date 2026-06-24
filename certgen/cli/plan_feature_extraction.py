"""Plan dry-run-safe feature extraction."""

from __future__ import annotations

import argparse
from pathlib import Path

from certgen.core.io import write_json
from certgen.features.extractors import EXTRACTORS


def write_feature_extraction_plan(
    *,
    input_manifest: str,
    extractor: str,
    out_dir: str,
    device: str,
    batch_size: int,
    out: str,
    json_out: str,
) -> dict:
    if extractor not in EXTRACTORS:
        raise ValueError(f"unknown extractor: {extractor}")
    adapter = EXTRACTORS[extractor]()
    plan = adapter.dry_run_plan(input_manifest, out_dir, batch_size, device)
    lines = [
        "# Feature Extraction Plan V3",
        "",
        "`NO_REAL_EVIDENCE`",
        "",
        f"- Extractor: `{plan['extractor']}`",
        f"- Item count: `{plan['item_count']}`",
        f"- Missing local files: `{plan['missing_local_files_count']}`",
        f"- Estimated batches: `{plan['estimated_batches']}`",
        f"- Device request: `{plan['device_request']}`",
        f"- Extractor available: `{plan['extractor_available']}`",
        f"- Evidence status: `{plan['evidence_status']}`",
        f"- Claim allowed: `{plan['claim_allowed']}`",
        "",
        "Extraction alone cannot support paper claims.",
    ]
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_json(plan, json_out)
    return plan


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a dry-run feature extraction plan.")
    parser.add_argument("--input-manifest", required=True)
    parser.add_argument("--extractor", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--out", required=True)
    parser.add_argument("--json-out", required=True)
    args = parser.parse_args(argv)
    if not args.dry_run:
        raise SystemExit("--dry-run is required in V3 planning CLI")
    try:
        write_feature_extraction_plan(
            input_manifest=args.input_manifest,
            extractor=args.extractor,
            out_dir=args.out_dir,
            device=args.device,
            batch_size=args.batch_size,
            out=args.out,
            json_out=args.json_out,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1
    print(f"Wrote feature extraction dry-run plan: {args.out}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
