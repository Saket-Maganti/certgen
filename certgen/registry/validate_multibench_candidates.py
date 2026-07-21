from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


REQUIRED = {
    "benchmark",
    "source_type",
    "sample_availability",
    "license",
    "expected_compute",
    "feature_extractors",
    "metric_reproduction_availability",
    "risk",
    "status",
}


def validate(path: str | Path) -> dict[str, object]:
    rows = list(csv.DictReader(Path(path).open(encoding="utf-8")))
    missing = [column for column in REQUIRED if column not in (rows[0].keys() if rows else set())]
    fake_ready = [row["benchmark"] for row in rows if row.get("status") == "ready_without_evidence"]
    return {
        "row_count": len(rows),
        "missing_columns": sorted(missing),
        "fake_ready_rows": fake_ready,
        "ok": not missing and not fake_ready,
        "claim_allowed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="registry/provenance/multibench_candidate_sources.csv")
    parser.add_argument("--out", default="data/results/v7_multibench_candidate_validation.json")
    args = parser.parse_args(argv)
    payload = validate(args.csv)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["ok"] else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
