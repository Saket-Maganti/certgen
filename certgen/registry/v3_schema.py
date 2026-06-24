"""V3 registry schema and availability validation."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from certgen.core.io import write_json


ELIGIBILITY_LEVELS = {
    "not_checked",
    "availability_planned",
    "samples_available",
    "features_available_unvalidated",
    "features_validated",
    "metric_reproduced",
    "pilot_ready",
    "pilot_blocked",
}


def read_csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def validate_v3_registry(benchmarks: str | Path, model_pairs: str | Path, feature_caches: str | Path) -> dict[str, Any]:
    bench_rows = read_csv_rows(benchmarks)
    pair_rows = read_csv_rows(model_pairs)
    cache_rows = read_csv_rows(feature_caches)
    errors: list[str] = []
    warnings: list[str] = []
    benchmarks_seen = {row.get("benchmark_id") for row in bench_rows}
    cache_ids = {row.get("cache_id") for row in cache_rows}
    for row in pair_rows:
        cid = row.get("comparison_id")
        level = row.get("pilot_eligibility")
        if level not in ELIGIBILITY_LEVELS:
            errors.append(f"{cid}: invalid pilot_eligibility")
        if row.get("benchmark_id") not in benchmarks_seen:
            errors.append(f"{cid}: benchmark_id missing from benchmarks table")
        if row.get("license_status") in {"restricted", "not_allowed"}:
            errors.append(f"{cid}: restricted license blocks pilot")
        if row.get("preprocessing_match") != "true" and level == "pilot_ready":
            errors.append(f"{cid}: preprocessing mismatch blocks pilot_ready")
        required_caches = [row.get("reference_cache_id"), row.get("model_a_cache_id"), row.get("model_b_cache_id")]
        if level == "pilot_ready":
            for cache_id in required_caches:
                if cache_id not in cache_ids:
                    errors.append(f"{cid}: required cache {cache_id} missing")
            if row.get("sample_source_verified") != "true":
                errors.append(f"{cid}: sample source not verified")
            if row.get("reported_claim_source") in {"", "TBD", "unknown"}:
                errors.append(f"{cid}: reported claim source missing")
        if level != "pilot_ready":
            warnings.append(f"{cid}: not pilot-ready ({level})")
    return {
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "benchmarks": len(bench_rows),
        "model_pairs": len(pair_rows),
        "feature_caches": len(cache_rows),
        "evidence_status": "planned_only",
        "claim_allowed": False,
    }


def render_availability_table(registry_dir: str | Path, out: str | Path, json_out: str | Path) -> dict[str, Any]:
    registry_dir = Path(registry_dir)
    rows = read_csv_rows(registry_dir / "model_pairs_template.csv")
    entries = []
    for row in rows:
        missing = []
        if row.get("sample_source_verified") != "true":
            missing.append("verified samples/features")
        if row.get("preprocessing_match") != "true":
            missing.append("matching preprocessing")
        if row.get("pilot_eligibility") != "pilot_ready":
            missing.append("pilot-ready eligibility")
        entries.append(
            {
                "comparison_id": row.get("comparison_id"),
                "pilot_ready": row.get("pilot_eligibility") == "pilot_ready" and not missing,
                "missing": missing,
                "next_action": "fill/validate missing metadata" if missing else "ready for non-claim pilot",
            }
        )
    payload = {"entries": entries, "evidence_status": "planned_only", "claim_allowed": False}
    lines = ["# V3 Availability Table", "", "`NO_REAL_EVIDENCE`", "", "| Comparison | Pilot Ready | Missing | Next Action |", "|---|---:|---|---|"]
    for entry in entries:
        lines.append(f"| `{entry['comparison_id']}` | `{entry['pilot_ready']}` | `{', '.join(entry['missing']) or 'none'}` | {entry['next_action']} |")
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_json(payload, json_out)
    return payload
