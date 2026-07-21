"""Merge generated-sample manifests with duplicate detection."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from certgen.core.io import write_json


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        row["_source_manifest"] = str(path)
        row["_source_line"] = line_no
        rows.append(row)
    return rows


def merge_sample_manifests(
    *,
    manifests: list[str | Path],
    out_manifest: str | Path,
    out_summary: str | Path,
    check_image_hashes: bool = False,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for manifest in manifests:
        rows.extend(_read_jsonl(manifest))

    errors: list[str] = []
    seen_seed: dict[tuple[str, int], dict[str, Any]] = {}
    seen_path: dict[str, dict[str, Any]] = {}
    seen_hash: dict[str, dict[str, Any]] = {}
    seen_sample_id: dict[str, dict[str, Any]] = {}
    for row in rows:
        if row.get("claim_allowed") is True:
            errors.append(f"{row.get('_source_manifest')}:{row.get('_source_line')}: claim_allowed=true is forbidden")
        sample_id = str(row.get("sample_id") or "")
        if sample_id:
            if sample_id in seen_sample_id:
                errors.append(f"duplicate sample_id: {sample_id}")
            seen_sample_id[sample_id] = row
        checkpoint_id = str(row.get("checkpoint_id") or row.get("model_id") or "unknown")
        if "seed" in row:
            key = (checkpoint_id, int(row["seed"]))
            if key in seen_seed:
                errors.append(f"duplicate seed for {checkpoint_id}: {row['seed']}")
            seen_seed[key] = row
        image_path = str(row.get("image_path") or row.get("path") or "")
        if image_path:
            if image_path in seen_path:
                errors.append(f"duplicate image path: {image_path}")
            seen_path[image_path] = row
        image_hash = row.get("image_hash") or row.get("sha256")
        if check_image_hashes and image_hash:
            if image_hash in seen_hash:
                errors.append(f"duplicate image hash: {image_hash}")
            seen_hash[str(image_hash)] = row

    clean_rows = []
    for row in rows:
        clean = {key: value for key, value in row.items() if not key.startswith("_")}
        clean["claim_allowed"] = False
        clean_rows.append(clean)
    clean_rows.sort(key=lambda row: (str(row.get("checkpoint_id", row.get("model_id", ""))), int(row.get("seed", -1)), str(row.get("sample_id", ""))))

    out_manifest = Path(out_manifest)
    out_manifest.parent.mkdir(parents=True, exist_ok=True)
    if not errors:
        with out_manifest.open("w", encoding="utf-8") as handle:
            for row in clean_rows:
                handle.write(json.dumps(row, sort_keys=True) + "\n")

    summary = {
        "passed": not errors,
        "errors": errors,
        "rows": len(clean_rows),
        "manifests": [str(item) for item in manifests],
        "out_manifest": str(out_manifest),
        "check_image_hashes": check_image_hashes,
        "evidence_status": "r1a_sample_package_non_evidence",
        "claim_allowed": False,
    }
    write_json(summary, out_summary)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Merge generated-sample manifests.")
    parser.add_argument("--manifest", action="append", required=True)
    parser.add_argument("--out-manifest", required=True)
    parser.add_argument("--out-summary", required=True)
    parser.add_argument("--check-image-hashes", action="store_true")
    args = parser.parse_args(argv)
    try:
        summary = merge_sample_manifests(
            manifests=args.manifest,
            out_manifest=args.out_manifest,
            out_summary=args.out_summary,
            check_image_hashes=args.check_image_hashes,
        )
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 2
    if not summary["passed"]:
        print(f"ERROR: merge failed with {len(summary['errors'])} duplicate/schema errors")
        return 2
    print(f"merged {summary['rows']} generated-sample rows -> {summary['out_manifest']}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
